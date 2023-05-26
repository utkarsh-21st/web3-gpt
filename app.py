import streamlit as st
from GitBook import GitBook
from config import SAVE_PATH
import shutil

if st.session_state.get("begin_query") is None:
    st.session_state["begin_query"] = 0

st.title("Q-A Bot")

st.button(
    "Clear all cache",
    on_click=lambda path: shutil.rmtree(path) if path.exists() else None,
    args=(SAVE_PATH,),
)

with st.form("url_form"):
    url = st.text_input("Enter URL", key="url")

    submitted = st.form_submit_button("Submit")
    if submitted:
        try:
            with st.spinner(
                "Loading GitBook... [will take a while for the first time]"
            ):
                st.session_state["gitbook"] = GitBook(url)  # clear_cache=True
                st.write("GitBook:", st.session_state["gitbook"].book_url)
                st.session_state["begin_query"] = 1
        except:
            st.write("Bad URL!")


if st.session_state["begin_query"] == 1:
    with st.form("query_form"):
        query = st.text_input("Question", key="question")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.write("Question: ", query)
            with st.spinner("Fetching the answer..."):
                answer = st.session_state["gitbook"].ask(query)
                st.write("Answer", answer)
