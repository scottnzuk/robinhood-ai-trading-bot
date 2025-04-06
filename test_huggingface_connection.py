"""
Minimal Hugging Face Hub connectivity test for Ultralytics environment.

This script verifies that the environment can successfully connect to Hugging Face Hub
and download a model using the `transformers` library.

Usage:
    python test_huggingface_connection.py
"""

from transformers import AutoModel, AutoTokenizer

def test_hf_download():
    model_name = "bert-base-uncased"
    print(f"Attempting to download model '{model_name}' from Hugging Face Hub...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        print("Successfully downloaded model and tokenizer.")
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False

if __name__ == "__main__":
    success = test_hf_download()
    if success:
        print("Hugging Face Hub connection test PASSED.")
    else:
        print("Hugging Face Hub connection test FAILED.")