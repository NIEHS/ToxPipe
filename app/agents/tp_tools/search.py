import os
from datetime import datetime as dt
from pathlib import Path
import multiprocessing
import langchain
import requests 

import paperscraper
from paperscraper.pubmed import get_and_dump_pubmed_papers
from paperscraper.arxiv import get_and_dump_arxiv_papers
from paperscraper.pdf import save_pdf
from paperscraper.xrxiv.xrxiv_query import XRXivQuery

from langchain.base_language import BaseLanguageModel
from langchain.llms import BaseLLM
from langchain.tools import BaseTool
from langchain_community.document_loaders import PyPDFLoader
from pypdf.errors import PdfReadError
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import USearch
from langchain.chains import RetrievalQA
from typing import List
from toolz import compose
from itertools import chain as ichain
from itertools import islice
from operator import methodcaller as mc

from time import time
import uuid

import pandas as pd
from glob import glob

from dotenv import load_dotenv
load_dotenv('../../.env')

N_PAPERS = 15

# Fetch rxiv dumps
from paperscraper.get_dumps import biorxiv, medrxiv, chemrxiv
#medrxiv()  #  Takes ~30min and should result in ~35 MB file
#biorxiv()  # Takes ~1h and should result in ~350 MB file
#chemrxiv()  #  Takes ~45min and should result in ~20 MB file
from paperscraper.pdf import save_pdf_from_dump

# Biopython entrez functionality
#from Bio import Entrez

def search_papers(search, limit, pdir, semantic_scholar_api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY")):
    try:
        res = requests.get(
            f"http://api.semanticscholar.org/graph/v1/paper/search?query={search}&limit={limit}",
            headers={'x-api-key': semantic_scholar_api_key}
        )
        res = res.json()

        print("===RES===")
        print(res)
        exit()

    except Exception:
        return {}

def paper_scraper(search: str, pdir: str = "query") -> dict:
    try:
        #return paperscraper.search_papers(search, limit=N_PAPERS, pdir=pdir, batch_size=4, semantic_scholar_api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY"))
        #return search_papers(search, limit=N_PAPERS, pdir=pdir, semantic_scholar_api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY"))
        
        print("!!! SCRAPING !!!")

        query = [[search]]
        uid = uuid.uuid4()
        if os.path.isdir(os.environ.get('PAPERSCRAPER_DIR')) == False:
            os.mkdir(os.environ.get('PAPERSCRAPER_DIR'))
        outpath = f"{os.environ.get('PAPERSCRAPER_DIR')}/pubmed_scraped_{uid}.jsonl"
        paperpath = f"{os.environ.get('PAPERSCRAPER_DIR')}/{uid}/"
        if os.path.isdir(paperpath) == False:
            os.mkdir(paperpath)
        get_and_dump_pubmed_papers(query, output_filepath=outpath, start_date="2014/01/01")
        #get_and_dump_pubmed_papers(query, output_filepath=outpath)

        #get_and_dump_arxiv_papers(query, output_filepath=outpath)

        #querier = XRXivQuery(f"{os.environ.get('PAPERSCRAPER_DUMP_DIR')}/biorxiv_2024-10-24.jsonl")
        #querier = XRXivQuery(f"{os.environ.get('PAPERSCRAPER_DUMP_DIR')}/chemrxiv_2024-10-24.jsonl")
        #querier.search_keywords(query, output_filepath=outpath)
        
        # Grab PDFs of fetched papers
        paper_df = pd.read_json(path_or_buf=outpath, lines=True)

        doi_list = []
        path_list = []

        for index, row in paper_df.head(100).iterrows():
            try:
                doi = str(row['doi'])
                doi = doi.splitlines()[0]
                row['doi'] = doi
                if doi:
                    fpath = f"{paperpath}/{doi.replace('/', '_')}.pdf"
                    save_pdf(row.to_dict(), fpath)
                    if os.path.isfile(fpath):
                        doi_list.append(doi)
                        path_list.append(fpath)
                    else:
                        txtfpath = f"{paperpath}/{doi.replace('/', '_')}.txt"
                        abstract = str(row['abstract'])
                        txtf = open(txtfpath, 'w', encoding='utf-8')
                        txtf.write(abstract)
                        txtf.close()
            except:
                print("Error parsing document")

                
        papers = pd.DataFrame({'doi': doi_list, 'path': path_list})

        return papers

    except KeyError:
        return {}


def paper_search(llm, query: str):
    if not os.path.isdir("./query"):
        os.mkdir("query/")
    search = query

    search_id = round(dt.timestamp(dt.now()))
    search_name = search.strip()
    for char in [' ', '"', '.']:
        search_name=search_name.replace(char, '')

    ts = time()
    papers = paper_scraper(search, pdir=str(Path("query") / f'{search_id}_{search_name}')) # bottleneck

    return papers


def retrieve_summary(llm, embeddings, query: str, paths: List[str]):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0, separators=["\n\n", "\n", " "])
    vectorize = compose(text_splitter.split_documents, mc("load"), PyPDFLoader)

    #docs = list(ichain.from_iterable(map(vectorize, paths)))[:5] # very slow - will need to do a single time for each document?
    #docs = list(ichain.from_iterable(map(vectorize, paths[:5]))) # just do first 5 papers?  # bottleneck - converting to list is slow
    ts = time()

    docs = [x for x in islice(ichain.from_iterable(map(vectorize, paths[:N_PAPERS])), N_PAPERS)]


    db = USearch.from_documents(docs, embeddings)
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=db.as_retriever())
    summary = chain.invoke(query)

    #summary_prompt_template = """
    #    Previously, {n_agents} separate LLM agents were run to answer the following prompt from an end user:
    #    {prompt}

    #    The following are the raw results from each agent:

    #    {res}

    #    Using these responses, reformat the responses into a single response to be returned to the end user.
    #    IMPORTANT: you MUST follow the following steps when formulating your final response:
    #        1. This summary should contain the most relevant information from the raw results that answers the original prompt. Try to only include information that is relevant to the original prompt and avoid including any irrelevant information.
        #"""
        #summary_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
        #summary_chain = summary_prompt | self.llm
        #summary = summary_chain.invoke({"n_agents": n_agents, "prompt": prompt, "res": res})

        #return summary.content

    return summary


def scholar2result_llm(llm, query: str):
    """Useful to answer questions that require
    technical knowledge. Ask a specific question."""

    papers = paper_search(llm, query)
    if len(papers) == 0:
        return "Not enough papers found"
    path_papers = []
    answer=['According to the following references:']

    for index, row in papers.iterrows():
            path_papers.append(row["path"])
            answer.append(f'Citation:{row["doi"]} \n Path: {row["path"]} \n')

    print(f"\nFound {len(path_papers)} papers")
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/paraphrase-MiniLM-L6-v2')
    summary = ""
    try:
        summary = retrieve_summary(llm, embeddings, query, path_papers)
    except:
        print("Problem generating summary")
    answer.append(f'Summary: {summary}')

    return "\n".join(answer)


class Scholar2ResultLLM(BaseTool):
    name: str = "LiteratureSearch"
    description: str = "Perform a comprehensive literature search to answer a specific question that requires a detailed, technical answer. Produces a summary of the search results including the most relevant papers and a summary of the information found alongside a source given as a DOI, URL, or PMID for each."    
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, query) -> str:
        return scholar2result_llm(self.llm, query)

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")
