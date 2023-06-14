from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
from llama_index import StorageContext, load_index_from_storage
import os

# set "OPENAI_API_KEY" environment variable IF not already set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'



documents = SimpleDirectoryReader('data').load_data()

# try to load index from storage
try:
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    # load index
    index = load_index_from_storage(storage_context)
# otherwise create index from documents
except:
    index = GPTVectorStoreIndex.from_documents(documents)

    index.storage_context.persist()



query_engine = index.as_query_engine()
response = query_engine.query("Who was mr hawking?")
print(response)

