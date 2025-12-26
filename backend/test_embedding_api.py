#!/usr/bin/env python
"""测试 embed_content API 返回值结构"""
from google import genai
from config import GEMINI_API_KEY
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)
result = client.models.embed_content(
    model="models/text-embedding-004",
    contents=["test text"],
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
)

print("Result type:", type(result))
print("Result attributes:", [x for x in dir(result) if not x.startswith("_")])

# 尝试提取向量
if hasattr(result, 'embedding'):
    print("Found 'embedding' attribute")
    embedding = result.embedding
    print(f"Embedding type: {type(embedding)}")
    if isinstance(embedding, list):
        print(f"Embedding length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
elif hasattr(result, 'embeddings'):
    print("Found 'embeddings' attribute")
    embeddings = result.embeddings
    print(f"Embeddings type: {type(embeddings)}")
    if isinstance(embeddings, list) and len(embeddings) > 0:
        print(f"First embedding length: {len(embeddings[0])}")
elif hasattr(result, 'values'):
    print("Found 'values' attribute")
    values = result.values
    print(f"Values type: {type(values)}")
else:
    print("Result object:", result)

