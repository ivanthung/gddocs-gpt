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
API_KEY = ""
DEFAULT_URL = ""
DEFAULT_PROMPT = "Edit the following text, making the language more clear and convincing: "


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
        if st.session_state.authorized:
            if(not st.session_state.revise):
                uploaded_file = st.text_input(
                    label="Enter the URL of the Google Docs file you want to edit",
                    value=DEFAULT_URL,
                )
            else:
                uploaded_file = st.text_input(
                    label="Enter the URL of the Google Docs file you want to edit",
                    value=st.session_state.revised_url,
                )
        else:
            uploaded_file = None
            st.write(
                "Authorize with OpenAI API key in the sidebar to use this service."
            )
        if st.session_state.prompt == DEFAULT_PROMPT:
            st.session_state.prompt = st.text_input(
                "Editing prompt", value=DEFAULT_PROMPT
            )
        else:
            st.session_state.prompt = st.text_input(
                "Editing prompt", value=st.session_state.prompt
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

    ######## DISPLAY FILE ########

    if uploaded_file is not None:
        st.session_state["default_checkbox_value"] = False
        document_id = gd.get_documentid(uploaded_file)
        st.session_state.document = gd.get_doc(document_id)

        if(st.session_state.document and st.session_state.selected_paragraphs == []):
            st.session_state.paragraphs = gd.get_paragraphs(st.session_state.document)
            checkbox_status = []
            with st.form(key="data_approval"):
                for i, p in enumerate(st.session_state.paragraphs):
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
                            st.session_state.selected_paragraphs.append(st.session_state.paragraphs[i])
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
        else:
            st.warning("Document not found. Please check the URL and try again.")

    ######## GENERATE COPY-EDIT ########

    if st.session_state.selected_paragraphs != []:
        if st.button("Generate AI-created copy-edit"):
            print("tripped!")
            with st.spinner("Generating copy-edit..."):
                st.session_state.response_paragraphs = ai_handler.get_copy_edit(
                    st.session_state.selected_paragraphs, st.session_state.api_key, st.session_state.prompt
                )
                assert len(st.session_state.response_paragraphs) == len(st.session_state.selected_paragraphs)
                assert len(st.session_state.paragraphs) == len(st.session_state.selected_paragraphs)

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

            ######## Compose new document from our copy-edit ########

            new_id = gd.compose_doc(
                title=title,
                original_paragraphs=st.session_state.paragraphs,
                edited_paragraphs=st.session_state.response_paragraphs,
                original_doc = st.session_state.document,
            )

            st.session_state.revised_url = f"https://docs.google.com/document/d/{new_id}/edit#"
            st.markdown(
                get_st_button_a_tag(
                    st.session_state.revised_url,
                    f"Copy-edit doc title: {title}",
                ), unsafe_allow_html=True
            )
            st.session_state.revise = st.button("Revise this edit?")


def init_defaults():
    if "selected_paragraphs" not in st.session_state:
        st.session_state.selected_paragraphs = []

    if "response_paragraphs" not in st.session_state:
        st.session_state.response_paragraphs = []

    if "saved_doc" not in st.session_state:
        st.session_state.saved_doc = io.BytesIO()

    if "submit_botton" not in st.session_state:
        st.session_state.submit_button = False

    if "prompt" not in st.session_state:
        st.session_state.prompt = DEFAULT_PROMPT

    if "authorized" not in st.session_state:
        st.session_state.authorized = False

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    if "document" not in st.session_state:
        st.session_state.document = None

    if "revise" not in st.session_state:
        st.session_state.revise = False

    if "revise_url" not in st.session_state:
        st.session_state.revise_url = ""

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
