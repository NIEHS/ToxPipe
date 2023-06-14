from llama_index import (GPTVectorStoreIndex,
                         GPTListIndex,
                         GPTTreeIndex,
                         GPTSimpleKeywordTableIndex,
                         SimpleDirectoryReader, 
                         load_index_from_storage, 
                         StorageContext,
                         LLMPredictor,
                         ServiceContext,
                        )
from llama_index.indices.composability import ComposableGraph

from langchain.chat_models import ChatOpenAI

import logging
import sys
import os
from pathlib import Path
import requests

# set logging to get more detailed output while running the code
logging.basicConfig(stream=sys.stdout, level=logging.INFO) # SET logging.INFO to logging.DEBUG for more detailed outputs
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'


# DON'T FORGET TO CHANGE THE SUMMARIES IF YOU CHNAGE THE GENRE OF INDEXES
wiki_titles = ["Nvidia", "AMD", "Intel", "Google", "Microsoft", "Apple", "Samsung", "Western Digital"]
# wiki_titles = ["Toronto", "Seattle", "Chicago", "Boston", "Houston"]
# wiki_titles = ["socrates", "rene descartes", "immanuel kant", "aristotle", "john locke", "david hume"]

# check the data directory to see if all the wiki titles are present. If not, download them

for title in wiki_titles:
    data_path = Path('data')
    if not data_path.exists():
        Path.mkdir(data_path)

    if not (data_path / f"{title}.txt").exists():
        
        print(f"Downloading {title} from Wikipedia")
        response = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'extracts',
                # 'exintro': True,
                'explaintext': True,
            }
        ).json()
        page = next(iter(response['query']['pages'].values()))
        wiki_text = page['extract']

        with open(data_path / f"{title}.txt", 'w', encoding="utf-8", errors="ignore") as fp:
            fp.write(wiki_text)

# Load all wiki documents
all_docs = SimpleDirectoryReader("data").load_data()

# # LLM Predictor (gpt-3.5-turbo)
llm_predictor_chatgpt = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"))
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor_chatgpt, chunk_size_limit=1024)

try:
    # Load indices from disk
    index_set = {}
    for name in wiki_titles:
        storage_context = StorageContext.from_defaults(persist_dir=f'./storage/{name}')
        cur_index = load_index_from_storage(storage_context=storage_context)
        index_set[name] = cur_index
except:
    # initialize simple vector indices + global vector index
    index_set = {}
    for i, name in enumerate(wiki_titles):
        # we create a temp doc becuase GPTVectorStoreIndex.from_documents wants an iterable object
        temp_doc = []
        temp_doc.append(all_docs[i])
        storage_context = StorageContext.from_defaults()
        cur_index = GPTVectorStoreIndex.from_documents(temp_doc)
        # cur_index = GPTTreeIndex.from_documents(temp_doc)
        # cur_index = GPTSimpleKeywordTableIndex.from_documents(temp_doc)
        index_set[name] = cur_index
        cur_index.storage_context.persist(persist_dir=f'./storage/{name}')

# create index summaries from the names. 
index_summaries = [f"this document is an article about the technology company '{name}' and gives details about the company." for name in wiki_titles]
print(index_summaries)

# define a list index over the vector indices
# allows us to synthesize information across each index
graph = ComposableGraph.from_indices(
    GPTListIndex,
    [index_set[name] for name in wiki_titles],
    index_summaries=index_summaries,
    service_context=service_context,
    storage_context=StorageContext.from_defaults(),
)
# root_id = graph.root_id

# [optional] save to disk
storage_context.persist(persist_dir=f'./storage/root')

custom_query_engines = {
    index.index_id: index.as_query_engine(
        child_branch_factor=2
    ) 
    for index in index_set.values()
}

query_engine = graph.as_query_engine(custom_query_engines=custom_query_engines)

# query the graph
while True:
    query = input("Enter query: ")
    if query == "exit":
        break
    response = query_engine.query(query)
    print(response)
    print(response.get_formatted_sources())
