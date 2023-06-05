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
    URLS,
    GITHUB_PA_TOKEN,
    CODE_MODEL_MAX_TOKENS,
)
from gpt_utils import (
    num_tokens,
    halved_by_delimiter,
    truncate_string,
    get_chat_completion_response,
    get_contracts,
)
import pandas as pd
import openai
from scipy import spatial
import ast
import shutil

openai.api_key = OPENAI_API_KEY


class DeFiQA:
    def __init__(
        self,
        doc_url,
        conracts_dir_url=None,
        clear_cache=False,
        clear_contracts_cache=False,
    ):
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

        self.repo_name = None
        self.contracts_name = None
        self.contracts_path = None
        self.contract_names = []

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

        if self.conracts_dir_url:
            try:
                match = re.search("https://github.com/([^/]+)/?", self.conracts_dir_url)
                self.repo_name = match.group(1)
                parts = self.conracts_dir_url.split("/")
                self.contracts_name = parts[-1]
            except Exception as e:
                print(e)
                print(
                    "Can't parse the given contracts URL: ",
                    self.conracts_dir_url,
                )
                print("Exiting...")
                sys.exit()
            self.contracts_path = SAVE_PATH / self.repo_name / self.contracts_name
            if clear_contracts_cache:
                print(f"Clearing cache for {self.repo_name}::{self.contracts_name}")
                if self.contracts_path.exists():
                    shutil.rmtree(self.contracts_path)

            if not self.contracts_path.exists():
                self.download_contracts()

        # pre-compute embeddings from contracts
        if not self.embeddings_path_doc.exists():
            self.scrape_urls_recursively()
            self.read_text_from_url()

            if self.conracts_dir_url:
                # TODO:
                # i = 0
                for path in self.contracts_path.rglob("*"):
                    # TODO:
                    # if i == 2:
                    #     break
                    if path.is_file() and path.suffix == ".sol":
                        # TODO:
                        # i += 1
                        dir_name = (
                            path.parts[-2]
                            if path.parts[-2].lower() != "contracts"
                            else ""
                        )
                        with open(path, "r") as file:
                            print("going through", path)
                            contract = file.read()
                            introduction = "Below is the code of a Smart Contract. Give a detailed explaination of it."
                            question = ""
                            split_messages = []

                            split_contracts = self.split_contract(
                                introduction, contract, question, CODE_MODEL
                            )
                            for split_contract in split_contracts:
                                split_message = introduction + split_contract + question
                                split_messages.append(split_message)
                            for split_message in split_messages:
                                chat_responses = []
                                chat_response = get_chat_completion_response(
                                    openai,
                                    CODE_MODEL,
                                    "You answer questions about provided Smart Contracts belonging to a DeFi protocol.",
                                    split_message,
                                )
                                chat_responses.append(chat_response)

                            contract_summary = "\n\n".join(chat_responses)

                            self.texts.append(contract_summary)
                            self.text_headings.append(
                                f"Contract: {dir_name}, {path.parts[-1]}"
                            )
                        self.contract_names.append(path.stem)

                contract_names_description = (
                    f"The {self.repo_name} consists of the following contracts:\n"
                )
                for i, contract_name in enumerate(self.contract_names):
                    contract_names_description += f"{i+1}. {contract_name}\n"

                self.texts.append(contract_names_description)
                self.text_headings.append("Contracts Summary:")

            self.calculate_and_save_doc_embeddings()
        else:
            print("Using saved embeddings")

        self.embeddings_df_doc = pd.read_csv(
            str(self.embeddings_path_doc),
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

    def split_contract(self, introduction, contract, question, model, max_recursion=50):
        contracts = []
        if (
            num_tokens(introduction + contract + question, model)
            < CODE_MODEL_MAX_TOKENS
        ):
            return [contract]
        elif max_recursion == 0:
            print("Max recursions reached")
            print("Truncate")
            return [
                truncate_string(
                    contract,
                    model=model,
                    max_tokens=CODE_MODEL_MAX_TOKENS
                    - num_tokens(introduction + question),
                )
            ]
        else:
            for delimiter in ["\n\n", "\n", ". "]:
                left, right = halved_by_delimiter(contract, delimiter, model)
                if left == "" or right == "":
                    # if either half is empty, retry with a more fine-grained delimiter
                    continue
                else:
                    contract1 = self.split_contract(
                        introduction, left, question, model, max_recursion - 1
                    )
                    contract2 = self.split_contract(
                        introduction, right, question, model, max_recursion - 1
                    )
                    contracts.extend(contract1)
                    contracts.extend(contract2)
                    return contracts
            # print("string:", string)
            print("num_tokens:", num_tokens(introduction + contract + question, model))
            print("Max:", CODE_MODEL_MAX_TOKENS)
            # print("left:", left)
            # print("right:", right)
            # string = re.sub(r"0x[a-fA-F0-9]{40}", "contract address", string)
            # print("string:", string)
            # print("num_tokens after deleting addresses:", num_tokens(string))
            # if num_tokens(string) >= MAX_TOKENS_PER_EMBEDDING:
            print("Truncate")
            return [
                truncate_string(
                    contract, model=CODE_MODEL, max_tokens=CODE_MODEL_MAX_TOKENS
                )
            ]

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

    def get_messages_contract(self, contract_names: str, query: str) -> list[list[str]]:
        contracts = get_contracts(contract_names, self.contracts_path)
        messages = []

        for i, contract in enumerate(contracts):
            question = f"\n\nQuestion: {query} Answer the question only for the contract named {contract_names[i]}"
            split_messages = []
            introduction = f"Use the below smart contract code for {contract_names[i]} of a DeFi protocol named {self.repo_name} to answer the question.\n\n"
            # introduction = f"Use the below smart contract code for {contract_names[i]} of a DeFi protocol named {self.repo_name} to answer the question. Just answer as much as you can without mentioning any inadequacy in the code provided.\n\n"
            split_contracts = self.split_contract(
                introduction, contract, question, CODE_MODEL
            )
            for split_contract in split_contracts:
                split_message = introduction + split_contract + question
                split_messages.append(split_message)
            messages.append(split_messages)
        return messages

    def ask_doc(self, query, model, print_message: bool = False, stream=False) -> str:
        if self.doc_url:
            """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
            message = self.get_message_doc(query, model)
            if print_message:
                print(message)
            chat_response = get_chat_completion_response(
                openai,
                DOC_MODEL,
                "You answer questions about a DeFi protocol",
                message,
                stream,
            )
            return chat_response
        else:
            print("No docs were provided")

    def ask_contract(
        self,
        contract_names,
        query,
        print_message: bool = False,
    ) -> str:
        if self.conracts_dir_url:
            """Answers a query using GPT and a dataframe of relevant texts and embeddings"""
            messages = self.get_messages_contract(contract_names, query)
            if print_message:
                [print(split_messages) for split_messages in messages]
                [print(len(split_messages)) for split_messages in messages]

            # TODO:
            print("len messages", len(messages))
            # print("messages-----", messages)
            chat_responses = []
            for message in messages:
                split_responses = []
                for split_message in message:
                    split_responses.append(
                        get_chat_completion_response(
                            openai,
                            CODE_MODEL,
                            "You answer questions about provided Smart Contracts belonging to a DeFi protocol. You never mention the source of your answer",
                            split_message,
                        )
                    )
                chat_responses.append("\n".join(split_responses))
            return "\n\n".join(chat_responses)
        else:
            print("No contracts were provided")
