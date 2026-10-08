
import os
import torch

from document_index import get_embedding

def search_documents(query):

    index_path = "document_embeddings.pt"

    if not os.path.exists(index_path):
        return []

    try:
        document_index = torch.load(
            index_path,
            weights_only=False
        )
    except Exception as error:
        print("Could not load document index:", error)
        return []

    query_embedding = get_embedding(
        query
    )

    results = []

    for path, document_embedding in document_index:

        score = torch.dot(
            query_embedding,
            document_embedding
        ).item()

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