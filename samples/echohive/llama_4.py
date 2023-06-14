from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, GPTListIndex
from llama_index import StorageContext, load_index_from_storage
from llama_index.node_parser import SimpleNodeParser
import os

# set "OPENAI_API_KEY" environment variable IF not already set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

documents = SimpleDirectoryReader('data').load_data()
documents_2 = SimpleDirectoryReader('data_2').load_data()

try:
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    # load index
    index = load_index_from_storage(storage_context)
except:

    index = GPTVectorStoreIndex([])

    for doc in documents:        
        index.insert(doc)
    
    for doc in documents_2:
        index.insert(doc)

    index.storage_context.persist()



query_engine = index.as_query_engine()
while True:
    response = query_engine.query(input("Enter query: "))
    print(response)

