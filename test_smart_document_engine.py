from smart_document_engine import (
    search_smart_documents
)


folder = input(
    "Folder to search: "
)

query = input(
    "What are you looking for? "
)


results = search_smart_documents(
    query,
    folder
)


print(
    "\nSmart Document Results:\n"
)


for result in results:

    print(
        "Type:",
        result[0]
    )

    print(
        "File:",
        result[1]
    )

    if result[2]:

        print(
            "Page/Paragraph:",
            result[2]
        )

    if result[3]:

        print(
            "Match:",
            result[3]
        )

    print(
        "Combined Score:",
        round(result[4], 4)
    )

    print(
        "-" * 50
    )


print(
    "\nTotal results:",
    len(results)
)