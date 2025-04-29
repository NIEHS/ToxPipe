import os
from datetime import datetime as dt
from pathlib import Path
import requests 
import xmltodict
import traceback
from langchain.llms import BaseLLM
from langchain.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from time import time
from dotenv import load_dotenv
load_dotenv('../../../.config/.env')

N_PAPERS = 15


#### ADAPTED CODE FROM AMLAN'S PUBMED TOOL
def search_pubmed_article(query: str, max_results: int = 2) -> list:
    """Returns a list of pubmed reference and article content for a given query"""
    
    def searchLiterature(query):
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}'
        response = requests.get(url)
        if not response.ok: raise Exception(response.text)
        try:
            return xmltodict.parse(response.text)
        except:
            raise Exception(response.text)
    
    def doi2apa(doi):
        url = f'http://dx.doi.org/{doi}'
        response = requests.get(url, headers={'accept':'text/x-bibliography; style=apa'})
        if not response.ok: raise Exception(response.text)
        return response.text
    
    def getPubMedArticle(pmid):
        url = f'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmid}/unicode'
        response = requests.get(url)
        if not response.ok: raise Exception(response.text)
        try:
            return response.json()
        except:
            raise Exception(response.text)
        
    def getPubMedArticle1(pmid):
        url = f'https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson?pmids={pmid}&full=true'
        response = requests.get(url)
        if not response.ok: raise Exception(response.text)
        try:
            return response.json()
        except:
            raise Exception(response.text)
        
    try:
        res = searchLiterature(query)
        ids = res['eSearchResult']['IdList']
 
        if not ids: return {"ref": '', "content": ''}
        ids = ids['Id']
        if isinstance(ids, str): ids = [ids]
    except Exception as exp:
        print(f'In searchLiterature: {str(exp)}')
        return []
    
    res = []
    for pmid in ids:
        try:
            d = getPubMedArticle(pmid=pmid)
            passages = d[0]['documents'][0]['passages']
            doi = passages[0]['infons']['article-id_doi']
        except Exception as exp:
            print(f'In getPubMedArticle: {str(exp)}')
            continue
        try:
            ref = doi2apa(doi)
        except Exception as exp:
            print(f'In doi2apa({doi}, pmid: {pmid}): {str(exp)}')
            continue
        
        try:
            section_type, section_content = '', ''
            content = ''
            for item in passages[1:] + [{'infons': {'section_type': '', 'type': ''}, 'text': ''}]:
 
                if item['infons']['section_type'] in ['REF', 'METHODS', 'RESULTS'] : continue
                if section_type != item['infons']['section_type']:
                    if section_type != '' and section_content != '':
                        content += (('\n\n\n' if content != '' else '') + f'**{section_type}**\n\n{section_content}')
                section_type = item['infons']['section_type']
                section_content += f"\n*{item['text']}*\n" if 'title' in item['infons']['type'] else item['text']
        except Exception as exp:
            print(f'pmid: {pmid}, Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}')
            continue
 
        res.append({"ref": ref, "content": content[:10000]})
        if len(res) >= max_results: break
 
    return res


############################

def paper_scraper(search: str, pdir: str = "query") -> dict:
    try:
        res = search_pubmed_article(query=search, max_results=N_PAPERS)
        return res
    except Exception:
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


def scholar2result_llm(llm, query: str):
    """Useful to answer questions that require
    technical knowledge. Ask a specific question."""

    papers = paper_search(llm, query)
    if len(papers) == 0:
        return "Not enough papers found"
    answer=[f"The following are summaries of scientific literature that answer the prompt: '{query}':"]

    summary_prompt_template = """
        The following is the content of this academic paper: {ref}

        Please write a 1-2 paragraph summary of this work and how it answers the query: {query}

        The content is as follows:
        {content}
    """

    for p in papers:
        summary = ""
        try:
            summary_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
            summary_chain = summary_prompt | llm
            summary = summary_chain.invoke({"ref": p["ref"], "query": query, "content": p["content"]})
            summary = f"{summary.content} (source: {p['ref']})"

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

    def _run(self, query:str, **kwargs) -> str:
        return scholar2result_llm(self.llm, query)

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")
