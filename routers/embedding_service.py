import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import os

client = QdrantClient(
    os.getenv("QDRANT_CLIENT", "http://localhost"),
    port=int(os.getenv("QDRANT_PORT", 6334)),
)
model = SentenceTransformer(os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"))
collection_name = os.getenv("QDRANT_COLLECTION_NAME", "Crail_data")


client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)


def flatten_doc(data):
    flat_text = []
    for key, value in data.items():
        formatted_key = key.replace("_", " ").capitalize()

        if isinstance(value, dict):
            nested = flatten_doc(value)
            flat_text.append(f"{formatted_key}: {nested}")
        elif isinstance(value, list):
            joined = ", ".join(str(v) for v in value)
            flat_text.append(f"{formatted_key}: {joined}")
        else:
            flat_text.append(f"{formatted_key}: {value}")
    return " | ".join(flat_text)


def generate_and_save_embeddings(user_id, data_list):
    points = []
    for data in data_list:
        doc_id = str(uuid.uuid4())
        flattened = flatten_doc(data)

        embedding = model.encode(flattened).tolist()

        point = PointStruct(
            id=doc_id,
            vector=embedding,
            payload={
                "user_id": user_id,
                "data": flattened,
            },
        )
        points.append(point)

    client.upsert(collection_name=collection_name, points=points)


# with open("E:\Crail 2025\doctors.json", "r", encoding="utf-8") as file:
#     doctor_list = json.load(file)


def generate_document_embeddings(user_id, file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # doctor_list = json.load(file)
            input_doc = json.load(file)
            generate_and_save_embeddings(user_id, input_doc)
        return True
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return False
