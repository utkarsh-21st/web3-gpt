from GitBook import GitBook
from Contracts import Contracts
from gpt_utils import num_tokens
from config import CHAT_MODEL

# TODO: clean scrapped text? remove '/$', for example

"""
TODO: Prevent repetitions while fetching
Example 1: These all targets the same page
https://docs.lyra.finance/overview/risks#synthetix-risk
https://docs.lyra.finance/overview/risks#smart-contract-risk
https://docs.lyra.finance/overview/risks#settlement-risk
https://docs.lyra.finance/overview/risks#amm-liquidity-provision-risk
https://docs.lyra.finance/overview/risks#withdrawal-delay-risk

TODO: Fix "undefined"
https://docs.lyra.finance/overview/risks#undefined

TODO: exception handling

TODO: combine top ranked texts from both doc and contracts for querying?

TODO: delete contract addresses when token length exceeds

TODO: when to truncate; remove addresses before truncate?

TODO: keep multiple, overlapping sub-text instead of discarding the truncated part
"""


def main():
    url = input("Enter a gitbook URL: ")
    gitbook = GitBook(url) # clear_cache=True
    while True:
        query = input("Question:")
        answer = gitbook.ask(query, print_message=False)
        print("Answer", answer, end="\n")

    # conracts_dir_url = (
    #     "https://github.com/lyra-finance/lyra-protocol/tree/master/contracts"
    # )
    # contracts = Contracts(conracts_dir_url)

    # print('Ranked: ', gitbook.texts_ranked_by_relatedness("What is lyra", top_n=5))

if __name__ == "__main__":
    main()
