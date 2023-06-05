import openai
from config import CODE_MODEL, OPENAI_API_KEY, CODE_MODEL_MAX_TOKENS, DOC_MODEL
from gpt_utils import truncate_string, get_chat_completion_response, get_multiple_queries

openai.api_key = OPENAI_API_KEY

model = CODE_MODEL
max_tokens = CODE_MODEL_MAX_TOKENS

answer_doc = """AGI TimeLock: A contract that locks AGI tokens for a specified period of time.
- Agility.Treasury.eth: A contract that holds the treasury funds of the Agility protocol.
- Token AGI: The AGI token contract.
- esAGI: A contract that mints and manages the esAGI token, which is used for voting on the liquidity distribution platform.
- AGI/ETH UNI V2 LP: A contract that manages the AGI/ETH liquidity pool on Uniswap.
- Farm Contract Deployer: A contract that deploys new liquidity farming contracts.
- Factory: A contract that deploys new liquidity pools.
- ETH Staking Pool: A contract that manages the staking of ETH for rewards.
- AGI/WETH LP Pool: A contract that manages the staking of AGI/WETH LP tokens for rewards.
- stETH Staking Pool: A contract that manages the staking of stETH for rewards.
- rETH Staking Pool: A contract that manages the staking of rETH for rewards.
- fraxETH Staking Pool: A contract that manages the staking of fraxETH for rewards.
- ankrETH Staking Pool: A contract that manages the staking of ankrETH for rewards.
- StaFi rETH Pool: A contract that manages the staking of rETH for rewards on the StaFi platform.
- AGI Single Staking Pool: A contract that manages the staking of AGI tokens for rewards."""

# with open(TEMP_PATH / "0xAppl/contracts/contracts/LockFarm.sol", "r") as file:
#     string = file.read()
# string = truncate_string(string, model, max_tokens - 500)


# introduction = f"Below are the smart contract codes of a DeFi protocol. Use it to answer the subsequent questions."
# message = f"{introduction}\n\n{string}\n\nQuestion: Summary of the above string?"
# content = "You summarize smart contracts string of a DeFi Protocol"
# introduction = f"Below are the smart contract codes of a DeFi protocol. Use it to answer the subsequent questions."

# introduction = "The given text might contain the name of smart contracts. Your task is to identify and just output a python list of them."
# string = answer_doc
# message = f"{introduction}\n\nText:{string}\n\n"
# content = "You are a helpful bot. You do as instructed"

model = DOC_MODEL
introduction = "Refine the below text to make it coherent an consise. Remove any redundancies."
string = '''The 0xAppl consists of two contracts:
1. TimeLock: A smart contract that allows the owner to queue and execute transactions with a delay. It provides a way to execute transactions at a specific time in the future, which can be useful for various purposes, such as scheduling payments or executing smart contract upgrades.
2. MerkleDistributorWithDeadline: A smart contract that distributes tokens using a Merkle tree. It allows the owner to specify a deadline after which the distribution is no longer possible.
There is only one contract provided in the code, named TimeLock. It is a smart contract that allows the owner to queue and execute transactions with a delay and a grace period. The purpose of this contract is to provide a time-locked mechanism for executing transactions, which can be useful in various DeFi protocols.
There is only one contract in the provided code, which is:

1. MerkleDistributorWithDeadline: This contract is a modified version of the MerkleDistributor contract and is used to distribute tokens to users based on a Merkle tree. It adds a deadline functionality to the distribution process, which means that users can only claim their tokens until a certain time. Additionally, it also allows the owner of the contract to withdraw any remaining tokens after the deadline has passed.
'''
message = f"{introduction}\n\nText:{string}\n\n"
content = "You are a helpful bot. You do as instructed"

# introduction = "The given question might contain names of smart contracts. Your task is to remove the names from the question and output only the resulting question. Frame the result with proper english if needed"
# string = "What is the role of tokenizer and reward contracts"
# message = f"{introduction}\n\nQuestion:{string}\n\n"
# content = "You are a helpful bot. You do as said"

# introduction = "You are given a question below which may contain multiple parts. Your task is to form multiple questions using those parts so that each question has a single part."
# introduction = "You are given a question below which may talk about multiple features. Your task is to form multiple questions, with each question talking about a single feature. Also, the output must be a python list of questions."
# string = "Using the documentation provided for Agility Finance, prepare a short introduction text covering the following points. About, Minting/Withdraw features, Fees, Expected returns"
# message = f"{introduction}\n\nQuestion:{string}\n\n"
# content = "You are a helpful bot. You do as said"

print(get_multiple_queries(openai, model))


# print(get_chat_completion_response(openai, model, content, message))
