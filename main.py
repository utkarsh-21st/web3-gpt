from DeFiQA import DeFiQA
from config import MODEL, URLS, OPENAI_API_KEY
from gpt_utils import extract_contract_names_as_list, get_multiple_queries
import openai
from pathlib import Path
import argparse

openai.api_key = OPENAI_API_KEY

"""
TODO: alternatives to truncate?

TODO: keep multiple, overlapping sub-text instead of discarding the truncated part?

TODO: exception handling

TODO: improve contract names extraction

TODO: improve QA parsing accuracy

TODO: concatenate each q with {the protocol name}?

TODO: format contract(.sol) after downloading

TODO: context is system vs message

TODO: tune num token for output?
"""


def parse_args():
    global args
    parser = argparse.ArgumentParser(description="QA Bot")

    parser.add_argument(
        "--clear_cache", action="store_true", help="Recomputes the embeddings"
    )
    parser.add_argument(
        "--clear_contracts_cache",
        action="store_true",
        help="Re-downloads all the contracts from github",
    )

    args = parser.parse_args()


def main():
    parse_args()
    doc_url = input("Enter a gitbook URL: ")
    contract_url = input("Enter an URL of a github contracts directory: ")
    # qa = DeFiQA(*URLS[0], args.clear_cache, args.clear_contracts_cache)
    qa = DeFiQA(
        URLS[0][0],
        clear_cache=args.clear_cache,
        clear_contracts_cache=args.clear_contracts_cache,
    )
    while True:
        query = input("Question:")
        queries = get_multiple_queries(query, openai, MODEL)

        [print("Question:", query) for query in queries]

        # queries = ["Provide a list of all contracts along ith a brief description"]
        answer_doc = ""
        for query_split in queries:
            answer_doc += qa.ask_doc(query_split, MODEL) + "\n\n"
        print("Answer from docs:", answer_doc, end="\n")
        answer = answer_doc
        if qa.contracts_path:
            contract_names = extract_contract_names_as_list(answer_doc, openai, MODEL)
            print("contract_names", contract_names)
            load_more = True if input("Load more...(y/n)").lower() == "y" else False
            if load_more:
                answer_contract = qa.ask_contract(
                    contract_names, query, print_message=True
                )
                print("Answer from code:", answer_contract, end="\n")
                answer += "\n" * 2 + answer_contract
        print("Answer:", answer)
        # break


if __name__ == "__main__":
    main()
