# scripts/test_llm.py

from transformers import pipeline

qa = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
result = qa(question="What is the capital of France?", context="Paris is the capital of France.")
print(result)
