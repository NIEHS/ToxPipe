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

N_PAPERS = os.environ.get("TOXPIPE_MAX_PAPERS")
PAPER_CONTENT_SIZE = os.environ.get("TOXPIPE_PAPER_CONTENT_MAX_SIZE")

#### ADAPTED CODE FROM AMLAN'S PUBMED TOOL
def search_pubmed_article(query: str, 
                          max_results: int = 10, 
                          content_size: int|None=None,
                          api_key: str='') -> list:
    """Returns a list of pubmed reference and article content for a given query"""
    
    # def doi2apa(doi):
    #     url = f'http://dx.doi.org/{doi}'
    #     response = requests.get(url, headers={'accept':'text/x-bibliography; style=apa'})
    #     if not response.ok: raise Exception(response.text)
    #     return response.text.strip()
        
    # def getPubMedArticle(pmcid):

    #     url = f'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/PMC{pmcid}/unicode'
    #     response = requests.get(url)
    #     if not response.ok: raise Exception(response.text)
    #     try:
    #         return response.json()
    #     except:
    #         raise Exception(response.text)
        
    # def getPubMedArticlePubtator(pmid):
    #     url = f'https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson?pmids={pmid}&full=true'
    #     response = requests.get(url)
    #     if not response.ok: raise Exception(response.text)
    #     try:
    #         return response.json()
    #     except:
    #         raise Exception(response.text)
        
    # def getArticleBioC(pmcid):

    #     exclude_sections: list=['REF', 'METHODS', 'RESULTS']

    #     d = getPubMedArticle(pmcid=pmcid)
    #     passages = d[0]['documents'][0]['passages']
    #     doi = passages[0]['infons']['article-id_doi']

    #     # d = getPubMedArticlePubtator(pmid=pmid)
    #     # passages = d['PubTator3'][0]['passages']
    #     # if 'journal' in passages[0]['infons']:
    #     #     doi = passages[0]['infons']['journal'].split('doi:')[-1].split('. ')[0].strip()
    #     # elif 'article-id_doi' in passages[0]['infons']:
    #     #     doi = passages[0]['infons']['article-id_doi']
    #     # else:
    #     #     raise Exception('DOI could not be found')

    #     ref = doi2apa(doi)

    #     section_type, section_content = '', ''
    #     content = '' 
    #     for item in passages[1:] + [{'infons': {'section_type': '', 'type': ''}, 'text': ''}]:

    #         if item['infons']['section_type'] in exclude_sections : continue
    #         if section_type != item['infons']['section_type']:
    #             if section_type != '' and section_content != '':
    #                 content += (('\n\n\n' if content != '' else '') + f'**{section_type}**\n\n{section_content}')
    #         section_type = item['infons']['section_type']
    #         section_content += f'\n*{item['text']}*\n' if 'title' in item['infons']['type'] else item['text']

    #     return ref, content
    
    
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
            if isinstance(d_xml, dict):
                for k in d_xml:
                    text = parseText(d_xml[k], text=text)
            elif isinstance(d_xml, list):
                for k in d_xml:
                    text = parseText(k, text=text)
            else:
                if d_xml: text.append(d_xml)

            return text

        try:
            d = getPubMedArticleEutils(pmcid=pmcid)
        except Exception as exp:
            raise Exception(f'In getPubMedArticleEutils({pmcid}), Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}')
            
        assert 'front' in d['pmc-articleset']['article'], 'Reference not available'
        assert 'body' in d['pmc-articleset']['article'], 'Content not available'
        
        ref = {'pmcid': pmcid}

        front = d['pmc-articleset']['article']['front']

        ref['journal'] = front['journal-meta']['journal-title-group']['journal-title']

        for article_id in front['article-meta']['article-id']:
            ref[article_id['@pub-id-type']] = article_id['#text'].strip()
            
        assert 'doi' in ref, 'DOI not found'

        ref['title'] = front['article-meta']['title-group']['article-title']
        if isinstance(ref['title'], dict):
            ref['title'] = ref['title']['#text']

        authors = []
        contrib_group = front['article-meta']['contrib-group']
        if isinstance(contrib_group, list):
            for contrib_group_element in contrib_group:
                if isinstance(contrib_group_element['contrib'], list):
                    for contrib in contrib_group_element['contrib']:
                        if contrib['@contrib-type'] == 'author':
                            authors.append({'first_name': contrib['name']['given-names']['#text'].strip(), 
                                            'last_name': contrib['name']['surname'].strip()})
        elif isinstance(contrib_group['contrib'], list):
            for contrib in contrib_group['contrib']:
                if contrib['@contrib-type'] == 'author':
                    authors.append({'first_name': contrib['name']['given-names']['#text'].strip(), 
                                    'last_name': contrib['name']['surname'].strip()})
        else:
            if contrib_group['contrib']['@contrib-type'] == 'author':
                if 'collab' in contrib_group['contrib']:
                    authors.append({'first_name': '', 
                                    'last_name': contrib_group['contrib']['collab'].strip()})

        ref['authors'] = authors

        if isinstance(front['article-meta']['pub-date'], list):
            for pub_date in front['article-meta']['pub-date']:
                ref['year'] = pub_date['year']
                break
        else:
            ref['year'] = front['article-meta']['pub-date']['year']

        ref['volume'] = front['article-meta']['volume']
        issue = front['article-meta'].get('issue', '1')
        if isinstance(issue, str):
            ref['issue'] = issue
        else:
            ref['issue'] = issue['#text']
        if 'elocation-id' in front['article-meta']:
            ref['pages'] = front['article-meta']['elocation-id']
        else:
            ref['pages'] = f"{front['article-meta']['fpage']}-{front['article-meta']['lpage']}"

        body = d['pmc-articleset']['article']['body']
        
        content = ' '.join(parseText(body))
        
        return ref, content
    
    def searchLiterature(query, retstart=1, retmax=5):
        qstring = f'db=pmc&term={query}&sort=relevance&retstart={retstart}&retmax={retmax}&api_key={api_key}'
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{qstring}'
        response = requests.get(url)
        if not response.ok: raise Exception(response.text)
        try:
            return xmltodict.parse(response.text)
        except:
            raise Exception(response.text)

    print(query)

    try:
        res = searchLiterature(query)
        ids = res['eSearchResult']['IdList']

        if not ids: return {"ref": '', "content": ''}
        ids = ids['Id']
        if isinstance(ids, str): ids = [ids]
    except Exception as exp:
        print(f'In searchLiterature("{query}"): {str(exp)}')
        return []
    
    res = []
    for id in ids:
        try:
            ref, content = getArticleEutils(pmcid=id)
        except Exception as exp:
            print(f'pmcid: {id}, Line number: {exp.__traceback__.tb_lineno}, Description: {exp}\n\n{traceback.format_exc()}')
            continue

        if content_size is not None: content = content[:content_size]
        
        res.append({"ref": ref, "content": content})

        if len(res) >= max_results: break

    return res


############################

def paper_scraper(search: str, pdir: str = "query") -> dict:
    try:
        res = search_pubmed_article(query=search, max_results=N_PAPERS, content_size=PAPER_CONTENT_SIZE)
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
