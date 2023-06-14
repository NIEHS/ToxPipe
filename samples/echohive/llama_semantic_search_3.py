import logging
import sys
import os

# set "OPENAI_API_KEY" environment variable IF not already set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

# set logging to get more detailed output while running the code
logging.basicConfig(stream=sys.stdout, level=logging.INFO) # SET logging.INFO to logging.DEBUG for more detailed outputs
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

query_mode = "svm"
# query_mode = "linear_regression"
# query_mode = "logistic_regression"

# set Logging to DEBUG for more detailed outputs
query_engine = index.as_query_engine(
    vector_store_query_mode=query_mode
)
# need to modify utils.py to get this to work!!!!
response = query_engine.query(
    "What was hawking famous for?"
)

print("response: ", response)
print("Formatted Sources: ", response.get_formatted_sources())
print("SOURCE 1: ", response.source_nodes[0].source_text)
print("SOURCE 2: ",response.source_nodes[1].source_text)
