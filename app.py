import streamlit as st
from DeFiQA import DeFiQA
from config import SAVE_PATH
import shutil

if st.session_state.get("begin_doc_query") is None:
    st.session_state["begin_doc_query"] = 0
if st.session_state.get("begin_contract_query") is None:
    st.session_state["begin_contract_query"] = 0

st.title("Q-A Bot")

st.button(
    "Clear all cache",
    on_click=lambda path: shutil.rmtree(path) if path.exists() else None,
    args=(SAVE_PATH,),
)

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
                    st.session_state["begin_doc_query"] = 1
                if contract_url:
                    st.write("Contracts:", st.session_state["qa"].conracts_dir_url)
                    st.session_state["begin_contract_query"] = 1
        except:
            st.write("Bad URL!")


if st.session_state["begin_doc_query"] == 1:
    with st.form("query_doc_form"):
        query = st.text_input(
            "Ask Docs", key="question_doc", placeholder="How much is the deposit fee?"
        )
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.write("Question: ", query)
            with st.spinner("Fetching the answer..."):
                answer = st.session_state["qa"].ask_doc(query)
                st.write("Answer", answer)

if st.session_state["begin_contract_query"] == 1:
    with st.form("query_contract_form"):
        query = st.text_input(
            "Ask Contracts",
            key="question_contract",
            placeholder='explain the "getBoardAndStrikeDetails" function of optionmarket contract',
        )
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.write("Question: ", query)
            with st.spinner("Fetching the answer..."):
                answer = st.session_state["qa"].ask_contract(query)
                st.write("Answer", answer)
