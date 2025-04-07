import os
import re
import pandas as pd
import requests
import urllib.parse
from langchain.tools import BaseTool
from langchain.llms import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from random import sample
load_dotenv('../../../.config/.env')
from ...rag import query

def query_rag(q: str, llm: BaseLLM, use_training_data: bool, relevancy_check: bool) -> str:
    try:
        rag_res = query(q, llm=llm, use_training_data=use_training_data, relevancy_check=relevancy_check)["response"]
        if type(rag_res) == dict:
            if rag_res["decision"] == "irrelevant":
                return f"RAG did not find any results for query: {q}."

        if(len(rag_res) < 1):
            return f"RAG did not find any results for query: {q}."
        else: 
            rag_res = f"{rag_res} (source: https://ntp.niehs.nih.gov/publications)"

        return rag_res
    except Exception as e:
        print("Error running RAG.")
        print(e)
        return f"Error: RAG failed to run with message: {e}."

class QueryRAG(BaseTool):
    name: str = "QueryRAG"
    description: str = "Search for chemical information using RAG across known documents that include NTP reports. These contain data about: carcinogenicity, developmental and reproductive toxicity, immunotoxicity, cancer and noncancer health effects, research, toxicity, and technical reports."
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, q: str) -> str:
        """Search for chemical information using RAG."""
        #rag_res = query_rag(q=q, llm=self.llm, use_training_data=False, relevancy_check=False) # never use training data when in agentic pipeline
        rag_res = query_rag(q=q, llm=self.llm, use_training_data=False, relevancy_check=True) # never use training data when in agentic pipeline

        return rag_res