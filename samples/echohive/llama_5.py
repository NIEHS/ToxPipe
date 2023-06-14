from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, LLMPredictor, PromptHelper, ServiceContext
from llama_index import StorageContext, load_index_from_storage
from llama_index.node_parser import SimpleNodeParser
from langchain import OpenAI
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

    # define LLM
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003"))

    # define prompt helper
    # set maximum input size
    max_input_size = 4096
    # set number of output tokens
    num_output = 256
    # set maximum chunk overlap. Couldn't see if this really works
    max_chunk_overlap = 20

    prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)

    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)

    index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)

    index.storage_context.persist()



query_engine = index.as_query_engine()
response = query_engine.query("who was the mathematician?")
print(response)

