import torch
from peft import PeftModel
from transformers import LlamaTokenizer, LlamaForCausalLM, AutoTokenizer, AutoModelForSeq2SeqLM

class CandleLLMs:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

        # LLaMA-LoRA model
        base_model = "/Users/byteme/lora-alpaca-trading-candles/weights_Llama_7b"
        lora_weights = "/Users/byteme/lora-alpaca-trading-candles/lora-alpaca-trading-candles"
        self.llama_tokenizer = LlamaTokenizer.from_pretrained(base_model, local_files_only=True)
        llama = LlamaForCausalLM.from_pretrained(base_model, device_map={"": self.device}, torch_dtype=torch.float16, local_files_only=True)
        self.llama_model = PeftModel.from_pretrained(llama, lora_weights, device_map={"": self.device}, torch_dtype=torch.float16, local_files_only=True)
        self.llama_model.eval()

        # Flan-T5 model
        t5_path = "/Users/byteme/flan-t5-base-trading_candles"
        self.t5_tokenizer = AutoTokenizer.from_pretrained(t5_path, local_files_only=True)
        self.t5_model = AutoModelForSeq2SeqLM.from_pretrained(t5_path, local_files_only=True).to(self.device)
        self.t5_model.eval()

    def llama_classify(self, instruction, input_text):
        prompt = f"Instruction: {instruction}\nInput: {input_text}\nResponse:"
        inputs = self.llama_tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.llama_model.generate(**inputs, max_new_tokens=50, temperature=0.1, top_p=0.75, top_k=40, num_beams=4)
        response = self.llama_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("Response:")[-1].strip()

    def t5_classify(self, prompt):
        inputs = self.t5_tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.t5_model.generate(**inputs, max_new_tokens=50, temperature=0.1, top_p=0.75, top_k=40, num_beams=4)
        response = self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.strip()