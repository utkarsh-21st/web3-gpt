from pathlib import Path
import os

# Request
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}
BLACKLIST = [
    "[document]",
    "noscript",
    "header",
    "html",
    "meta",
    "head",
    "input",
    "script",
    "style",
]

# Models used
MODEL = "gpt-3.5-turbo"  # change `MAX_TOKENS_PER_QUERY` accordingly
EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI's best embeddings as of Apr 2023

# keys
OPENAI_API_KEY = "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"
GITHUB_PA_TOKEN = "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"

# Size
MODEL_MAX_TOKENS = 4096
MIN_OUTPUT_TOKENS = 500  # reserve 500 for output
BATCH_SIZE = 1000  # you can submit up to 2048 embedding inputs per request
MAX_TOKENS_PER_EMBEDDING = 1000
MAX_TOKENS_PER_QUERY = MODEL_MAX_TOKENS - MIN_OUTPUT_TOKENS
TOP_N = 5  # number of top ranked texts to consider for query message
TOP_N_CONTRACT = 12  # number of top ranked texts to consider for query message

# Paths
SAVE_PATH = Path("saved")
EMBEDDINGS_DOC_DIR = SAVE_PATH / Path("embeddings_doc")
EMBEDDINGS_DOC_PLUS_CONTRACTS_DIR = SAVE_PATH / Path("embeddings_doc_plus_contracts")
if not SAVE_PATH.exists():
    os.mkdir(SAVE_PATH)
if not EMBEDDINGS_DOC_DIR.exists():
    os.mkdir(EMBEDDINGS_DOC_DIR)
if not EMBEDDINGS_DOC_PLUS_CONTRACTS_DIR.exists():
    os.mkdir(EMBEDDINGS_DOC_PLUS_CONTRACTS_DIR)


Q_PARSING_EXAMPLES = [
    {
        "query": "{Do vaults have withdraw and deposit functionality. If so, tell about the associated fees in both cases. Answer in detail.}",
        "answer": "['Do vaults have withdraw functionality. If so, tell about the associated fee. Answer in detail.', 'Do vaults have deposit functionality. If so, tell about the associated fee. Answer in detail.']",
    },
    {
        "query": "{Using the documentation provided, explain in detail in points on the following in max 1000 char. Fees, Fees Distribution, Rewards Distribution, Risks associated. Use more prominent features of the protocol to make points as necessary.}",
        "answer": "['Using the documentation provided, explain in detail in points on Fees associated in max 1000 char. Use more prominent features of the protocol to make points as necessary.', 'Using the documentation provided, explain in detail in points on Fees Distribution associated in max 1000 char. Use more prominent features of the protocol to make points as necessary.', 'Using the documentation provided, explain in detail in points on Rewards Distributionassociated in max 1000 char. Use more prominent features of the protocol to make points as necessary.', 'Using the documentation provided, explain in detail in points on Risks associated in max 1000 char. Use more prominent features of the protocol to make points as necessary.']",
    },
    {
        "query": "{Explain rewards and fee distribution in context of vaults. Answer in points.}",
        "answer": "['Explain reward distribution in context of vaults. Answer in points.', 'Explain fee distribution in context of vaults. Answer in points.']",
    },
    {
        "query": "{Show all contract addresses}",
        "answer": "['Show all contract addresses']",
    },
    {
        "query": "{explain options and its corresponding contract in brief}",
        "answer": "['Explain options in brief', 'Explain the corresponding contract for options in brief']",
    },
    {
        "query": "{Provide a brief description of all the contracts along with their addresses}",
        "answer": "['Provide a brief description of all the contracts', 'Provide the addresses of all the contracts']",
    },
    {
        "query": "{What are positions in Lyra and how to open and close them? Explain in detail. Also compare them with the industry standard}",
        "answer": "['What are positions in Lyra? Explain in detail. Also compare them with the industry standard.', 'How to open positions in Lyra? Explain in detail. Also compare them with the industry standard.', 'How to close positions in Lyra? Explain in detail. Also compare them with the industry standard.']",
    },
    {
        "query": "{what is optionmarket contract in 100 words}",
        "answer": "['What is the optionmarket contract in 100 words']",
    },
    {
        "query": "{Use the Url provided to find all the vaults, their adresses and their reward distribution. Answer should not exceed 50 words.}",
        "answer": "['Use the Url provided to find all the vaults. Answer should not exceed 50 words.', 'Use the Url provided to find all the vault adresses. Answer should not exceed 50 words.', 'Use the Url provided to find reward distribution of all the vaults. Answer should not exceed 50 words.']",
    },
]


# inputs
URLS = [
    (
        "https://docs.lyra.finance/overview/how-does-lyra-work",
        "https://github.com/lyra-finance/lyra-protocol/tree/master/contracts",
    ),
    (
        "https://gmxio.gitbook.io/gmx/",
        "https://github.com/gmx-io/gmx-contracts/tree/master/contracts",
    ),
    (
        "https://docs.agilitylsd.com/",
        "https://github.com/0xAppl/agility-contracts/tree/main/contracts",
    ),
]
