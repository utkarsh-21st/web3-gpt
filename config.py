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
CHAT_MODEL = "gpt-3.5-turbo"
CODE_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI's best embeddings as of Apr 2023


API_KEY = "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"

# Size
BATCH_SIZE = 1000  # you can submit up to 2048 embedding inputs per request
MAX_TOKENS_PER_EMBEDDING = 1000
MAX_TOKENS_PER_QUERY = 4096 - 500
TOP_N = 5  # number of top ranked texts to consider for query message

# Paths
SAVE_PATH = Path("saved")
TEMP_PATH = Path("temp")
if not SAVE_PATH.exists():
    os.mkdir(SAVE_PATH)
if not TEMP_PATH.exists():
    os.mkdir(TEMP_PATH)

URLS = [
    "https://docs.lyra.finance/overview/how-does-lyra-work",
    "https://gmxio.gitbook.io/gmx/",
]
