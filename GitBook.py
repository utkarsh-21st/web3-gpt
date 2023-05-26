import os
import sys
import re
from bs4 import BeautifulSoup
import requests
from config import (
    HEADERS,
    BLACKLIST,
    MAX_TOKENS_PER_EMBEDDING,
    CHAT_MODEL,
    BATCH_SIZE,
    EMBEDDING_MODEL,
    API_KEY,
    SAVE_PATH,
    MAX_TOKENS_PER_QUERY,
    TOP_N,
    URLS,
)
from gpt_utils import num_tokens, halved_by_delimiter, truncate_text
import pandas as pd
import openai
from scipy import spatial
import ast

openai.api_key = API_KEY


class GitBook:
    def __init__(self, url, clear_cache=False):
        try:
            match = re.search("(https?://[^/]+)/?", url)
        except Exception as e:
            print(e)
            print("Can't parse the given URL: ", url)
            print("Example URL: ", URLS[0])
            print("Exiting...")
            sys.exit()

        self.book_url = match.group(1)
        self.doc_name = self.book_url.split("//")[1]
        self.urls = []
        self.urls_reponse = {}
        self.texts = []
        self.text_headings = []
        self.embedding_texts = []
        self.embeddings = []
        self.embeddings_path = SAVE_PATH / (self.doc_name + ".csv")
        self.embeddings_df = pd.DataFrame()

        if not clear_cache and self.embeddings_path.exists():
            print("Using saved embeddings")
            self.embeddings_df = pd.read_csv(
                str(self.embeddings_path), converters={"embedding": ast.literal_eval}
            )
        else:
            if self.embeddings_path.exists():
                print(f"Clearing cache for {self.book_url}")
                os.remove(self.embeddings_path)
            print("Calculating embeddings")
            self.scrape_urls_recursively(url)
            self.get_text_from_url()
            self.perform_text_splitting()
            self.calculate_and_save_embeddings()

    def scrape_urls_recursively(self, url):
        r = self.get_url_reponse(url)
        s = BeautifulSoup(r.text, "html.parser")

        for i in s.find_all("a"):
            href = i.attrs["href"]
            if href.startswith("/"):
                url_ = self.book_url + href
                if url_ not in self.urls:
                    # TODO:
                    # if len(self.urls) == 10:
                    #     break
                    self.urls.append(url_)
                    print(url_)
                    self.scrape_urls_recursively(url_)

    def get_text_from_url(self):
        for url in self.urls:
            res = self.get_url_reponse(url)
            html_page = res.content
            soup = BeautifulSoup(html_page, "html.parser")
            text_all = soup.find_all(text=True)
            output = ""
            for t in text_all:
                if t.parent.name not in BLACKLIST:
                    output += "{} ".format(t.strip())

            heading = url[len(self.book_url) + 1 :] + ":\n"
            self.text_headings.append(heading)
            self.texts.append(output)

    def get_url_reponse(self, url):
        return (
            self.urls_reponse.get(url)
            if self.urls_reponse.get(url)
            else requests.get(url, headers=HEADERS)
        )

    def perform_text_splitting(self):
        for text, heading in zip(self.texts, self.text_headings):
            split_texts = self.split_text(text)
            embedding_texts = list(
                map(lambda split_text: f"{heading}:\n{split_text}", split_texts)
            )
            self.embedding_texts.extend(embedding_texts)

    def split_text(self, text, max_recursion=5):
        texts = []
        if num_tokens(text) < MAX_TOKENS_PER_EMBEDDING:
            texts.extend([text])
            return texts
        elif max_recursion == 0:
            print("Max recursions reached")
            print("Truncate")
            return [
                truncate_text(
                    text, model=CHAT_MODEL, max_tokens=MAX_TOKENS_PER_EMBEDDING
                )
            ]
        else:
            for delimiter in ["\n\n", "\n", ". "]:
                left, right = halved_by_delimiter(text, delimiter=delimiter)
                if left == "" or right == "":
                    # if either half is empty, retry with a more fine-grained delimiter
                    continue
                else:
                    texts1 = self.split_text(left, max_recursion - 1)
                    texts2 = self.split_text(right, max_recursion - 1)
                    texts.extend(texts1)
                    texts.extend(texts2)
                    return texts
            # print("text:", text)
            print("num_tokens:", num_tokens(text))
            print("Max:", MAX_TOKENS_PER_EMBEDDING)
            # print("left:", left)
            # print("right:", right)
            # text = re.sub(r"0x[a-fA-F0-9]{40}", "contract address", text)
            # print("text:", text)
            # print("num_tokens after deleting addresses:", num_tokens(text))
            # if num_tokens(text) >= MAX_TOKENS_PER_EMBEDDING:
            print("Truncate")
            return [
                truncate_text(
                    text, model=CHAT_MODEL, max_tokens=MAX_TOKENS_PER_EMBEDDING
                )
            ]
            # else:
            #     return text

    def calculate_and_save_embeddings(self):
        for batch_start in range(0, len(self.embedding_texts), BATCH_SIZE):
            batch_end = batch_start + BATCH_SIZE
            batch = self.embedding_texts[batch_start:batch_end]
            print(f"Batch {batch_start} to {batch_end-1}")
            response = openai.Embedding.create(model=EMBEDDING_MODEL, input=batch)
            for i, be in enumerate(response["data"]):
                assert (
                    i == be["index"]
                )  # double check embeddings are in same order as input
            batch_embeddings = [e["embedding"] for e in response["data"]]
            self.embeddings.extend(batch_embeddings)

        self.embeddings_df = pd.DataFrame(
            {"text": self.embedding_texts, "embedding": self.embeddings}
        )
        self.embeddings_df.to_csv(self.embeddings_path, index=False)

    def texts_ranked_by_relatedness(
        self,
        query: str,
        relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
        top_n: int = 100,
    ) -> tuple[list[str], list[float]]:
        """Returns a list of texts and relatednesses, sorted from most related to least."""
        query_embedding_response = openai.Embedding.create(
            model=EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]
        strings_and_relatednesses = [
            (row["text"], relatedness_fn(query_embedding, row["embedding"]))
            for i, row in self.embeddings_df.iterrows()
        ]
        strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
        strings, relatednesses = zip(*strings_and_relatednesses)
        return strings[:top_n], relatednesses[:top_n]

    def query_message(self, query: str) -> str:
        """Return a message for GPT, with relevant source texts pulled from a dataframe."""
        texts, relatednesses = self.texts_ranked_by_relatedness(query, top_n=TOP_N)
        introduction = 'Use the below documentation of a DeFi protocol to answer the subsequent question. If the answer cannot be found in the articles, write "I could not find an answer."'
        question = f"\n\nQuestion: {query}"
        message = introduction
        for text in texts:
            next_article = f"\n\n{text}\n\n"
            if num_tokens(message + next_article + question) > MAX_TOKENS_PER_QUERY:
                break
            else:
                message += next_article
        return message + question

    def ask(
        self,
        query,
        print_message: bool = False,
    ) -> str:
        """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
        message = self.query_message(query)
        if print_message:
            print(message)
        messages = [
            {
                "role": "system",
                "content": f"You answer questions about a DeFi protocol named: {self.doc_name}",
            },
            {"role": "user", "content": message},
        ]
        response = openai.ChatCompletion.create(
            model=CHAT_MODEL, messages=messages, temperature=0
        )
        response_message = response["choices"][0]["message"]["content"]
        return response_message
