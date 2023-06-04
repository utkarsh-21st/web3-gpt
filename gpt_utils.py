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
    introduction = "The given text might contain the name of smart contracts. Your task is to identify and just output a python list of them."
    message = f"{introduction}\n\nText:{answer_doc}\n\n"
    content = "You are a helpful bot. You do as instructed"
    chat_response = get_chat_completion_response(openai, model, content, message)
    match = re.search("(\[.*\])", chat_response)
    contract_names = eval(match.group(1))
    contract_names = list(
        map(lambda s: s.split(".")[-2] if ".sol" in s.lower() else s, contract_names)
    )
    return contract_names


def get_contracts(contract_names, contracts_path):
    contract_names = list(map(lambda s: s.lower(), contract_names))
    contracts = []
    for path in contracts_path.rglob("*"):
        if path.stem.lower() in contract_names:
            with open(path, "r") as file:
                contracts.append(file.read())
    # TODO:
    print("contracts", contracts)
    print("length contracts", len(contracts))
    return contracts
