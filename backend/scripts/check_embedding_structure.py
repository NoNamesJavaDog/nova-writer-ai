#!/usr/bin/env python
"""检查 ContentEmbedding 对象结构"""
from google import genai
from config import GEMINI_API_KEY
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)
result = client.models.embed_content(
    model="models/text-embedding-004",
    contents=["test text"],
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
)

emb = result.embeddings[0]
print("ContentEmbedding attributes:", [x for x in dir(emb) if not x.startswith("_")])

# 尝试访问可能的属性
if hasattr(emb, 'values'):
    print("Found 'values' attribute")
    print(f"Values type: {type(emb.values)}")
    print(f"Values length: {len(emb.values) if hasattr(emb.values, '__len__') else 'N/A'}")
    print(f"First 5 values: {emb.values[:5] if hasattr(emb.values, '__getitem__') else 'N/A'}")
elif hasattr(emb, 'embedding'):
    print("Found 'embedding' attribute")
    print(f"Embedding type: {type(emb.embedding)}")
    print(f"Embedding length: {len(emb.embedding) if hasattr(emb.embedding, '__len__') else 'N/A'}")
else:
    print("Trying to convert to dict...")
    if hasattr(emb, 'dict'):
        emb_dict = emb.dict()
        print(f"Dict keys: {emb_dict.keys() if isinstance(emb_dict, dict) else 'N/A'}")

