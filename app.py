import streamlit as st
import openai
import utils.google_docs as gd
import utils.ai_handler as ai_handler
from utils.diff_handler import render_diff
import io
from datetime import datetime

pricing_dict = {"ada": 0.0004, "babbage": 0.0005, "curie": 0.002, "davinci": 0.02}

st.set_page_config(layout="wide")
path = "index.html"

backup = "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"
API_KEY = "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"
URL = "https://docs.google.com/document/d/1JD7mIqhSL78gsxtGmBTL3T9ErCXSGlknrPdZVHd0cWA/edit#"


def app():
    st.title("First draft editor")
    # session variables
    with st.sidebar:
        st.title("First draft editor using GPT3")
        st.markdown(
            """This is a proof of concept for an copy-editing program using GPT3. It is not intended for production use.
                 It uses the OpenAI API and is subject to the OpenAI terms of service. To use this service you need to have an OpenAI API key.
                 You can obtain one for free at https://beta.openai.com/account/api-keys.
                 You will not be charged unless you exceed the free tier limits, which starts with 18 dollars.
                 If you want to know more, you can get in touch at github.com/ivanthung.

                 Note: This service is a proof of concept. It does not take into account formatting of the original word document, footnotes, tables, etc.
                 It will only work with word documents that consist of simple paragraphs. Future versions may include this (if I have time for it!)
                 """
        )

    init_defaults()

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.authorized == True:
            uploaded_file = st.text_input(
                label="Enter the URL of the Google Docs file you want to edit",
                value=URL,
            )
        else:
            uploaded_file = None
            st.write(
                "Authorize with OpenAI API key in the sidebar to use this service."
            )
    with col2:
        st.subheader("Instructions")
        st.markdown(
            """
        This service uses a basic editing prompt to suggest changes to wordfile that you can upload.
        Instrutions:
        1. Paste the link to your google docs file
        2. Select the paragraphs you want to edit.
        3. Generate the copy-edit.
        5. Create a new google docs, copy the text from the copy-edit and paste it in the new document.
        The copy-edit will be included in the text of the wordfile and the original text will be included as a comment.
        THIS VERSION ONLY WORKS WITH ENGLISH DOCUMENTS.
        """
        )

    if uploaded_file is not None:
        st.session_state["default_checkbox_value"] = False
        document_id = gd.get_documentid(uploaded_file)
        document = gd.get_doc(document_id)

        st.session_state.document = document
        paragraphs = gd.get_paragraphs(document)

        checkbox_status = []
        with st.form(key="data_approval"):
            st.session_state.paragraphs = paragraphs
            for i, p in enumerate(paragraphs):
                checkbox_status.append(
                    st.checkbox(
                        key=i, label=p, value=st.session_state["default_checkbox_value"]
                    )
                )
            approve_button = st.form_submit_button(label="Calculate costs")

        if approve_button:
            if any(checkbox_status):
                for i, c in enumerate(checkbox_status):
                    if c:
                        st.session_state.selected_paragraphs.append(paragraphs[i])
                    else:
                        st.session_state.selected_paragraphs.append("")
                combined = "/n".join(st.session_state.selected_paragraphs)
                tokens = int(ai_handler.get_tokens(combined))

                st.info(
                    f"This action will consume about: {tokens} tokens from the model 'davinci'. This will cost approximately {round((tokens / 1000) * pricing_dict['davinci'], 4)} dollars.\n Please confirm to proceed.",
                    icon="ℹ️",
                )
            else:
                st.warning("No paragraphs selected!")

    if st.session_state.selected_paragraphs != []:
        if st.button("Generate AI-created copy-edit"):
            with st.spinner("Generating copy-edit..."):
                st.session_state.response_paragraphs = ai_handler.get_copy_edit(
                    st.session_state.selected_paragraphs, st.session_state.api_key
                )
            st.header("Preview of copy edits.")
            for i in range(0, len(st.session_state.response_paragraphs)):
                s1 = st.session_state.paragraphs[i]
                s2 = (
                    st.session_state.response_paragraphs[i]
                    if (st.session_state.response_paragraphs[i] != "")
                    else st.session_state.paragraphs[i]
                )
                page = render_diff(s1, s2)
                st.markdown(page, unsafe_allow_html=True)

            title = (
                st.session_state.document.get("title")
                + "_edit_"
                + datetime.today().strftime("%Y-%m-%d")
            )
            new_id = gd.compose_doc(
                title=title,
                original_paragraphs=st.session_state.paragraphs,
                edited_paragraphs=st.session_state.response_paragraphs,
            )

            st.markdown(
                get_st_button_a_tag(
                    f"https://docs.google.com/document/d/{new_id}/edit#",
                    f"Here's your edit! -> {title}",
                    unsafe_allow_html=True,
                )
            )


def init_defaults():
    if "selected_paragraphs" not in st.session_state:
        st.session_state.selected_paragraphs = []

    if "response_paragraphs" not in st.session_state:
        st.session_state.response_paragraphs = []

    if "saved_doc" not in st.session_state:
        st.session_state.saved_doc = io.BytesIO()

    if "submit_botton" not in st.session_state:
        st.session_state.submit_button = False

    if "authorized" not in st.session_state:
        st.session_state.authorized = False

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    if "document" not in st.session_state:
        st.session_state.document = None

    with st.sidebar:
        st.session_state.api_key = st.text_input(
            "Put your OpenAI Api Key here", type="password", value=API_KEY
        )

        if st.session_state.api_key != "":
            openai.api_key = st.session_state.api_key
            try:
                openai.Model.list()
                st.markdown(
                    f"Valid API key ending with: {st.session_state.api_key[-4:]}"
                )
                st.session_state.authorized = True
            except:
                st.error("API key not valid, please check and try again.")
                st.session_state.authorized = False


def get_st_button_a_tag(url_link, button_name):
    """
    generate html a tag
    :param url_link:
    :param button_name:
    :return:
    """
    return f"""
    <a href={url_link}><button style="
    fontWeight: 400;
    padding: 0.25rem 0.75rem;
    borderRadius: 0.25rem;
    margin: 0px;
    lineHeight: 1.6;
    width: auto;
    userSelect: none;
    backgroundColor: #FFFFFF;
    border: 1px solid rgba(49, 51, 63, 0.2);">{button_name}</button></a>
    """


if __name__ == "__main__":
    app()
