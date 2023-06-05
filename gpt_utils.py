import tiktoken
import re
import time


def num_tokens(text: str, model: str) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def halved_by_delimiter(string: str, delimiter: str, model: str) -> list[str, str]:
    """Split a string in two, on a delimiter, trying to balance tokens on each side."""
    chunks = string.split(delimiter)
    if len(chunks) == 1:
        return [string, ""]  # no delimiter found
    elif len(chunks) == 2:
        return chunks  # no need to search for halfway point
    else:
        total_tokens = num_tokens(string, model)
        halfway = total_tokens // 2
        best_diff = halfway
        for i, chunk in enumerate(chunks):
            left = delimiter.join(chunks[: i + 1])
            left_tokens = num_tokens(left, model)
            diff = abs(halfway - left_tokens)
            if diff >= best_diff:
                break
            else:
                best_diff = diff
        left = delimiter.join(chunks[:i])
        right = delimiter.join(chunks[i:])
        return [left, right]


def truncate_string(
    string: str,
    model: str,
    max_tokens: int,
    print_warning: bool = True,
) -> str:
    """Truncate a string to a maximum number of tokens."""
    encoding = tiktoken.encoding_for_model(model)
    encoded_string = encoding.encode(string)
    truncated_string = encoding.decode(encoded_string[:max_tokens])
    if print_warning and len(encoded_string) > max_tokens:
        print(
            f"Warning: Truncated string from {len(encoded_string)} tokens to {max_tokens} tokens."
        )
    return truncated_string


def get_chat_completion_response(openai, model, content, message, stream=False):
    gpt_messages = [
        {
            "role": "system",
            "content": content,
        },
        {"role": "user", "content": message},
    ]
    try:
        response = openai.ChatCompletion.create(
            model=model, messages=gpt_messages, temperature=0, stream=stream
        )
    except Exception as e:
        print(
            f">> error while chat completion:: {e}\n\nTrying again in a few seconds.."
        )
        time.sleep(20)
        return get_chat_completion_response(openai, model, content, message)
    return response if stream else response["choices"][0]["message"]["content"]


def extract_contract_names_as_list(answer_doc, openai, model):
    contract_names = []
    try:
        introduction = "The given text might contain the name of smart contracts. Your task is to identify all of them and just output a python list of them with each element as string. Don't output partial names"
        message = f"{introduction}\n\nText:{answer_doc}\n\n"
        content = "You are a helpful bot. You do as instructed"
        chat_response = get_chat_completion_response(openai, model, content, message)
        match = re.search("(\[.*\])", chat_response)
        contract_names = eval(match.group(1))
        contract_names = list(
            map(
                lambda s: s.split(".")[-2] if ".sol" in s.lower() else s, contract_names
            )
        )
    except Exception as e:
        print(">> Couldn't extract contract names", e)
    return contract_names


def get_contracts(contract_names, contracts_path):
    contract_names = list(map(lambda s: s.lower(), contract_names))
    contracts = []
    for path in contracts_path.rglob("*"):
        if path.is_file() and path.stem.lower() in contract_names:
            with open(path, "r") as file:
                contracts.append(file.read())
    # TODO:
    print("contracts", contracts)
    print("length contracts", len(contracts))
    return contracts


def get_multiple_queries(query, openai, model):
    try:
        content = "You follow a consistent style"
        introduction = "You are given a question below. The question may talk about multiple topics. Split the question into multiple questions on that topic. Each resulting question must be about a different topic. Also, the output must be a python list of questions."
        query1 = "{Do vaults have withdraw and deposit functionality. If so, tell about the associated fees in both cases. Answer in detail.}"
        answer1 = "['Do vaults have withdraw functionality. If so, tell about the associated fee. Answer in detail.', 'Do vaults have deposit functionality. If so, tell about the associated fee. Answer in detail.']"
        message1 = f"{introduction}\n\nQuestion:{query1}\n\n"
        query2 = "{Using the documentation provided, explain in detail in points on the following in max 1000 char. Fees, Fees Distribution, Rewards Distribution, Risks associated. Use more prominent features of the protocol to make points as necessary.}"
        answer2 = "['Using the documentation provided, explain in detail in points on Fees associated in max 1000 char. Use more prominent features of the protocol to make points as necessary.', 'Using the documentation provided, explain in detail in points on Fees Distribution associated in max 1000 char. Use more prominent features of the protocol to make points as necessary.', 'Using the documentation provided, explain in detail in points on Rewards Distributionassociated in max 1000 char. Use more prominent features of the protocol to make points as necessary.', 'Using the documentation provided, explain in detail in points on Risks associated in max 1000 char. Use more prominent features of the protocol to make points as necessary.']"
        message2 = f"{introduction}\n\nQuestion:{query2}\n\n"
        query3 = "{Explain rewards and fee distribution in context of vaults. Answer in points.}"
        answer3 = "['Explain reward distribution in context of vaults. Answer in points.', 'Explain fee distribution in context of vaults. Answer in points.']"
        message3 = f"{introduction}\n\nQuestion:{query3}\n\n"
        query4 = "{Show all contract addresses}"
        answer4 = "['Show all contract addresses']"
        message4 = f"{introduction}\n\nQuestion:{query4}\n\n"
        query5 = "{explain options and its corresponding contract in brief}"
        answer5 = "['Explain options in brief', 'Explain the corresponding contract for options in brief']"
        message5 = f"{introduction}\n\nQuestion:{query5}\n\n"
        query6 = "{Provide a brief description of all the contracts along with their addresses}"
        answer6 = "['Provide a brief description of all the contracts', 'Provide the addresses of all the contracts']"
        message6 = f"{introduction}\n\nQuestion:{query6}\n\n"
        query7 = "{What are positions in Lyra and how to open and close them? Explain in detail. Also compare them with the industry standard}"
        answer7 = "['What are positions in Lyra? Explain in detail. Also compare them with the industry standard.', 'How to open positions in Lyra? Explain in detail. Also compare them with the industry standard.', 'How to close positions in Lyra? Explain in detail. Also compare them with the industry standard.']"
        message7 = f"{introduction}\n\nQuestion:{query7}\n\n"
        query8 = "{what is optionmarket contract in 100 words}"
        answer8 = "['What is the optionmarket contract in 100 words']"
        message8 = f"{introduction}\n\nQuestion:{query8}\n\n"
        query9 = "{Use the Url provided to find all the vaults, their adresses and their reward distribution. Answer should not exceed 50 words.}"
        answer9 = "['Use the Url provided to find all the vaults. Answer should not exceed 50 words.', 'Use the Url provided to find all the vault adresses. Answer should not exceed 50 words.', 'Use the Url provided to find reward distribution of all the vaults. Answer should not exceed 50 words.']"
        message9 = f"{introduction}\n\nQuestion:{query9}\n\n"
        # query9 = "{explain withdraw/mint/deposit in the context of this protocol}"
        # answer9 = "['explain withdraw in the context of this protocol', 'explain mint in the context of this protocol', 'explain deposit in the context of this protocol']"
        # message9 = f"{introduction}\n\nQuestion:{query9}\n\n"
        # query5 = "{Show all vaults which have a deposit fee}"
        # answer5 = "['What are the risks involved']"
        # message5 = f"{introduction}\n\nQuestion:{query5}\n\n"

        # content = "You are given a question below related to a DeFi protocol. Split the question into multiple questions if required while avoiding repetition of questions. Also, the output must be a python list of questions."
        # introduction = "You are given a question below related to a DeFi protocol. Split the question into multiple questions if required while avoiding repetition of questions. Also, the output must be a python list of questions."
        # introduction = "You are given a question below which may talk about multiple topics. Form multiple questions if the question talks about multiple topics, with each question talking about a single topic. Also, the output must be a python list of questions."
        # query = "{Using the documentation provided for Agility Finance, prepare a short introduction text covering the following points in max 250 char per point and upto 10 points. About, Minting/Withdraw features, Fees, Expected returns. Use more prominent features of Agility protocols to make points as necessary}"
        # query = "{explain stage one, stage two}"
        query = "{" + query + "}"
        message = f"{introduction}\n\nQuestion:{query}\n\n"

        gpt_messages = [
            {
                "role": "system",
                "content": content,
            },
            {"role": "user", "content": message1},
            {"role": "assistant", "content": answer1},
            {"role": "user", "content": message2},
            {"role": "assistant", "content": answer2},
            {"role": "user", "content": message3},
            {"role": "assistant", "content": answer3},
            {"role": "user", "content": message4},
            {"role": "assistant", "content": answer4},
            {"role": "user", "content": message5},
            {"role": "assistant", "content": answer5},
            {"role": "user", "content": message6},
            {"role": "assistant", "content": answer6},
            {"role": "user", "content": message7},
            {"role": "assistant", "content": answer7},
            {"role": "user", "content": message8},
            {"role": "assistant", "content": answer8},
            {"role": "user", "content": message9},
            {"role": "assistant", "content": answer9},
            {"role": "user", "content": message},
        ]
        response = openai.ChatCompletion.create(
            model=model, messages=gpt_messages, temperature=0
        )
        queries = eval(response["choices"][0]["message"]["content"])
    except Exception as e:
        print(">> Couldn't get multiple queries", e)
        queries = [query]
    return queries
