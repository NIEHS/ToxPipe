import logging
import sys
import os

# set "OPENAI_API_KEY" environment variable IF not already set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

# set logging to get more detailed output while running the code
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG) # SET logging.INFO to logging.DEBUG for more detailed outputs
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, load_index_from_storage, StorageContext


try:
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir='storage')
    # load index
    index = load_index_from_storage(storage_context, index_id="Hawking")
except:
    
    # load documents
    documents = SimpleDirectoryReader('data').load_data()

    index = GPTVectorStoreIndex.from_documents(documents)

    # save index to disk
    index.set_index_id("Hawking")
    index.storage_context.persist('storage')

# set Logging to DEBUG for more detailed outputs
query_engine = index.as_query_engine()
response = query_engine.query("What is Hawking famous for?")

print(response)