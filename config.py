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
DOC_MODEL = "gpt-3.5-turbo"  # change `MAX_TOKENS_PER_QUERY` accordingly
CODE_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI's best embeddings as of Apr 2023

# keys
OPENAI_API_KEY = "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"
GITHUB_PA_TOKEN = "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"

# Size
CODE_MODEL_MAX_TOKENS = 4096
DOC_MODEL_MAX_TOKENS = 4096
BATCH_SIZE = 1000  # you can submit up to 2048 embedding inputs per request
MAX_TOKENS_PER_EMBEDDING = 1000
MAX_TOKENS_PER_QUERY = 4096 - 500
TOP_N = 5  # number of top ranked texts to consider for query message
TOP_N_CONTRACT = 12  # number of top ranked texts to consider for query message

# Paths
SAVE_PATH = Path("saved")
if not SAVE_PATH.exists():
    os.mkdir(SAVE_PATH)

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