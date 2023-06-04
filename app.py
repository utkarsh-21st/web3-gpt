import os
import streamlit as st
from DeFiQA import DeFiQA
from config import DOC_MODEL, CODE_MODEL, OPENAI_API_KEY
from gpt_utils import extract_contract_names_as_list, get_chat_completion_response
import shutil
import openai

openai.api_key = OPENAI_API_KEY

if st.session_state.get("begin_query") is None:
    st.session_state["begin_query"] = 0
if st.session_state.get("begin_query_doc") is None:
    st.session_state["begin_query_doc"] = 0

st.title("Q-A Bot")


def clear_all_cache():
    if st.session_state.get("qa"):
        paths = [
            st.session_state.get("qa").embeddings_path_doc,
            st.session_state.get("qa").contracts_path.parent,
        ]
        for path in paths:
            os.remove(path) if path.is_file() else shutil.rmtree(path)
    else:
        st.write("Please provide a URL first!")


with st.form("url_form"):
    doc_url = st.text_input(
        "Enter a documentation URL",
        key="doc_url",
        placeholder="https://docs.lyra.finance/overview/how-does-lyra-work",
    )
    contract_url = st.text_input(
        "Enter a contracts URL",
        key="contract_url",
        placeholder="https://github.com/lyra-finance/lyra-protocol/tree/master/contracts",
    )

    submitted = st.form_submit_button("Submit")
    if submitted:
        try:
            with st.spinner("Loading DeFiQA... [will take a while for the first time]"):
                st.session_state["qa"] = DeFiQA(
                    doc_url, contract_url
                )  # clear_cache=True
                if doc_url and contract_url:
                    st.write("Docs:", st.session_state["qa"].doc_url)
                    st.session_state["begin_query"] = 1
        except Exception:
            st.write("Bad URL!")
            st.write(Exception)

if submitted:
    st.button(
        "Clear all cache", on_click=clear_all_cache, help="Not allowed", disabled=True
    )


def get_answer_contracts(contract_names, query, answer_doc, answer_placeholder):
    with st.spinner("Fetching the answer"):
        answer_contract = answer_doc + "\n" * 2
        messages = st.session_state["qa"].get_messages_contract(contract_names, query)
        for i, message in enumerate(messages):
            # TODO:
            print("i", i)
            print("add", f"{i+1}. {contract_names[i]}:\n")
            answer_contract += f"{i+1}. {contract_names[i]}:\n"
            answer_placeholder.write(answer_contract)
            for split_message in message:
                answer_chunk_contract = get_chat_completion_response(
                    openai,
                    CODE_MODEL,
                    "You answer questions about provided Smart Contracts belonging to a DeFi protocol. You never mention the source of your answer",
                    split_message,
                    stream=True,
                )
                for chunk in answer_chunk_contract:
                    if chunk["choices"][0]["delta"].get("content"):
                        answer_contract += chunk["choices"][0]["delta"]["content"]
                        answer_placeholder.write(answer_contract)
                answer_contract += "\n"
                answer_placeholder.write(answer_contract)
                print("answer_contract 1 slash", answer_contract)
            answer_contract += "\n\n"
            print("answer_contract 2 slash", answer_contract)
            answer_placeholder.write(answer_contract)


if st.session_state["begin_query"] == 1:
    with st.form("query_form"):
        query = st.text_input(
            "Ask", key="question_doc", placeholder="How much is the deposit fee?"
        )
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["begin_query_doc"] = 1


if st.session_state["begin_query_doc"] == 1:
    contract_names = []
    answer_doc = ""
    st.write("Question: ", query)
    answer_placeholder = st.empty()
    spinner = st.spinner("Fetching the answer...")
    with spinner:
        answer_doc = ""
        answer_chunk_doc = st.session_state["qa"].ask_doc(query, DOC_MODEL, stream=True)
        for chunk in answer_chunk_doc:
            print("chunk", chunk)
            if chunk["choices"][0]["delta"].get("content"):
                answer_doc += chunk["choices"][0]["delta"]["content"]
                answer_placeholder.write(answer_doc)

        contract_names = extract_contract_names_as_list(answer_doc, openai, DOC_MODEL)
    print("contract_names, query", contract_names, query)
    if len(contract_names):
        st.button(
            "more...",
            on_click=get_answer_contracts,
            args=(contract_names, query, answer_doc, answer_placeholder),
        )
    st.session_state["begin_query_doc"] = 0
