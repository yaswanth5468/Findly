import os

import torch

from transformers import AutoTokenizer, AutoModel

from pypdf import PdfReader

from docx import Document


model_name = "sentence-transformers/all-MiniLM-L6-v2"


tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

model = AutoModel.from_pretrained(
    model_name
)


def get_embedding(text):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True
    )

    with torch.no_grad():

        output = model(**inputs)

    embedding = output.last_hidden_state.mean(
        dim=1
    )

    embedding = embedding / embedding.norm(
        dim=1,
        keepdim=True
    )

    return embedding


def read_txt(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()

    except:

        return ""


def read_pdf(path):

    text = ""

    try:

        reader = PdfReader(path)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

    except:

        pass

    return text


def read_docx(path):

    text = ""

    try:

        document = Document(path)

        for paragraph in document.paragraphs:

            if paragraph.text:

                text += paragraph.text + "\n"

    except:

        pass

    return text


def read_document(path):

    extension = os.path.splitext(
        path
    )[1].lower()

    if extension == ".txt":

        return read_txt(path)

    if extension == ".pdf":

        return read_pdf(path)

    if extension == ".docx":

        return read_docx(path)

    return ""


def search_semantic_documents(
    query,
    folder,
    threshold=0.30
):

    query_embedding = get_embedding(
        query
    )

    results = []

    for root, folders, files in os.walk(folder):

        folders[:] = [
            folder_name
            for folder_name in folders
            if folder_name != ".venv"
        ]

        for file in files:

            extension = os.path.splitext(
                file
            )[1].lower()

            if extension not in [
                ".txt",
                ".pdf",
                ".docx"
            ]:

                continue

            path = os.path.join(
                root,
                file
            )

            text = read_document(
                path
            )

            if not text.strip():

                continue

            document_embedding = get_embedding(
                text[:5000]
            )

            score = torch.dot(
                query_embedding[0],
                document_embedding[0]
            ).item()

            if score >= threshold:

                results.append(
                    (
                        path,
                        score
                    )
                )

    results.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return results