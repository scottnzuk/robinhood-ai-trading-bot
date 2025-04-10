import uuid
import chromadb
from src.ai_trading_framework.modules.chroma_mcp import ChromaMCP

class TestChromaMCP(ChromaMCP):
    def __init__(self):
        # Hardcoded connection params matching MCP config
        self.host = "localhost"
        self.port = 8000
        self.collection_name = "roo-memory"
        # Initialize ChromaDB client directly
        self.client = chromadb.HttpClient(host=self.host, port=self.port)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

def main():
    # Initialize patched MCP without config file dependency
    mcp = TestChromaMCP()

    # Generate unique ID and dummy content
    test_id = str(uuid.uuid4())
    test_content = "This is a Roo MCP integration test."
    metadata = {"source": "roo_test"}

    # Store the dummy content
    try:
        mcp.store_memory(test_id, test_content, metadata)
        print(f"Stored test document with ID: {test_id}")
    except Exception as e:
        print(f"Error storing document: {e}")
        return

    # Query back the content
    try:
        results = mcp.query_memory("Roo MCP integration test", n_results=3)
        print("Query results:", results)
    except Exception as e:
        print(f"Error querying document: {e}")
        return

if __name__ == "__main__":
    main()