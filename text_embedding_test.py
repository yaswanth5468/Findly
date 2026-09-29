from transformers import AutoTokenizer, AutoModel
import torch


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


text1 = "Python Flask MongoDB project"

text2 = "Python web application using database"

text3 = "My favorite cricket match"


embedding1 = get_embedding(text1)
embedding2 = get_embedding(text2)
embedding3 = get_embedding(text3)


score12 = torch.dot(
    embedding1[0],
    embedding2[0]
).item()


score13 = torch.dot(
    embedding1[0],
    embedding3[0]
).item()


print("Text 1:", text1)
print("Text 2:", text2)
print("Text 3:", text3)

print()

print(
    "Similarity between Text 1 and Text 2:",
    round(score12, 4)
)

print(
    "Similarity between Text 1 and Text 3:",
    round(score13, 4)
)