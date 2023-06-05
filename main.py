from DeFiQA import DeFiQA
from config import DOC_MODEL, CODE_MODEL, URLS, OPENAI_API_KEY
from gpt_utils import extract_contract_names_as_list, get_multiple_queries
import openai
from pathlib import Path
import argparse

openai.api_key = OPENAI_API_KEY

"""
TODO: Format final output like frontend

TODO: Fix spinner when more is clicked

TODO: make the final combined output consise

TODO: clean scrapped text? remove '/$', for example

TODO: when to truncate; remove addresses before truncate?

TODO: make doc url and contract url independent

TODO: exception handling

TODO: combine top ranked texts from both doc and contracts for querying?

TODO: keep multiple, overlapping sub-text instead of discarding the truncated part

TODO: In case of contracts, use as much code as possible, possibly using multiple queries covering all relevant codes (see n_messages)

TODO: format contract(.sol) after downloading

TODO: context is system vs message

TODO: lacking context in contracts Q/A?

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
    # contract_url = input("Enter an URL of a github contracts directory: ")
    qa = DeFiQA(doc_url, clear_cache=args.clear_cache)
    # qa = DeFiQA(*URLS[2], args.clear_cache, args.clear_contracts_cache)
    while True:
        query = input("Question:")
        try:
            queries = get_multiple_queries(query, openai, DOC_MODEL)
        except Exception as e:
            print(">> Couldn't get multiple queries", e)
            queries = [query]

        [print("Question:", query) for query in queries]

        # queries = ["Provide a list of all contracts along ith a brief description"]
        answer_doc = ""
        for query in queries:
            answer_doc += qa.ask_doc(query, DOC_MODEL) + "\n\n"
        print("Answer from docs:", answer_doc, end="\n")
        contract_names = extract_contract_names_as_list(answer_doc, openai, DOC_MODEL)
        print("contract_names", contract_names)
        # load_more = True if input("Load more...(y/n)").lower() == "y" else False
        # if load_more:
        #     answer_contract = qa.ask_contract(
        #         contract_names, query, print_message=True
        #     )
        #     print("Answer from code:", answer_contract, end="\n")
        # break
        # answer = answer_doc + '\n'*2 + answer_contract
        # print("Answer:", answer)


if __name__ == "__main__":
    main()


"""
- ask docs
- prepare a list of contracts using the answer from docs and the original question
- ask the question from contracts on each contract from the list
"""
