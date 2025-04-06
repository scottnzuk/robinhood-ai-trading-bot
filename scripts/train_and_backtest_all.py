import os
import pandas as pd
from multiprocessing import Pool, cpu_count

def process_symbol(symbol_file):
    try:
        df = pd.read_csv(symbol_file)
        symbol = os.path.basename(symbol_file).replace('_1d_enriched.csv', '')
        print(f"Processing {symbol}...")

        # Feature extraction (assumed done)
        # Label: next day return
        df['future_return'] = df['close'].shift(-1) / df['close'] - 1

        # Simple regime label
        df['regime'] = 'sideways'
        df.loc[df['future_return'] > 0.01, 'regime'] = 'bull'
        df.loc[df['future_return'] < -0.01, 'regime'] = 'bear'

        # Placeholder: train simple model (e.g., mean future return by regime)
        mean_returns = df.groupby('regime')['future_return'].mean().to_dict()

        # Save stats
        out_path = symbol_file.replace('_enriched.csv', '_stats.txt')
        with open(out_path, 'w') as f:
            f.write(f"Symbol: {symbol}\n")
            f.write(f"Mean future returns by regime:\n")
            for k, v in mean_returns.items():
                f.write(f"{k}: {v:.5f}\n")

        print(f"Saved stats for {symbol}")
    except Exception as e:
        print(f"Error processing {symbol_file}: {e}")

def main():
    data_dir = "data/crypto"
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('_1d_enriched.csv')]
    print(f"Found {len(files)} enriched datasets.")

    with Pool(cpu_count()) as pool:
        pool.map(process_symbol, files)

if __name__ == "__main__":
    main()