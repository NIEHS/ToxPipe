import logging
import sys
import os
from llama_index.logger import LlamaLogger
from llama_index import ServiceContext

# set up service context AMD llama logger
llama_logger = LlamaLogger()
service_context = ServiceContext.from_defaults(llama_logger=llama_logger)

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

query_engine = index.as_query_engine(
    service_context=service_context,
    similarity_top_k=2,
    # response_mode="tree_summarize"
)
response = query_engine.query(
    "What did Hawking do growing up?",
)

# get logs
print(service_context.llama_logger.get_logs())
import pprint
pp = pprint.PrettyPrinter(indent=4)

logs = service_context.llama_logger.get_logs()
pp.pprint(logs)

print("response: ", logs[1]["initial_response"])
