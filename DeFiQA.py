import os
import sys
import re
from bs4 import BeautifulSoup
import subprocess
import requests
from config import (
    HEADERS,
    BLACKLIST,
    MAX_TOKENS_PER_EMBEDDING,
    DOC_MODEL,
    CODE_MODEL,
    BATCH_SIZE,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    SAVE_PATH,
    MAX_TOKENS_PER_QUERY,
    TOP_N,
    TOP_N_CONTRACT,
    URLS,
    TEMP_PATH,
    GITHUB_PA_TOKEN,
)
from gpt_utils import num_tokens, halved_by_delimiter, truncate_string
import pandas as pd
import openai
from scipy import spatial
import ast
import shutil

openai.api_key = OPENAI_API_KEY


class DeFiQA:
    def __init__(self, doc_url=None, conracts_dir_url=None, clear_cache=False):
        self.doc_url = doc_url
        self.conracts_dir_url = conracts_dir_url

        self.doc_name = None
        self.urls = []
        self.urls_response = {}
        self.texts = []
        self.text_headings = []
        self.embeddings_doc = []
        self.embeddings_path_doc = None
        self.embeddings_df_doc = pd.DataFrame()

        self.code_names = []
        self.codes = []
        self.embeddings_contract = []
        self.embeddings_path_contract = None
        self.embeddings_df_contract = pd.DataFrame()
        self.repo_name = None
        self.contracts_name = None

        # docs
        if self.doc_url:
            try:
                match = re.search("(https?://[^/]+)/?", self.doc_url)
                self.doc_url = match.group(1)
            except Exception as e:
                print(e)
                print("Can't parse the given URL: ", self.doc_url)
                print("Example URL: ", URLS[0])
                print("Exiting...")
                sys.exit()

            self.doc_name = self.doc_url.split("//")[1] if self.doc_url else None
            self.embeddings_path_doc = SAVE_PATH / (self.doc_name + ".csv")

            if clear_cache:
                print(f"Clearing cache for {self.doc_url}")
                if self.embeddings_path_doc.exists():
                    os.remove(self.embeddings_path_doc)

            if not self.embeddings_path_doc.exists():
                self.scrape_urls_recursively()
                self.read_text_from_url()
                self.calculate_and_save_doc_embeddings()
            else:
                print("Using saved doc embeddings")

            self.embeddings_df_doc = pd.read_csv(
                str(self.embeddings_path_doc),
                converters={"embedding": ast.literal_eval},
            )

        # contracts
        if self.conracts_dir_url:
            try:
                match = re.search("https://github.com/([^/]+)/?", self.conracts_dir_url)
                self.repo_name = match.group(1)
                parts = self.conracts_dir_url.split("/")
                self.contracts_name = parts[-1] if parts[-1] else parts[-2]
            except Exception as e:
                print(e)
                print("Can't parse the given contracts URL: ", self.conracts_dir_url)
                print("Exiting...")
                sys.exit()

            self.embeddings_path_contract = SAVE_PATH / (self.repo_name + ".csv")
            self.contracts_path = TEMP_PATH / self.repo_name / self.contracts_name
            self.embeddings_contract = []
            self.embeddings_path_contract = SAVE_PATH / (
                self.repo_name + "_" + self.contracts_name + ".csv"
            )
            self.embeddings_df_contract = pd.DataFrame()

            if clear_cache:
                print(f"Clearing cache for {self.repo_name}::{self.contracts_name}")
                if self.embeddings_path_contract.exists():
                    os.remove(self.embeddings_path_contract)
                if self.contracts_path.exists():
                    shutil.rmtree(self.contracts_path)

            if not self.embeddings_path_contract.exists():
                if not self.contracts_path.exists():
                    self.download_contracts()
                self.read_contracts()

                self.calculate_and_save_contract_embeddings()
            else:
                print("Using saved contract embeddings")

            self.embeddings_df_contract = pd.read_csv(
                str(self.embeddings_path_contract),
                converters={"embedding": ast.literal_eval},
            )

    def scrape_urls_recursively(self, url=None):
        url = url if url else self.doc_url
        r = self.get_url_reponse(url)
        s = BeautifulSoup(r.text, "html.parser")

        for i in s.find_all("a"):
            href = i.attrs["href"]
            if href.startswith("/"):
                url_ = self.doc_url + href
                split_hash = url_.split("#")
                if len(split_hash) > 1:
                    url_ = "#".join(split_hash[:-1])
                if url_ not in self.urls:
                    self.urls.append(url_)
                    print(url_)
                    self.scrape_urls_recursively(url_)

    def download_contracts(self):
        subprocess.run(
            [
                "gh-folder-download",
                "--url",
                self.conracts_dir_url,
                "--output",
                str(self.contracts_path),
                "--force",
                "--token",
                GITHUB_PA_TOKEN,
            ]
        )
        for path in self.contracts_path.rglob("*"):
            print(path)

    def read_text_from_url(self):
        for url in self.urls:
            res = self.get_url_reponse(url)
            html_page = res.content
            soup = BeautifulSoup(html_page, "html.parser")
            text_all = soup.find_all(text=True)
            output = ""
            for t in text_all:
                if t.parent.name not in BLACKLIST:
                    output += "{} ".format(t.strip())
            heading = url[len(self.doc_url) + 1 :] + ":\n"

            self.text_headings.append(heading)
            self.texts.append(output)

    def read_contracts(self, contracts_path=None):
        contracts_path = contracts_path if contracts_path else self.contracts_path
        for path in contracts_path.rglob("*"):
            if path.is_file():
                if str(path).split(".")[-1].lower() == "sol":
                    with open(path, "r") as contract:
                        self.code_names.append(
                            f"Contract Category: {path.parts[-2]}\nContract {path.stem}"
                        )
                        self.codes.append(contract.read())
            else:
                pass
                # self.read_contracts(path)

    def get_url_reponse(self, url):
        return (
            self.urls_response.get(url)
            if self.urls_response.get(url)
            else requests.get(url, headers=HEADERS)
        )

    def perform_string_splitting(self, strings, prefixes, model):
        result = []
        for string, prefix in zip(strings, prefixes):
            split_strings = self.split_string(string, model)
            split_strings = list(
                map(lambda split_string: f"{prefix}:\n{split_string}", split_strings)
            )
            result.extend(split_strings)
        return result

    def split_string(self, string, model, max_recursion=5):
        texts = []
        if num_tokens(string, model) < MAX_TOKENS_PER_EMBEDDING:
            return [string]
        elif max_recursion == 0:
            print("Max recursions reached")
            print("Truncate")
            return [
                truncate_string(
                    string, model=model, max_tokens=MAX_TOKENS_PER_EMBEDDING
                )
            ]
        else:
            for delimiter in ["\n\n", "\n", ". "]:
                left, right = halved_by_delimiter(string, delimiter, model)
                if left == "" or right == "":
                    # if either half is empty, retry with a more fine-grained delimiter
                    continue
                else:
                    texts1 = self.split_string(left, model, max_recursion - 1)
                    texts2 = self.split_string(right, model, max_recursion - 1)
                    texts.extend(texts1)
                    texts.extend(texts2)
                    return texts
            # print("string:", string)
            print("num_tokens:", num_tokens(string, model))
            print("Max:", MAX_TOKENS_PER_EMBEDDING)
            # print("left:", left)
            # print("right:", right)
            # string = re.sub(r"0x[a-fA-F0-9]{40}", "contract address", string)
            # print("string:", string)
            # print("num_tokens after deleting addresses:", num_tokens(string))
            # if num_tokens(string) >= MAX_TOKENS_PER_EMBEDDING:
            print("Truncate")
            return [
                truncate_string(
                    string, model=DOC_MODEL, max_tokens=MAX_TOKENS_PER_EMBEDDING
                )
            ]
            # else:
            #     return string

    def calculate_and_save_doc_embeddings(self):
        texts = self.perform_string_splitting(self.texts, self.text_headings, DOC_MODEL)

        for batch_start in range(0, len(texts), BATCH_SIZE):
            batch_end = batch_start + BATCH_SIZE
            batch = texts[batch_start:batch_end]
            print(f"Batch {batch_start} to {batch_end-1}")
            response = openai.Embedding.create(model=EMBEDDING_MODEL, input=batch)
            for i, be in enumerate(response["data"]):
                assert (
                    i == be["index"]
                )  # double check embeddings are in same order as input
            batch_embeddings = [e["embedding"] for e in response["data"]]
            self.embeddings_doc.extend(batch_embeddings)

        self.embeddings_df_doc = pd.DataFrame(
            {"text": texts, "embedding": self.embeddings_doc}
        )
        self.embeddings_df_doc.to_csv(self.embeddings_path_doc, index=False)

    def calculate_and_save_contract_embeddings(self):
        codes = self.perform_string_splitting(self.codes, self.code_names, CODE_MODEL)

        for batch_start in range(0, len(codes), BATCH_SIZE):
            batch_end = batch_start + BATCH_SIZE
            batch = codes[batch_start:batch_end]
            print(f"Batch {batch_start} to {batch_end-1}")
            response = openai.Embedding.create(model=EMBEDDING_MODEL, input=batch)
            for i, be in enumerate(response["data"]):
                assert (
                    i == be["index"]
                )  # double check embeddings are in same order as input
            batch_embeddings = [e["embedding"] for e in response["data"]]
            self.embeddings_contract.extend(batch_embeddings)

        self.embeddings_df_contract = pd.DataFrame(
            {"text": codes, "embedding": self.embeddings_contract}
        )
        self.embeddings_df_contract.to_csv(self.embeddings_path_contract, index=False)

    def docs_ranked_by_relatedness(
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
            for i, row in self.embeddings_df_doc.iterrows()
        ]
        strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
        strings, relatednesses = zip(*strings_and_relatednesses)
        return strings[:top_n], relatednesses[:top_n]

    def codes_ranked_by_relatedness(
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
            for i, row in self.embeddings_df_contract.iterrows()
        ]
        strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
        strings, relatednesses = zip(*strings_and_relatednesses)
        return strings[:top_n], relatednesses[:top_n]

    def get_message_doc(self, query: str, model: str) -> str:
        """Return a message for GPT, with relevant source texts pulled from a dataframe."""
        texts, relatednesses = self.docs_ranked_by_relatedness(query, top_n=TOP_N)
        introduction = f'Use the below documentation of a DeFi protocol named {self.doc_name} to answer the subsequent question. If the answer cannot be found in the articles, write "I could not find an answer."'
        question = f"\n\nQuestion: {query}"
        message = introduction
        for text in texts:
            next_article = f"\n\n{text}\n\n"
            if (
                num_tokens(message + next_article + question, model)
                > MAX_TOKENS_PER_QUERY
            ):
                break
            else:
                message += next_article
        return message + question

    def get_messages_contract(self, query: str, n_messages: int, model: str) -> str:
        """Return a list messages for GPT, with relevant source texts pulled from a dataframe."""
        texts, relatednesses = self.codes_ranked_by_relatedness(
            query, top_n=TOP_N_CONTRACT
        )
        introduction = f'Use the below Solidity Contracts of a DeFi protocol named {self.repo_name} to answer the subsequent question. If the answer cannot be found in the articles, write "I could not find an answer."'
        question = f"\n\nQuestion: {query}"
        messages = []
        message = introduction
        for i, text in enumerate(texts):
            next_article = f"\n\n{text}\n\n"
            if (
                num_tokens(message + next_article + question, model)
                > MAX_TOKENS_PER_QUERY
            ):
                messages.append(message + question)
                if len(messages) == n_messages:
                    break
                message = introduction + next_article
            else:
                message += next_article
                if i == len(texts) - 1:
                    messages.append(message)

        return messages

    def ask_doc(
        self,
        query,
        model,
        print_message: bool = False,
    ) -> str:
        if self.doc_url:
            """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
            message = self.get_message_doc(query, model)
            if print_message:
                print(message)
            messages = [
                {
                    "role": "system",
                    "content": "You answer questions about a DeFi protocol",
                },
                {"role": "user", "content": message},
            ]
            response = openai.ChatCompletion.create(
                model=DOC_MODEL, messages=messages, temperature=0
            )
            response_message = response["choices"][0]["message"]["content"]
            return response_message
        else:
            print("No docs were provided")

    def ask_contract(
        self,
        query,
        model,
        print_message: bool = False,
    ) -> str:
        if self.conracts_dir_url:
            """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
            messages = self.get_messages_contract(query, 1, model)
            if print_message:
                [print(message, "\n\n") for message in messages]

            response_messages = []
            # print("len messages", len(messages))
            # print("messages-----", messages)
            for message in messages:
                gpt_messages = [
                    {
                        "role": "system",
                        "content": "You answer questions about provided Smart Contracts belonging to a DeFi protocol",
                    },
                    {"role": "user", "content": message},
                ]
                response = openai.ChatCompletion.create(
                    model=CODE_MODEL, messages=gpt_messages, temperature=0
                )
                response_messages.append(response["choices"][0]["message"]["content"])
                # print("Part Answer:", response["choices"][0]["message"]["content"])
            return "\n\n".join(response_messages)
        else:
            print("No contracts were provided")
