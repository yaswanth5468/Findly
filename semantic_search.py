import torch

from transformers import AutoTokenizer, AutoModel


model_name = "sentence-transformers/all-MiniLM-L6-v2"


tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

model = AutoModel.from_pretrained(
    model_name
)


document_index = torch.load(
    "document_embeddings.pt",
    weights_only=False
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

    return embedding[0]


def search_documents(query):

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