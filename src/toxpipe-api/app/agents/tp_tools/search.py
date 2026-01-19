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
from dotenv import dotenv_values

DIR_HOME = Path(__file__).parent.parent.parent.parent
env_config = dotenv_values(DIR_HOME / ".config" / "example.env")
if os.path.exists(DIR_HOME / ".config" / ".env"):
    env_config = dotenv_values(DIR_HOME / ".config" / ".env")

N_PAPERS = env_config["TOXPIPE_MAX_PAPERS"]
try:
    N_PAPERS = int(N_PAPERS)
except Exception as e:
    N_PAPERS = 10

PAPER_CONTENT_SIZE = env_config["TOXPIPE_PAPER_CONTENT_MAX_SIZE"]

try:
    PAPER_CONTENT_SIZE = int(PAPER_CONTENT_SIZE)
except Exception as e:
    PAPER_CONTENT_SIZE = 10000

PUBMED_API_KEY = env_config["TOXPIPE_PUBMED_API_KEY"]

#### ADAPTED CODE FROM AMLAN'S PUBMED TOOL
def search_pubmed_article(query: str, 
                          max_results: int = 10, 
                          content_size: int|None=None,
                          api_key: str='') -> list:
    """Returns a list of pubmed reference and article content for a given query"""
    
    def getPubMedArticleEutils(pmcid):
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}&rettype=full&api_key={api_key}'
        response = requests.get(url)
        if not response.ok: raise Exception(response.text)
        try:
            return xmltodict.parse(response.text)
        except:
            raise Exception(response.text)
        
    def getArticleEutils(pmcid):

        def parseText(d_xml, text = []):
            
            text = text.copy()
            
            if isinstance(d_xml, dict):
                for k in d_xml:
                    if k not in ['title', 'sec', 'p', '#text']: continue
                    text = parseText(d_xml[k], text=text)
            elif isinstance(d_xml, list):
                for k in d_xml:
                    text = parseText(k, text=text)
            else:
                if d_xml: text.append(d_xml)

            return text
        
        def parseTextField(val):
            if isinstance(val, dict):
                return val.get('#text', '')
            return val

        def extractAuthors(contrib):
            if 'collab' in contrib:
                return {'first_name': '', 
                        'last_name': parseTextField(contrib['collab']).strip()}
            else:
                return {'first_name': contrib['name']['given-names']['#text'].strip(), 
                        'last_name': contrib['name']['surname'].strip()}

        try:
            d = getPubMedArticleEutils(pmcid=pmcid)
        except Exception as exp:
            raise Exception(f'In getPubMedArticleEutils(pmcid={pmcid}), Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}')
            
        assert 'front' in d['pmc-articleset']['article'], 'Reference not available'
        assert 'body' in d['pmc-articleset']['article'], 'Content not available'
        
        ref = {'pmcid': pmcid}

        front = d['pmc-articleset']['article']['front']

        ref['journal'] = parseTextField(front['journal-meta']['journal-title-group']['journal-title'])
        
        for article_id in front['article-meta']['article-id']:
            ref[article_id['@pub-id-type']] = article_id['#text'].strip()
            
        assert 'doi' in ref, 'DOI not found'

        ref['title'] = parseTextField(front['article-meta']['title-group']['article-title'])
    
        authors = []            

        contrib_group = front['article-meta'].get('contrib-group')
        
        if isinstance(contrib_group, list):
            for contrib_group_element in contrib_group:
                if isinstance(contrib_group_element['contrib'], list):
                    for contrib in contrib_group_element['contrib']:
                        if contrib['@contrib-type'] == 'author':
                            authors.append(extractAuthors(contrib))
                else:
                    contrib = contrib_group_element['contrib']
                    if contrib['@contrib-type'] == 'author':
                            authors.append(extractAuthors(contrib))
        elif isinstance(contrib_group, dict):
            if isinstance(contrib_group['contrib'], list):
                for contrib in contrib_group['contrib']:
                    if contrib['@contrib-type'] == 'author':
                        authors.append(extractAuthors(contrib))
            elif isinstance(contrib_group['contrib'], dict):
                contrib = contrib_group['contrib']
                if contrib['@contrib-type'] == 'author':
                    authors.append(extractAuthors(contrib))
            

        ref['authors'] = authors

        if isinstance(front['article-meta']['pub-date'], list):
            for pub_date in front['article-meta']['pub-date']:
                ref['year'] = pub_date['year']
                break
        else:
            ref['year'] = front['article-meta']['pub-date']['year']

        ref['year'] = parseTextField(ref['year'])
        ref['volume'] = parseTextField(front['article-meta'].get('volume', ''))
        ref['issue'] = parseTextField(front['article-meta'].get('issue', ''))
        
        if 'elocation-id' in front['article-meta']:
            ref['pages'] = front['article-meta']['elocation-id']
        else:
            ref['pages'] = f"{front['article-meta']['fpage']}-{front['article-meta']['lpage']}"

        ref['pages'] = parseTextField(ref['pages'])

        abstract = front['article-meta'].get('abstract', [])
        body = d['pmc-articleset']['article']['body']
        
        abstract = ' '.join(parseText(abstract))
        body = ' '.join(parseText(body))
        
        return ref, abstract, body
    
    def searchLiterature(query, retstart=1, retmax=5):
        qstring = f'db=pmc&term={query}&sort=relevance&retstart={retstart}&retmax={retmax}&api_key={api_key}'
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{qstring}'
        response = requests.get(url)
        if not response.ok: raise Exception(response.text)
        try:
            return xmltodict.parse(response.text)
        except:
            raise Exception(response.text)

    try:
        res = searchLiterature(query)
        ids = res['eSearchResult']['IdList']

        if not ids: return []
        ids = ids['Id']
        if isinstance(ids, str): ids = [ids]
    except Exception as exp:
        print(f'In searchLiterature("{query}"): {str(exp)}')
        return []
    
    res = []
    for id in ids:
        try:
            ref, abstract, body = getArticleEutils(pmcid=id)
        except Exception as exp:
            print(f'In getArticleEutils(pmcid={id}):, Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}')
            continue
        
        if content_size is not None: body = body[:content_size]
        
        res.append({"ref": ref, "abstract": abstract, "body": body})

        if len(res) >= max_results: break

    return res


############################

def paper_scraper(search: str, pdir: str = "query") -> dict:
    try:
        res = search_pubmed_article(query=search, max_results=N_PAPERS, content_size=PAPER_CONTENT_SIZE, api_key=PUBMED_API_KEY)
        return res
    except Exception as e:
        print(e)
        print( traceback.print_exc())
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
        #return "Not enough papers found"
        return ""
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
            summary = summary_chain.invoke({"ref": p["ref"], "query": query, "content": p["body"]})
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
        search_response = scholar2result_llm(self.llm, query)
        return search_response

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")
