import os
import streamlit as st
from DeFiQA import DeFiQA
from config import MODEL, MODEL, OPENAI_API_KEY
from gpt_utils import (
    extract_contract_names_as_list,
    get_chat_completion_response,
    get_multiple_queries,
)
import shutil
import openai

openai.api_key = OPENAI_API_KEY

if st.session_state.get("begin_query") is None:
    st.session_state["begin_query"] = False
if st.session_state.get("begin_query_doc") is None:
    st.session_state["begin_query_doc"] = False
if st.session_state.get("answer_more") is None:
    st.session_state["answer_more"] = False

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
                if doc_url:
                    st.write("Docs:", st.session_state["qa"].doc_url)
                    st.session_state["begin_query"] = True
            st.session_state["begin_query_doc"] = False
        except Exception:
            st.write("Bad URL!")
            st.write(Exception)

if submitted:
    st.button(
        "Clear all cache", on_click=clear_all_cache, help="Not allowed", disabled=True
    )


def get_answer_contracts(contract_names, query, answer_placeholder):
    with st.spinner("Fetching the answer"):
        answer = st.session_state["answer"] + "\n" * 2
        messages = st.session_state["qa"].get_messages_contract(contract_names, query)
        for i, message in enumerate(messages):
            # TODO:
            print("i", i)
            print("add", f"{i+1}. {contract_names[i]}:\n")
            answer += f"{i+1}. {contract_names[i]}:\n"
            answer_placeholder.write(answer)
            for split_message in message:
                answer_chunk_contract = get_chat_completion_response(
                    openai,
                    MODEL,
                    "You answer questions about provided Smart Contracts belonging to a DeFi protocol. You never mention the source of your answer",
                    split_message,
                    stream=True,
                )
                for chunk in answer_chunk_contract:
                    if chunk["choices"][0]["delta"].get("content"):
                        answer += chunk["choices"][0]["delta"]["content"]
                        answer_placeholder.write(answer)
                answer += "\n"
                answer_placeholder.write(answer)
                print("answer 1 slash", answer)
            answer += "\n\n"
            print("answer 2 slash", answer)
            answer_placeholder.write(answer)
    st.session_state["answer_more"] = True
    st.session_state["answer"] = answer


def get_answer_docs(query):
    answer_placeholder = st.empty()
    spinner = st.spinner("Fetching the answer...")
    answer_doc = ""
    if query:
        with spinner:
            queries = get_multiple_queries(query, openai, MODEL)
            for query_split in queries:
                answer_doc += (
                    "***Question***: " + query_split + "  \n" + "***Answer***: "
                )
                answer_placeholder.write(answer_doc)
                answer_chunk_doc = st.session_state["qa"].ask_doc(
                    query_split, MODEL, stream=True
                )
                for chunk in answer_chunk_doc:
                    if chunk["choices"][0]["delta"].get("content"):
                        answer_doc += chunk["choices"][0]["delta"]["content"]
                        answer_placeholder.write(answer_doc)
                answer_doc += "\n" * 30
                answer_placeholder.write(answer_doc)
    st.session_state["answer"] = answer_doc

    if st.session_state["qa"].contracts_path:
        contract_names = extract_contract_names_as_list(answer_doc, openai, MODEL)
        print("contract_names, query", contract_names, query)
        if len(contract_names):
            st.button(
                "more...",
                on_click=get_answer_contracts,
                args=(contract_names, query, answer_placeholder),
            )


if st.session_state["begin_query"] == True:
    with st.form("query_form"):
        query = st.text_input(
            "Ask",
            key="question_doc",
            placeholder="What are positions in Lyra and how to open and close them? Explain in detail.",
        )
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["begin_query_doc"] = True
            st.session_state["answer_more"] = False

if st.session_state["begin_query_doc"]:
    if not st.session_state["answer_more"]:
        get_answer_docs(query)
    else:
        answer_placeholder = st.empty()
        answer_placeholder.write(st.session_state["answer"])
