from DeFiQA import DeFiQA
from config import DOC_MODEL, CODE_MODEL

"""
TODO: clean scrapped text? remove '/$', for example

TODO: when to truncate; remove addresses before truncate?

TODO: exception handling

TODO: combine top ranked texts from both doc and contracts for querying?

TODO: keep multiple, overlapping sub-text instead of discarding the truncated part

TODO: In case of contracts, use as much code as possible, possibly using multiple queries covering all relevant codes (see n_messages)

TODO: format contract(.sol) after downloading

TODO: context is system vs message

TODO: lacking context in contracts Q/A?
"""


def main():
    doc_url = input("Enter a gitbook URL: ")
    contract_url = input("Enter an URL of a github contracts directory: ")
    qa = DeFiQA(doc_url, contract_url)  # clear_cache=True
    # qa = DeFiQA(
    #     "https://docs.lyra.finance/overview/how-does-lyra-work",
    #     None,
    #     # "https://github.com/lyra-finance/lyra-protocol/tree/master/contracts",
    # )
    # qa = DeFiQA(
    #     "https://gmxio.gitbook.io/gmx/",
    #     "https://github.com/gmx-io/gmx-contracts/tree/master/contracts",
    # )
    while True:
        query = input("Question:")
        # query = "explain updateIncreaseOrder function from the orderbook contract"
        # query = "explain orderbook contract"
        answer = qa.ask_doc(query, DOC_MODEL, print_message=False)
        print("Answer from docs:", answer, end="\n")
        answer = qa.ask_contract(query, CODE_MODEL, print_message=False)
        print("Answer from code:", answer, end="\n")


if __name__ == "__main__":
    main()
