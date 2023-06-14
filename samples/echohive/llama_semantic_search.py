from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
import os

# set "OPENAI_API_KEY" environment variable IF not already set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

documents = SimpleDirectoryReader('data').load_data()

index = GPTVectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()

response = query_engine.query("What did the Hawking do growing up?")

print(response)