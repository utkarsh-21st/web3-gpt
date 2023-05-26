import os
import sys
import subprocess
import re
from config import SAVE_PATH, TEMP_CONTRACTS_PATH
import pandas as pd


class Contracts:
    def __init__(self, conracts_dir_url, clear_cache=False):
        try:
            match = re.search("https://github.com/([^/]+)/?", conracts_dir_url)
            self.repo_name = match.group(1)
            parts = conracts_dir_url.split("/")
            self.contracts_name = parts[-1] if parts[-1] else parts[-2]
        except Exception as e:
            print(e)
            print("Can't parse the given URL: ", conracts_dir_url)
            print("Exiting...")
            sys.exit()

        print("repo_name", self.repo_name)
        print("contracts_name", self.contracts_name)

        self.contracts_path = TEMP_CONTRACTS_PATH / self.repo_name / self.contracts_name

        for path in self.contracts_path.rglob("*"):
            print(path)
        # self.urls = []
        # self.urls_reponse = {}
        # self.texts = []
        # self.text_headings = []
        # self.embedding_texts = []
        # self.embeddings = []
        # self.embeddings_path = SAVE_PATH / (self.doc_name + ".csv")
        # self.embeddings_df = pd.DataFrame()

        # if not clear_cache and self.embeddings_path.exists():
        #     print("Using saved embeddings")
        #     self.embeddings_df = pd.read_csv(
        #         str(self.embeddings_path), converters={"embedding": ast.literal_eval}
        #     )
        # else:
        #     if self.embeddings_path.exists():
        #         print(f"Clearing cache for {self.book_url}")
        #         os.remove(self.embeddings_path)
        #     print("Calculating embeddings")
        #     self.scrape_urls_recursively(url)
        #     self.get_text_from_url()
        #     self.perform_text_splitting()
        #     self.calculate_and_save_embeddings()

        # Download contracts
        # subprocess.run(
        #     [
        #         "gh-folder-download",
        #         "--url",
        #         conracts_dir_url,
        #         "--output",
        #         str(self.contracts_path),
        #     ]
        # )
