import os
import re
import pandas as pd
from langchain.tools import BaseTool
from langchain.llms import BaseLLM
from random import sample
from ...rag import query

def query_rag(q: str, llm: BaseLLM, use_training_data: bool) -> str:
    try:
        rag_res = query(q, llm=llm, use_training_data=use_training_data)["response"]
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
    description: str = "Search for chemical information using RAG across known documents that include NTP and ChEMBL reports. These contain data about: carcinogenicity, developmental and reproductive toxicity, immunotoxicity, cancer and noncancer health effects, research, toxicity, and technical reports."
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, q: str, **kwargs) -> str:
        """Search for chemical information using RAG."""
        rag_res = query_rag(q=q, llm=self.llm, use_training_data=False) # never use training data when in agentic pipeline

        return rag_res