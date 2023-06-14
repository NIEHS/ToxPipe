from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, GPTListIndex
from llama_index import StorageContext, load_index_from_storage
from llama_index.node_parser import SimpleNodeParser
import os

# set "OPENAI_API_KEY" environment variable IF not already set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

documents = SimpleDirectoryReader('data').load_data()


try:
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    # load index
    index = load_index_from_storage(storage_context)
except:
    parser = SimpleNodeParser()

    nodes = parser.get_nodes_from_documents(documents)

    storage_context = StorageContext.from_defaults()
    storage_context.docstore.add_documents(nodes)

    # create vectorstore index
    index1 = GPTVectorStoreIndex(nodes, storage_context=storage_context, name="index1")
    # create list index
    index2 = GPTListIndex(nodes, storage_context=storage_context, name="index2")

    index1.storage_context.persist()
    index2.storage_context.persist()
    



query_engine = index.as_query_engine()
response = query_engine.query("What did the author do growing up?")
print(response)

