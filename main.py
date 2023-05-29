from DeFiQA import DeFiQA
from gpt_utils import num_tokens
from config import CHAT_MODEL

"""
TODO: clean scrapped text? remove '/$', for example

TODO: Prevent repetitions while fetching
These all targets the same page
https://docs.lyra.finance/overview/risks#synthetix-risk
https://docs.lyra.finance/overview/risks#smart-contract-risk
https://docs.lyra.finance/overview/risks#settlement-risk
https://docs.lyra.finance/overview/risks#amm-liquidity-provision-risk
https://docs.lyra.finance/overview/risks#withdrawal-delay-risk

TODO: Fix "undefined"
https://docs.lyra.finance/overview/risks#undefined

TODO: exception handling

TODO: combine top ranked texts from both doc and contracts for querying?

TODO: when to truncate; remove addresses before truncate?

TODO: keep multiple, overlapping sub-text instead of discarding the truncated part

TODO: In case of contracts, use as much code as possible, possibly using multiple queries covering all relevant codes

TODO: format contract(.sol) after downloading

TODO: use github token to prevent rate limit error
"""


def main():
    doc_url = input("Enter a gitbook URL: ")
    contract_url = input("Enter an URL of a github contracts directory: ")
    # url = "https://docs.lyra.finance/overview/how-does-lyra-work"
    # qa = DeFiQA(doc_url, "https://github.com/lyra-finance/lyra-protocol/tree/master/contracts")
    qa = DeFiQA(doc_url, contract_url)  # clear_cache=True
    while True:
        query = input("Question:")
        answer = qa.ask_doc(query, print_message=False)
        print("Answer from docs:", answer, end="\n")
        answer = qa.ask_contract(query, print_message=True)
        print("Answer from code:", answer, end="\n")

    # conracts_dir_url = (
    #     "https://github.com/lyra-finance/lyra-protocol/tree/master/contracts"
    # )
    # contracts = Contracts(conracts_dir_url)

    # print('Ranked: ', qa.texts_ranked_by_relatedness("What is lyra", top_n=5))


if __name__ == "__main__":
    main()
