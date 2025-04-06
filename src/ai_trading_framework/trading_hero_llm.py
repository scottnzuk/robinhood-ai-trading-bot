"""
Trading-Hero-LLM Integration Module
----------------------------------

This module provides functions to load the Trading-Hero-LLM financial sentiment analysis model,
preprocess input text, and predict sentiment labels.

Usage:
    pip install transformers torch

"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Dynamically select device: MPS if available, else CPU
if torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("fuchenru/Trading-Hero-LLM")
model = AutoModelForSequenceClassification.from_pretrained("fuchenru/Trading-Hero-LLM")
model.to(device)

# Optional: pipeline interface
nlp_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

def preprocess(text, max_length=128):
    """
    Tokenize and preprocess input text.

    Args:
        text (str): Input text.
        max_length (int): Max sequence length.

    Returns:
        dict: Tokenized inputs as PyTorch tensors.
    """
    return tokenizer(text, truncation=True, padding='max_length', max_length=max_length, return_tensors='pt')

def predict_sentiment(input_text):
    """
    Predict sentiment label for the input text.

    Args:
        input_text (str): The input sentence or paragraph.

    Returns:
        str: Predicted sentiment ('neutral', 'positive', 'negative').
    """
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True)
    # Move inputs to CPU explicitly
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    predicted_label = torch.argmax(outputs.logits, dim=1).item()
    label_map = {0: 'neutral', 1: 'positive', 2: 'negative'}
    return label_map[predicted_label]

if __name__ == "__main__":
    # Sample usage
    stock_news = [
        "Market analysts predict a stable outlook for the coming weeks.",
        "The market remained relatively flat today, with minimal movement in stock prices.",
        "Investor sentiment improved following news of a potential trade deal.",
        "The company reported a significant loss in the last quarter."
    ]
    for news in stock_news:
        sentiment = predict_sentiment(news)
        print(f"News: {news}\nPredicted Sentiment: {sentiment}\n")