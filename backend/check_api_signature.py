#!/usr/bin/env python
"""检查 embed_content API 签名"""
from google import genai
from config import GEMINI_API_KEY
import inspect

client = genai.Client(api_key=GEMINI_API_KEY)
sig = inspect.signature(client.models.embed_content)
print("embed_content 签名:")
print(sig)
print("\n参数详情:")
for param_name, param in sig.parameters.items():
    print(f"  {param_name}: {param.annotation} = {param.default}")

