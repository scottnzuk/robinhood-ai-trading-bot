from transformers import LlamaTokenizer, LlamaForCausalLM
import torch

class CandleGen:
    def __init__(self, device="cpu"):
        vocab_file = "/Users/byteme/lora-alpaca-trading-candles/tokenizer.model"
        self.tokenizer = LlamaTokenizer(vocab_file=vocab_file)
        base_model = "/Users/byteme/lora-alpaca-trading-candles"
        self.model = LlamaForCausalLM.from_pretrained(base_model, local_files_only=True, trust_remote_code=True).to(device)
        self.device = device
        self.model.eval()

    def classify(self, instruction, input_text):
        prompt = f"Instruction: {instruction}\nInput: {input_text}\nResponse:"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                top_p=0.75,
                top_k=40,
                num_beams=4
            )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("Response:")[-1].strip()