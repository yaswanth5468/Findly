
import os
import torch

from transformers import AutoTokenizer, AutoModel
from pypdf import PdfReader
from docx import Document


# ============================================================
# MODEL
# ============================================================

model_name = "sentence-transformers/all-MiniLM-L6-v2"


tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

model = AutoModel.from_pretrained(
    model_name
)


# ============================================================
# INDEX FILES
# ============================================================

INDEX_PATH = "document_embeddings.pt"

METADATA_PATH = "document_metadata.pt"


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx"
}


# ============================================================
# CREATE EMBEDDING
# ============================================================

def get_embedding(text):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True
    )

    with torch.no_grad():

        output = model(
            **inputs
        )

    embedding = output.last_hidden_state.mean(
        dim=1
    )

    embedding = embedding / embedding.norm(
        dim=1,
        keepdim=True
    )

    return embedding[0]


# ============================================================
# READ TXT
# ============================================================

def read_txt(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()

    except Exception as error:

        print(
            "\nFAILED TO READ TXT"
        )

        print(
            "File:",
            path
        )

        print(
            "Error:",
            error
        )

        return ""


# ============================================================
# READ PDF
# ============================================================

def read_pdf(path):

    text = ""

    try:

        reader = PdfReader(
            path
        )

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            try:

                page_text = page.extract_text()

                if page_text:

                    text += (
                        page_text
                        + "\n"
                    )

            except Exception as error:

                print(
                    "\nFAILED TO READ PDF PAGE"
                )

                print(
                    "File:",
                    path
                )

                print(
                    "Page:",
                    page_number
                )

                print(
                    "Error:",
                    error
                )

    except Exception as error:

        print(
            "\nFAILED TO READ PDF"
        )

        print(
            "File:",
            path
        )

        print(
            "Error:",
            error
        )

    return text


# ============================================================
# READ DOCX
# ============================================================

def read_docx(path):

    text = ""

    try:

        document = Document(
            path
        )

        for paragraph in document.paragraphs:

            if paragraph.text:

                text += (
                    paragraph.text
                    + "\n"
                )

    except Exception as error:

        print(
            "\nFAILED TO READ DOCX"
        )

        print(
            "File:",
            path
        )

        print(
            "Error:",
            error
        )

    return text


# ============================================================
# READ DOCUMENT
# ============================================================

def read_document(path):

    extension = os.path.splitext(
        path
    )[1].lower()

    if extension == ".txt":

        return read_txt(
            path
        )

    if extension == ".pdf":

        return read_pdf(
            path
        )

    if extension == ".docx":

        return read_docx(
            path
        )

    return ""


# ============================================================
# FILE METADATA
# ============================================================

def get_file_metadata(path):

    stat = os.stat(
        path
    )

    return {
        "mtime": stat.st_mtime,
        "size": stat.st_size
    }


# ============================================================
# CHECK WHETHER FILE IS INSIDE FOLDER
# ============================================================

def is_inside_folder(path, folder):

    try:

        return os.path.commonpath(
            [
                os.path.abspath(path),
                os.path.abspath(folder)
            ]
        ) == os.path.abspath(folder)

    except ValueError:

        return False


# ============================================================
# LOAD SAVED INDEX + METADATA
# ============================================================

def load_saved_data():

    index = []

    metadata = {}

    # --------------------------------------------------------
    # Load embeddings
    # --------------------------------------------------------

    if os.path.exists(
        INDEX_PATH
    ):

        try:

            index = torch.load(
                INDEX_PATH,
                weights_only=False
            )

        except Exception as error:

            print(
                "Could not load document index:",
                error
            )

            return None, None

    # --------------------------------------------------------
    # Load metadata
    # --------------------------------------------------------

    if os.path.exists(
        METADATA_PATH
    ):

        try:

            metadata = torch.load(
                METADATA_PATH,
                weights_only=False
            )

        except Exception as error:

            print(
                "Could not load document metadata:",
                error
            )

            return None, None

    return index, metadata


# ============================================================
# SAVE INDEX + METADATA
# ============================================================

def save_index(
    index,
    metadata
):

    torch.save(
        index,
        INDEX_PATH
    )

    torch.save(
        metadata,
        METADATA_PATH
    )


# ============================================================
# CREATE DOCUMENT INDEX
# ============================================================

def create_document_index(folder):

    folder = os.path.abspath(
        folder
    )

    print(
        "\nCreating document index...\n"
    )

    add_folder_to_index(
        folder
    )


# ============================================================
# ADD / UPDATE FOLDER INDEX
# ============================================================

def add_folder_to_index(folder):

    folder = os.path.abspath(
        folder
    )

    # --------------------------------------------------------
    # Load existing index
    # --------------------------------------------------------

    index, metadata = load_saved_data()

    if index is None:

        return

    # --------------------------------------------------------
    # Keep documents from other folders
    # --------------------------------------------------------

    updated_index = []

    updated_metadata = {}

    for item in index:

        try:

            path = os.path.abspath(
                item[0]
            )

            embedding = item[1]

        except Exception as error:

            print(
                "\nInvalid index entry:"
            )

            print(
                "Entry:",
                item
            )

            print(
                "Error:",
                error
            )

            continue

        if not is_inside_folder(
            path,
            folder
        ):

            updated_index.append(
                (
                    path,
                    embedding
                )
            )

            if path in metadata:

                updated_metadata[path] = (
                    metadata[path]
                )

    # --------------------------------------------------------
    # Find all supported documents
    # --------------------------------------------------------

    current_files = set()

    for root, folders, files in os.walk(
        folder
    ):

        # Don't scan virtual environments
        folders[:] = [
            name
            for name in folders
            if name != ".venv"
        ]

        for file in files:

            extension = os.path.splitext(
                file
            )[1].lower()

            if extension not in SUPPORTED_EXTENSIONS:

                continue

            path = os.path.abspath(
                os.path.join(
                    root,
                    file
                )
            )

            current_files.add(
                path
            )

    # --------------------------------------------------------
    # Existing entries for this folder
    # --------------------------------------------------------

    old_entries = {}

    for item in index:

        try:

            path = os.path.abspath(
                item[0]
            )

            embedding = item[1]

        except:

            continue

        if is_inside_folder(
            path,
            folder
        ):

            old_entries[path] = (
                embedding
            )

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    print(
        "\nChecking documents in:",
        folder
    )

    newly_indexed = 0

    updated_documents = 0

    skipped_documents = 0

    failed_documents = 0

    # --------------------------------------------------------
    # Process documents
    # --------------------------------------------------------

    for path in sorted(
        current_files
    ):

        print(
            "\nChecking:",
            path
        )

        # ----------------------------------------------------
        # Read file metadata
        # ----------------------------------------------------

        try:

            current_metadata = (
                get_file_metadata(
                    path
                )
            )

        except OSError as error:

            print(
                "\nFAILED TO INSPECT FILE"
            )

            print(
                "File:",
                path
            )

            print(
                "Error:",
                error
            )

            failed_documents += 1

            continue

        # ----------------------------------------------------
        # Previous metadata
        # ----------------------------------------------------

        old_metadata = metadata.get(
            path
        )

        # ----------------------------------------------------
        # Check whether document is unchanged
        # ----------------------------------------------------

        if (
            path in old_entries
            and old_metadata is not None
            and old_metadata.get(
                "mtime"
            ) == current_metadata.get(
                "mtime"
            )
            and old_metadata.get(
                "size"
            ) == current_metadata.get(
                "size"
            )
        ):

            updated_index.append(
                (
                    path,
                    old_entries[path]
                )
            )

            updated_metadata[path] = (
                old_metadata
            )

            skipped_documents += 1

            print(
                "Unchanged - skipped."
            )

            continue

        # ----------------------------------------------------
        # New or modified document
        # ----------------------------------------------------

        print(
            "Indexing:",
            os.path.basename(
                path
            )
        )

        # ----------------------------------------------------
        # Read document
        # ----------------------------------------------------

        text = read_document(
            path
        )

        # ----------------------------------------------------
        # Empty / unreadable document
        # ----------------------------------------------------

        if not text.strip():

            print(
                "\nDOCUMENT COULD NOT BE INDEXED"
            )

            print(
                "File:",
                path
            )

            print(
                "Reason: No readable text found."
            )

            # Keep previous version if available
            if path in old_entries:

                updated_index.append(
                    (
                        path,
                        old_entries[path]
                    )
                )

                if old_metadata is not None:

                    updated_metadata[path] = (
                        old_metadata
                    )

            failed_documents += 1

            continue

        # ----------------------------------------------------
        # Create embedding
        # ----------------------------------------------------

        try:

            embedding = get_embedding(
                text[:5000]
            )

        except Exception as error:

            print(
                "\nFAILED TO CREATE EMBEDDING"
            )

            print(
                "File:",
                path
            )

            print(
                "Error:",
                error
            )

            # Keep previous version if available
            if path in old_entries:

                updated_index.append(
                    (
                        path,
                        old_entries[path]
                    )
                )

                if old_metadata is not None:

                    updated_metadata[path] = (
                        old_metadata
                    )

            failed_documents += 1

            continue

        # ----------------------------------------------------
        # Save new embedding
        # ----------------------------------------------------

        updated_index.append(
            (
                path,
                embedding
            )
        )

        updated_metadata[path] = (
            current_metadata
        )

        # ----------------------------------------------------
        # Count new vs updated
        # ----------------------------------------------------

        if path in old_entries:

            updated_documents += 1

            print(
                "Document updated."
            )

        else:

            newly_indexed += 1

            print(
                "New document indexed."
            )

    # --------------------------------------------------------
    # Detect removed documents
    # --------------------------------------------------------

    removed_documents = sum(
        1
        for path in old_entries
        if path not in current_files
    )

    # --------------------------------------------------------
    # Save everything
    # --------------------------------------------------------

    save_index(
        updated_index,
        updated_metadata
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "Folder refresh complete."
    )

    print(
        "================================"
    )

    print(
        "New documents:",
        newly_indexed
    )

    print(
        "Updated documents:",
        updated_documents
    )

    print(
        "Unchanged documents skipped:",
        skipped_documents
    )

    print(
        "Removed documents:",
        removed_documents
    )

    print(
        "Documents that could not be indexed:",
        failed_documents
    )

    print(
        "Total documents in index:",
        len(updated_index)
    )

    print(
        "================================\n"
    )


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    folder = input(
        "Folder to index: "
    ).strip()

    if os.path.isdir(
        folder
    ):

        create_document_index(
            folder
        )

    else:

        print(
            "Folder does not exist."
        )

