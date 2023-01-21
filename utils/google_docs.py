from __future__ import print_function
import os.path
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.postrequests import create_insert_request, create_styling_request
from utils.diff_handler import get_difference, create_color_indexes


SCOPES = {
    "read": "https://www.googleapis.com/auth/documents.readonly",
    "write": "https://www.googleapis.com/auth/documents",
}

SUGGEST_MODE = "PREVIEW_SUGGESTIONS_ACCEPTED"

COLORS = {
    "green": {
        "red": 0.3,
        "green": 0.5,
        "blue": 0.0,
    },
    "black": {
        "red": 0.0,
        "green": 0.0,
        "blue": 0.0,
    },
    "red": {
        "red": 1.0,
        "green": 0.0,
        "blue": 0.0,
    },
}


def compose_doc(title="My Document", original_paragraphs=[], edited_paragraphs=[]):
    """
    Composes a document with the given title and paragraphs. Returns the document ID.
    Works backwards from the end of the document to the beginning.
    Add coloring for edited paragraphs.
    """
    requests = []
    for i in range(0, len(edited_paragraphs)):
        if edited_paragraphs[i] == "":
            end_index = len(original_paragraphs[i])
            if end_index > 1:
                requests.append(create_styling_request(1, end_index, COLORS["black"]))
            requests.append(create_insert_request(1, original_paragraphs[i]))
        else:
            diff = get_difference(original_paragraphs[i], edited_paragraphs[i])
            styles = [
                create_styling_request(s[0] + 1, s[1] + 1, COLORS["green"])
                for s in create_color_indexes(diff)
            ]
            requests.extend(styles)

            # Need to override with a black style the whole paragraph, otherwise the green style will be applied to the whole paragraph.
            end_index = len(edited_paragraphs[i])
            requests.append(create_styling_request(1, end_index, COLORS["black"]))
            requests.append(create_insert_request(1, edited_paragraphs[i] + "\n"))
    doc = create_doc(title)
    document_id = doc.get("documentId")
    update_document(document_id, list(reversed(requests)))

    return document_id


def create_doc(title="My Document"):
    service = authorize("write")
    body = {
        "title": title,
    }
    doc = service.documents().create(body=body).execute()
    return doc


# The ID of a sample document.
def get_doc(document_id):
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    Returns the document as an object
    """

    service = authorize("write")
    document = (
        service.documents()
        .get(documentId=document_id, suggestionsViewMode=SUGGEST_MODE)
        .execute()
    )
    print("The title of the document is: {}".format(document.get("title")))
    return document


def authorize(scope):
    "Authorizing to the Docs API. Returns the service with credentials"
    # If modifying these scopes, delete the file token.json.
    if scope == "read":
        sel_scope = SCOPES["read"]
    elif scope == "write":
        sel_scope = SCOPES["write"]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", sel_scope)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            os.remove("/Users/ivanthung/code/ivanthung/google_doc_editor/token.json")
            authorize(scope)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", sel_scope
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        if not os.path.exists("token.json"):
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    if creds.valid:
        try:
            service = build("docs", "v1", credentials=creds)
            return service

        except HttpError as err:
            print(err)

    pass


def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

    Args:
        element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get("textRun")
    if not text_run:
        return ""
    return text_run.get("content")


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
    in nested elements.

    Args:
        elements: a list of Structural Elements.
    """
    text = ""
    for value in elements:
        if "paragraph" in value:
            elements = value.get("paragraph").get("elements")
            for elem in elements:
                text += read_paragraph_element(elem)
        elif "table" in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get("table")
            for row in table.get("tableRows"):
                cells = row.get("tableCells")
                for cell in cells:
                    text += read_structural_elements(cell.get("content"))
        elif "tableOfContents" in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get("tableOfContents")
            text += read_structural_elements(toc.get("content"))
    return text


def get_paragraphs(document):
    """Gets the text in the document.
    Args:
        document: a Google Doc.
    Returns:
        list of text content paragraphs in the document. Each paragraph is a string. Deletions and additions are included.
    """
    elements = document.get("body").get("content")
    text = []
    for value in elements:
        if "paragraph" in value:
            elements = value.get("paragraph").get("elements")
            paragraph_text = ""
            for elem in elements:
                paragraph_text += read_paragraph_element(elem)
            text.append(paragraph_text)
    return text


def get_documentid(doc_url):
    match = re.search(r"\/document\/d\/([a-zA-Z0-9-_]+)", doc_url)

    if match:
        document_id = match.group(1)
        return document_id

    else:
        print("No match found.")
        return 0


def update_document(document_id, requests):
    service = authorize("write")
    try:
        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()
        print("success")
    except Exception as e:
        print(e)


def get_paragraphs_with_index(document):
    """Gets the text in the document.
    Args:
        document: a Google Doc.
    Returns:
        list of text content paragraphs in the document, including start and end index.
    """
    elements = document.get("body").get("content")
    paragraph_object = []
    for value in elements:
        if "paragraph" in value:
            elements = value.get("paragraph").get("elements")
            paragraph_text = ""
            start_index = elements[0].get("startIndex")
            end_index = elements[-1].get("endIndex")
            for elem in elements:
                paragraph_text += read_paragraph_element(elem)
            paragraph_object.append(
                {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "text": paragraph_text,
                }
            )
    return paragraph_object
