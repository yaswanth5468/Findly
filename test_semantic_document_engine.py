from semantic_document_engine import (
    search_semantic_documents
)


folder = input(
    "Folder to search: "
)

query = input(
    "What are you looking for? "
)


results = search_semantic_documents(
    query,
    folder
)


print(
    "\nSemantic Results:\n"
)


for path, score in results:

    print(
        "File:",
        path
    )

    print(
        "Similarity:",
        round(score, 4)
    )

    print(
        "-" * 50
    )


print(
    "\nTotal results:",
    len(results)
)