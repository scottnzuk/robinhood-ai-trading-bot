from my_transformers_extensions import AutoTokenizer, AutoModelForQuestionAnswering
import torch

class CandleQA:
    def __init__(self, model_name="mrzlab630/lora-alpaca-trading-candles", device="cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForQuestionAnswering.from_pretrained(model_name).to(device)
        self.device = device

    def classify(self, question, context):
        inputs = self.tokenizer(question, context, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            answer_start = torch.argmax(outputs.start_logits)
            answer_end = torch.argmax(outputs.end_logits) + 1
            answer = self.tokenizer.convert_tokens_to_string(
                self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end])
            )
        return answer