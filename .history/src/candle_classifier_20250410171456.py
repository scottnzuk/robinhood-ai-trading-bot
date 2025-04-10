import pandas as pd
import sys
sys.path.append("src")
from strategies import MovingAverageCrossStrategy, RSIStrategy
from my_transformers_extensions import AutoTokenizer, AutoModelForCausalLM
import torch

class CandleClassifier:
    def __init__(self, llm_model_name="mrzlab630/lora-alpaca-trading-candles", device="cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(llm_model_name)
        self.model = AutoModelForCausalLM.from_pretrained(llm_model_name).to(device)
        self.device = device

    def classify_llm(self, open_p, close_p, high_p, low_p):
        prompt = (
            "Instruction: identify candle\n"
            f"Input: open:{open_p},close:{close_p},high:{high_p},low:{low_p}\n"
            "Response:"
        )
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

    def detect_patterns(self, df: pd.DataFrame):
        return ohlcv.detect(df)

    def generate_signals(self, df: pd.DataFrame):
        strat = strategies.MovingAverageCrossStrategy(df)
        signals = strat.generate_signals()
        rsi_strat = strategies.RSIStrategy(df)
        rsi_signals = rsi_strat.generate_signals()
        combined = (signals['signal'] != 0) & (rsi_signals['signal'] != 0)
        df['combined_signal'] = combined.astype(int)
        return df[['combined_signal']]