import openai
from config import DOC_MODEL, OPENAI_API_KEY
from gpt_utils import get_multiple_queries

openai.api_key = OPENAI_API_KEY

model = DOC_MODEL
queries = [
    "Using the documentation provided for Agility Finance, prepare a short introduction text covering the following points in max 250 char per point and upto 10 points. About, Minting/Withdraw features, Fees, Expected returns. Use more prominent features of Agility protocols to make points as necessary",
    "Explain options contract",
    "explain withdraw/mint/deposit in the context of this protocol",
    "What are positions in Lyra and how to open and close them? Explain in detail. Also compare them with the industry standard",
]
query = "what is optionmarket contract in 100 words"
[(print(query), print(get_multiple_queries(query, openai, model))) for query in queries]
