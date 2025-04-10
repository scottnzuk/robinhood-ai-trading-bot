import time
import threading
import random
from collections import defaultdict
import os
from cryptography.fernet import Fernet

class APIKey:
    def __init__(self, plaintext_key: str, fernet: Fernet):
        self.encrypted_key = fernet.encrypt(plaintext_key.encode())
        self.last_used = 0
        self.error_count = 0
        self.rate_limited_until = 0
        self.lock = threading.Lock()
        self._fernet = fernet

    def get_decrypted(self):
        return self._fernet.decrypt(self.encrypted_key).decode()

    def is_available(self):
        return time.time() > self.rate_limited_until

class ProviderRegistry:
    def __init__(self, master_key: bytes = None):
        # Setup encryption
        if master_key is None:
            key_env = os.getenv("API_KEYSAFE_MASTER_KEY")
            if key_env:
                master_key = key_env.encode()
            else:
                # Generate new key if not provided
                master_key = Fernet.generate_key()
                print(f"[WARNING] Generated new encryption key: {master_key.decode()}")
        self.fernet = Fernet(master_key)

        # provider_name -> list of APIKey objects
        self.providers = defaultdict(list)
        # provider priority order
        self.priority = []

    def add_provider(self, name: str, plaintext_keys: list[str], priority: int):
        self.providers[name] = [APIKey(k, self.fernet) for k in plaintext_keys]
        self.priority.append((priority, name))
        self.priority.sort()

    def mark_key_error(self, provider: str, key_obj: APIKey, rate_limited_seconds=0):
        with key_obj.lock:
            key_obj.error_count += 1
            if rate_limited_seconds > 0:
                key_obj.rate_limited_until = time.time() + rate_limited_seconds

    def get_next_key(self):
        # Iterate providers by priority
        for _, provider in sorted(self.priority):
            keys = self.providers.get(provider, [])
            # Shuffle keys for load balancing
            random.shuffle(keys)
            for key_obj in keys:
                if key_obj.is_available():
                    return provider, key_obj
        return None, None

    def reset_errors(self):
        for keys in self.providers.values():
            for key_obj in keys:
                key_obj.error_count = 0
                key_obj.rate_limited_until = 0

# Example usage:
if __name__ == "__main__":
    reg = ProviderRegistry()
    reg.add_provider("requestly", ["sk-req-1", "sk-req-2"], priority=1)
    reg.add_provider("deepseek", ["sk-ds-1"], priority=2)
    reg.add_provider("openrouter", ["sk-or-1"], priority=3)

    for _ in range(10):
        provider, key_obj = reg.get_next_key()
        if not key_obj:
            print("No available keys!")
            break
        print(f"Using key {key_obj.key} from {provider}")
        # Simulate error or rate limit
        if random.random() < 0.3:
            reg.mark_key_error(provider, key_obj, rate_limited_seconds=5)
        time.sleep(1)