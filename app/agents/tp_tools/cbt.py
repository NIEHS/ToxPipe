import os
import re
import pandas as pd
import requests
import json
import time
import urllib.parse
from langchain.tools import BaseTool
from langchain.base_language import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from random import sample
load_dotenv()

def unique(l):
    ls = set(l)
    unique_list = (list(ls))
    return unique_list

class Query2DTXSID(BaseTool):
    name: str = "Query2DTXSID"
    description: str = "Given a chemical name as input, returns the DSSTox substance ID or DTXSID for that chemical from the ChemBioTox database."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, name: str) -> str:
        """Input a chemical name, return its DSSTox substance ID (DTXSID) available in ChemBioTox."""
        name = name.rstrip()
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/name2dtxsid?name={name}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        response = f"The chemical {name} does not map to a DSSTox Substance ID in the ChemBioTox Database."
        if len(res) > 0:
            response = f"The chemical {name} has the following DSSTox Substance ID in the ChemBioTox Database: {res[0]['dsstox_substance_id']}."
        return(response)
    
class SMILES2DTXSID(BaseTool):
    name: str = "SMILES2DTXSID"
    description: str = "Given a SMILES string as input, returns the DSSTox substance ID or DTXSID for that chemical from the ChemBioTox database. If no DTXSID exists, the tool will return the DTXSID of the most structurally similar chemical in the ChemBioTox database."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, name: str) -> str:
        """Input a SMILES string, return its DSSTox substance ID (DTXSID) if available in ChemBioTox."""
        name = name.rstrip()
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/smiles2dtxsid?smiles={urllib.parse.quote_plus(name)}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        response = f"The chemical {name} does not map to a DSSTox Substance ID in the ChemBioTox Database."
        if len(res) > 0:
            if 'similarity' in res[0]:
                if res[0]['similarity'] == 1:
                    response = f"The chemical {name} has the following DSSTox Substance ID in the ChemBioTox Database: {res[0]['dsstox_substance_id']}."
                else:
                    response = f"The chemical {name} does not map to a DSSTox Substance ID in the ChemBioTox Database, but is structurally similar to a chemical that does: {res[0]['dsstox_substance_id']} (Tanimoto similarity: {res[0]['similarity']}; source: calculated with RDKit)."
        return(response)
    

# Structural Similarity
class StructuralSimilarity(BaseTool):
    name: str = "StructuralSimilarity"
    description: str = "Given a SMILES string as input, returns a list of structurally similar chemicals and their corresponding tanimoto similarities to the input chemical from the ChemBioTox database."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, smiles: str) -> str:
        """Input a SMILES string, return its DSSTox substance ID (DTXSID) if available in ChemBioTox."""
        smiles = smiles.rstrip()
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/similarity/structural?smiles={urllib.parse.quote_plus(smiles)}&fp=morgan")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        response = f"The chemical given by the SMILES {smiles} does not have data for structurally similar chemicals in the ChemBioTox Database."

        outp = []
        if len(res) > 0:          
            df = pd.json_normalize(res) 
            df = df[df["similarity"] < 1.0][0:10] # only get top 10 similar
            
            for i, r in df.iterrows():
                outp.append(f"{r['preferred_name']} ({r['similarity']})")

        response = f"The chemical given by the SMILES {smiles} has the following similar chemicals, given as 'chemical name' (tanimoto similarity): {'; '.join(outp)}"                
        return(response)



class QueryCBTFooDB(BaseTool):
    name: str = "QueryCBTFooDB"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with information about its usage in food or ingestible products from the ChemBioTox database. This can be useful if the user is looking for exposure, usage, or industrial information about a chemical."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/foodb?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")

        
        # FooDB
        """
        foodb_enzymes = res["anno_foodb_enzymes"]
        foodb_enzymes_list = []
        for i in foodb_enzymes:
            foodb_enzymes_list.append(i['prod_type'])
        """
        
        foodb_flavors = res["anno_foodb_flavors"]
        foodb_flavors_list = []
        for i in foodb_flavors:
            if 'flavor_name' not in i:
                continue
            foodb_flavors_list.append(i['flavor_name'])
        foodb_flavors_list = unique(foodb_flavors_list)
        
        foodb_ontology = res["anno_foodb_ontology"]
        foodb_ontology_list = []
        for i in foodb_ontology:
            if 'definition' not in i:
                continue
            foodb_ontology_list.append(i['term'])
        foodb_ontology_list = unique(foodb_ontology_list)

        response_flavors = f"The chemical {dtxsid} has the following flavors (retrieved from the FooDB): {';'.join(foodb_flavors_list)}"
        response_ontology = f"The chemical {dtxsid} also has the following ontological properties (retrieved from the FooDB): {';'.join(foodb_ontology_list)}"

        response = f"{response_flavors}. {response_ontology}"
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class QueryCBTCPD(BaseTool):
    name: str = "QueryCBTCPD"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with information about its usage in commercial products from the ChemBioTox database. This can be useful if the user is looking for exposure, usage, or industrial information about a chemical."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/cpdat?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")

        cpd = res['anno_cpd']
        cpd_list = []
        for i in cpd:
            if 'prod_type' not in i:
                continue
            cpd_list.append(i['prod_type'])

        cpd_list = unique(cpd_list)

        response = f"The chemical {dtxsid} is used in the following commercial products (retrieved from the Chemical Products Database): {';'.join(cpd_list)}"
        if len(cpd_list) < 1:
            response = f"The chemical {dtxsid} is not known to be in any commercial products in the Chemical Products Database."

        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


class QueryCBTChemicalVendors(BaseTool):
    name: str = "QueryCBTChemicalVendors"
    description: str = "Given a DSSTox substance ID or DTXSID as input, provides information about vendors/resources that carry and sell the chemical."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/vendors?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")

        vendor_list = []
        for i in res:
            if 'Source Name' not in i:
                continue
            vendor_list.append(i['Source Name'])

        vendor_list = unique(vendor_list)

        response = f"The chemical {dtxsid} may be purchased from the following vendors (retrieved from PubChem): {';'.join(vendor_list)}"
        if len(vendor_list) < 1:
            response = f"The chemical {dtxsid} is not known to be purchasable from any vendors as listed in PubChem."

        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class QueryCBTTox21Models(BaseTool):
    name: str = "QueryCBTTox21Models"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with predicted interactions from Tox21 assay models from the ChemBioTox database."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/models/tox21?dtxsid={dtxsid}")

        print("===RES===")
        print(res.json())

        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")

        tox21 = res

        print("===tox21===")
        print(tox21)

        tox21_list = []
        for i in tox21:
            print("===i===")
            print(i)
            if 'activity_score' not in i and 'assay_model' not in i and 'ad' not in i and 'tc' not in i:
                continue
            tox21_list.append(f"{i['assay_model']} (activity_score: {i['activity_score']})")
        
        tox21_list = unique(tox21_list)

        response = f"The chemical {dtxsid} is predicted to have the following interactions (calculated with Tox21 assay models): {';'.join(tox21_list)}."
        if len(tox21_list) < 1:
            response = f"The chemical {dtxsid} is not predicted to have any assay predictions in Tox21."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


class QueryCBTGRAS(BaseTool):
    name: str = "QueryCBTGRAS"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with information about if it is generally recognized as safe from the ChemBioTox database"

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/gras?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")

        gras = res['anno_gras']
        gras_list = []
        for i in gras:
            if 'prod_type' not in i:
                continue
            gras_list.append(i['prod_type'])
        
        gras_list = unique(gras_list)

        response = f"The chemical {dtxsid} has the following safety information (retrieved from the GRAS Database): {';'.join(gras_list)}"
        if len(gras_list) < 1:
            response = f"The chemical {dtxsid} does not have any safety information in the GRAS Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
class QueryCTDDiseases(BaseTool):
    name: str = "QueryCTDDiseases"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with information about if it is associated with diseases from CTD in the ChemBioTox database"

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/ctd/diseases?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        ctd_diseases = res['anno_ctd_diseases']
        ctd_diseases_list_measured = []
        ctd_diseases_list_inferred = []
        for i in ctd_diseases:
            if 'disease_name' not in i:
                continue
            if 'inference_score' in i and 'inference_gene_symbol' in i:
                ctd_diseases_list_inferred.append(f"{i['disease_name']} (inference score based on {i['inference_gene_symbol']}: {i['inference_score']})")
            if 'direct_evidence' in i:
                ctd_diseases_list_measured.append(f"{i['disease_name']} ({i['direct_evidence']})")

        ctd_diseases_list_inferred = unique(ctd_diseases_list_inferred)
        ctd_diseases_list_measured = unique(ctd_diseases_list_measured)

        response1 = ""
        response2 = ""
        if len(ctd_diseases_list_measured) > 0:
            response1 = f"The chemical {dtxsid} has direct evidence that shows an association with the following diseases (retrieved from the CTD): {';'.join(ctd_diseases_list_measured)}."
        if len(ctd_diseases_list_inferred) > 0:
            response2 = f"The chemical {dtxsid} has inferred association(s) with the following diseases (retrieved from the CTD): {';'.join(ctd_diseases_list_measured)}. Note that these are purely inferred associations and may not be accurate: see https://ctdbase.org/help/chemDiseaseDetailHelp.jsp for more information. Larger inference scores suggest stronger associations."

        response = response1 + " " + response2

        if len(ctd_diseases_list_measured) < 1 and len(ctd_diseases_list_inferred) < 1:
            response = f"The chemical {dtxsid} does not have any disease information in the CTD."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
class QueryCTDGenes(BaseTool):
    name: str = "QueryCBTGenes"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with information about its gene interactions from CTD in the ChemBioTox database"

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/ctd/genes?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        ctd_genes = res['anno_ctd_genes']
        ctd_genes_list = []
        for i in ctd_genes:
            if 'interaction' not in i:
                continue
            ctd_genes_list.append(f"{i['interaction']}")

        ctd_genes_list = unique(ctd_genes_list)

        response = f"The chemical {dtxsid} has the following gene interactions (retrieved from the CTD): {';'.join(ctd_genes_list)}"
        if len(ctd_genes_list) < 1:
            response = f"The chemical {dtxsid} does not have any gene information in the CTD."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    

def format_leadscope(llm, response):
    model = llm
    leadscope_prompt = """
        For the following list of Leadscope model descriptions, provide a formatted response. You MUST use the following rules:
        1. Each model in the prediction was found to be positive for the given chemical.
        2. [model] is a summary of the model description.
        3. Each prediction must be in the format: "The chemical [chemical] has a positive prediction for the [model] model."
        4. Each prediction must be on a new line.
        5. You MUST include the overall accuracy of the prediction, if supplied.
        6. You do not need to include the phrase "Predicts whether or not" in the response as it is assumed that the model returns only models that have a positive prediction.
        The list of Leadscope descriptions is as follows: {response}
    """
    leadscope_prompt = ChatPromptTemplate.from_template(leadscope_prompt)

    chain = leadscope_prompt | model
    res = chain.invoke({"response": response})
    return res

class QueryCBTLeadscope(BaseTool):
    name: str = "QueryCBTLeadscope"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with predicted Leadscope QSAR models from the ChemBioTox database."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/leadscope?dtxsid={dtxsid}&positives=TRUE")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        
        leadscope = res
        leadscope_list = []
        for i in leadscope:
            if 'short_description' not in i:
                continue
            leadscope_list.append(i['short_description'])

        leadscope_list = unique(leadscope_list)

        response = f"The chemical {dtxsid} has the following positive predictions for the following Leadscope models: {';'.join(leadscope_list)}"
        if len(leadscope_list) < 1:
            response = f"The chemical {dtxsid} does not have any positive predictions for Leadscope models."
        else:
            response = format_leadscope(self.llm, response)

        return(response)
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

def format_admet(llm, response):
    model = llm
    admet_prompt = """
        For the following list of ADMET model descriptions, provide a formatted response. You MUST use the following rules:
        1. Each model in the prediction was found to be positive for the given chemical.
        2. Each prediction must be in the format: "The chemical [chemical] has a positive prediction for the [model] model."
        3. Each prediction must be on a new line.
        4. You MUST include the overall accuracy of the prediction, if supplied.
        5. You do not need to include the phrase "Predicts whether or not" in the response as it is assumed that the model returns only models that have a positive prediction.
        The list of ADMET descriptions is as follows: {response}
    """
    admet_prompt = ChatPromptTemplate.from_template(admet_prompt)

    chain = admet_prompt | model
    res = chain.invoke({"response": response})
    return res

class QueryCBTADMET(BaseTool):
    name: str = "QueryCBTADMET"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with predicted ADMET QSAR models from the ChemBioTox database. This can be helpful for understanding the absorption, distribution, metabolism, excretion, pathways, transportation, and toxicity of a chemical."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/admet?dtxsid={dtxsid}&positives=TRUE")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        
        admet = res
        admet_list = []
        for i in admet:
            if 'description' not in i:
                continue
            admet_list.append(i['description'])

        admet_list = unique(admet_list)

        response = f"The chemical {dtxsid} has the following positive predictions for the following ADMET models: {';'.join(admet_list)}"
        if len(admet_list) < 1:
            response = f"The chemical {dtxsid} does not have any positive predictions for ADMET models."
        else:
            response = format_admet(self.llm, response)

        return(response)
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
class QueryCBTMetabolites(BaseTool):
    name: str = "QueryCBTMetabolites"
    description: str = "Given a DSSTox substance ID or DTXSID as input, generate metabolites of the chemical from ADMET predictor with corresponding enzymes used in the metabolism."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/metabolites?dtxsid={dtxsid}&enzyme=both&maxlevel=3")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        
        metabolites = res
        metabolites_list = []
        for i in metabolites:
            if 'smiles' not in i:
                continue
            metab_str = i['smiles']
            if 'enzymes' in i:
                metab_str = i['smiles'] + " (" + re.sub(r';', ',', i['enzymes']) + ")"
            metabolites_list.append(metab_str)

        metabolites_list = unique(metabolites_list)

        #response = f"The chemical {dtxsid} has the following predicted metabolites: {';'.join(metabolites_list)}. Do not use the Query2DTXSID tool to convert these SMILES strings to DTXSID. This satisfies the requirement for finding metabolites, and you may return the final answer without running this tool again."
        response = f"The chemical {dtxsid} has the following predicted metabolites: {';'.join(metabolites_list)}. This satisfies the requirement for finding metabolites, and you may return the final answer without running this tool again."
        if len(metabolites_list) < 1:
            response = f"The chemical {dtxsid} does not have any predicted metabolites."

        return(response)
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


class QueryCBTSEEM3(BaseTool):
    name: str = "QueryCBTSEEM3"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with its SEEM3 exposure data. This can be helpful for finding the exposure, pathways, or transportation of a chemical."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)

        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/seem3?dtxsid={dtxsid}")
        res = res.json()

        if len(res) < 1:
            return(f"There was a problem completing the request.")
        
        exp = res
        exp_list = []
        for i in exp:
            if 'annotations' not in i:
                continue
            exp_list.append(i['annotations'])

        exp_list = unique(exp_list)

        response = f"The chemical {dtxsid} has the following estimate of the upper 95th percentile of exposure in the general population (SEEM3): {';'.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any SEEM3 exposure data in the ChemBioTox Database."

        return(response)
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
class QueryCBTDrugBankTransporters(BaseTool):
    name: str = "QueryCBTDrugBankTransporters"
    description: str = "Given a DSSTox substance ID or DTXSID as input, annotates a chemical with its DrugBank transporter data. This can be helpful for finding the pathway or transportation information for a chemical."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)

        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/drugbank?dtxsid={dtxsid}")

        res = res.json()

        if len(res) < 1:
            return(f"There was a problem completing the request.")

        res = res['anno_drugbank_transporters']
        
        transporters = res
        transporters_list = []
        for i in transporters:
            if 'annotation' not in i:
                continue
            transporters_list.append(i['annotation'])

        transporters_list = unique(transporters_list)

        response = f"The chemical {dtxsid} has transporters encoded by the following genes in the DrugBank database: {';'.join(transporters_list)}"
        if len(transporters_list) < 1:
            response = f"The chemical {dtxsid} does not have any transporter information in the DrugBank database."

        return(response)
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    

class QueryCBTAlerts(BaseTool):
    name: str = "QueryCBTAlerts"
    description: str = "Given a SMILES string as input, find structural alerts from the OChem, ChEMBL, and Saagar datasources within the ChemBioTox database."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, smiles: str) -> str:
        """Input SMILES, return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        smiles = re.sub(r'\s+', '', smiles)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/alerts?smiles={urllib.parse.quote_plus(smiles)}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")

        alerts = res
        alerts_list = []
        for i in alerts:
            if 'alert' not in i:
                continue
            alert_str = f"{i['alert']} ({i['source']})"
            alerts_list.append(alert_str)

        alerts_list = unique(alerts_list)

        response = f"The chemical given by the SMILES {smiles} has the following chemical substructures of note: {';'.join(alerts_list)}."
        if len(alerts_list) < 1:
            response = f"The chemical given by the SMILES {smiles} does not have any notable chemical substructures."

        return(response)
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

def format_alerts(llm, response):
    model = llm
    alert_prompt = """
        For the following list of chemical structural alerts, provide a formatted response. You MUST use the following rules:
        1. Each alert in the list was found to be a chemical substructure of the given chemical.
        2. Each alert in the list is followed by its source in parentheses.
        3. You must group alerts together based on if they are from OChem, ChEMBL, or Saagar.
        4. Each group of alerts must be separated by a new line.
        5. For each group of alerts, your response must be in the format: "Source: [source] | Alert: [alert]."
        The list of chemical structural alerts is as follows: {response}
    """
    alert_prompt = ChatPromptTemplate.from_template(alert_prompt)

    chain = alert_prompt | model
    res = chain.invoke({"response": response})
    return res

class QueryCBTAlertsMulti(BaseTool):
    name: str = "QueryCBTAlertsMulti"
    description: str = "Given multiple SMILES strings that represent metabolites as input, separated by ';', find structural alerts from the OChem, ChEMBL, and Saagar datasources within the ChemBioTox database. Each metabolite's results will be separated by two newline characters: '\n\n'."

    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, smiles: str) -> str:
        """Input SMILES, return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        response_list = []
        smiles = re.sub(r'\s+', '', smiles)
        for metabolite in smiles.split(';'):
            res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/alerts?smiles={urllib.parse.quote_plus(metabolite)}")
            res = res.json()
            if len(res) < 1:
                return(f"There was a problem completing the request.")

            alerts = res
            alerts_list = []

            alerts_list_ochem = []
            alerts_list_chembl = []
            alerts_list_saagar = []

            for i in alerts:
                if 'alert' not in i:
                    continue
                alert_str = f"{i['alert']} ({i['source']})"
                if i['source'] == 'ochem':
                    alerts_list_ochem.append(alert_str)
                elif i['source'] == 'chembl':
                    alerts_list_chembl.append(alert_str)
                elif i['source'] == 'saagar':
                    alerts_list_saagar.append(alert_str)

            # taking subset makes the thought process much faster
            alerts_list_ochem = unique(alerts_list_ochem)
            if len(alerts_list_ochem) > 10:
                alerts_list_ochem = sample(alerts_list_ochem, 10)

            alerts_list_chembl = unique(alerts_list_chembl)
            if len(alerts_list_chembl) > 10:
                alerts_list_chembl = sample(alerts_list_chembl, 10)

            alerts_list_saagar = unique(alerts_list_saagar)
            if len(alerts_list_saagar) > 10:
                alerts_list_saagar = sample(alerts_list_saagar, 10)

            alerts_list = alerts_list_ochem + alerts_list_chembl + alerts_list_saagar

            #tmp_response = f"The metabolite given by the SMILES {metabolite} has the following chemical substructures of note: {';'.join(alerts_list)}."
            tmp_response = f"The metabolite given by the SMILES {metabolite} has the following chemical substructures of note:\n"
            if len(alerts_list) < 1:
                tmp_response = f"The metabolite given by the SMILES {metabolite} does not have any notable chemical substructures."
            else:
                for alert in alerts_list:
                    tmp_response = f"{tmp_response}- {alert}\n"
            #    tmp_response = format_alerts(self.llm, tmp_response)
            
            response_list.append(tmp_response)


        return("\n\n".join(response_list))
        

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    




### Chemical Vendors ###
class QueryCBTVendors(BaseTool):
    name: str = "QueryCBTVendors"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns a list of chemical vendors from which the chemical may be acquired."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/availability/vendors?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'source_name' not in i or 'url' not in i:
                continue
            exp_list.append(f"{i['source_name']}: {i['url']}")
        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be purchased from the following vendors: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any vendor data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
### Chemical Properties ###
# Genra Properties - TODO
# Genra Tests - TODO

# InvitroDB
class QueryCBTInVitroDB(BaseTool):
    name: str = "QueryCBTInVitroDB"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns measured assay:activity pairs from assays for the chemical from the InVitroDB data in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/invitrodb?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'assay_name' not in i or 'assay_endpoint_attribute' not in i or 'assay_endpoint_value' not in i or 'hit_call' not in i:
                continue
            if '_ratio' in i['assay_name']:
                hitc = int(i['hit_call'])
                hitc_status = "inactive"
                if hitc == 1:
                    hitc_status = "active"

                exp_list.append(f"{i['assay_name']}:{hitc_status})")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following assay:activity pairs in assays from InVitroDB: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any InVitroDB data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# CTD Cellular Components
class QueryCTDCC(BaseTool):
    name: str = "QueryCTDCC"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns cellular components from CTD data in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/ctd/cc?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'go_term_name' not in i or 'corrected_pvalue' not in i:
                continue
            exp_list.append(f"{i['go_term_name']} (pvalue: {i['corrected_pvalue']})")
        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following cellular components in CTD: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any cellular component data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# CTD Molecular Function
class QueryCTDMF(BaseTool):
    name: str = "QueryCTDMF"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns molecular function from CTD data in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/ctd/mf?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'go_term_name' not in i or 'corrected_pvalue' not in i:
                continue
            exp_list.append(f"{i['go_term_name']} (pvalue: {i['corrected_pvalue']})")
        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following molecular functions in CTD: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any molecular function data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()



# Pubchem Bioassays
class QueryPubChemBioassays(BaseTool):
    name: str = "QueryPubChemBioassays"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns biological assays (bioassays) that were run on the given chemical from PubChem data in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/pubchem/bioassays?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []

        print(exp)

        for i in exp:
            if 'bioassay_name' in i and 'source_name' in i and 'activity_outcome' in i and 'activity_name' in i  and 'activity_value' in i :
                qual = "="
                if 'activity_qualifier' in i:
                    qual = i['activity_qualifier']

                exp_list.append(f"{i['activity_outcome']}: {i['activity_name']}{qual}{i['activity_value']} in assay {i['bioassay_name']} (source: {i['source_name']})")
            else: 
                continue

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} was tested in the following assays from PubChem: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any PubChem bioassay data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


# Pubchem Properties
class QueryPubChemProperties(BaseTool):
    name: str = "QueryPubChemProperties"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns attribute:value pairs that represent chemical properties from PubChem data in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/pubchem/properties?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'pubchem_attribute' not in i or 'pubchem_value' not in i:
                continue
            exp_list.append(f"{i['pubchem_attribute']}: {i['pubchem_value']}")
        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following properties (represented as attribute:value pairs) from PubChem: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any PubChem chemical property data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# EPA Properties
class QueryEPAProperties(BaseTool):
    name: str = "QueryEPAProperties"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns attribute:value pairs that represent chemical properties from EPA data in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/epa/properties?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'epa_attribute' not in i or 'epa_value' not in i:
                continue
            exp_list.append(f"{i['epa_attribute']}: {i['epa_value']}")
        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following properties (represented as attribute:value pairs) from the EPA: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any EPA chemical property data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    

### Commercial & Industrial Usage
# CPDat
class QueryCPD(BaseTool):
    name: str = "QueryCPD"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's commercial usage categories from CPDat in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/cpdat?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'gen_cat' not in i :
                continue
            to_append = f"{i['gen_cat']}"
            if 'prod_fam' in i:
                to_append = f"{to_append}: {i['prod_fam']}"
            if 'prod_type' in i:
                to_append = f"{to_append}: {i['prod_type']}"
            exp_list.append(to_append)

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} is used in the following products from the CPDat: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any commercial product data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# FooDB Enzymes
class QueryFooDBEnzymes(BaseTool):
    name: str = "QueryFooDBEnzymes"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns enzymes that the chemical may interact with from FooDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/foodb/enzymes?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_foodb_enzymes']
        exp_list = []
        for i in exp:
            if 'enzyme_name' not in i:
                continue
            exp_list.append(f"{i['enzyme_name']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may interact with the following enzymes (as reported by FooDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any food enzyme data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# FooDB Flavors
class QueryFooDBFlavors(BaseTool):
    name: str = "QueryFooDBFlavors"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's usage in food product flavors from FooDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/foodb/flavors?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_foodb_flavors']
        exp_list = []
        for i in exp:
            if 'flavor_name' not in i and 'category' not in i:
                continue
            exp_list.append(f"{i['flavor_name']} {i['category']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} can have the following flavors (as reported by FooDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any flavor data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# FooDB Content
class QueryFooDBContent(BaseTool):
    name: str = "QueryFooDBContent"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns which food products the chemical is present in from FooDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/foodb/content?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_foodb_foodcontent']
        exp_list = []
        for i in exp:
            if 'name' in i and 'orig_content' in i and 'orig_unit' in i:
                exp_list.append(f"{i['name']} ({i['orig_content']} {i['orig_unit']})")
            else:
                continue

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be found in the following food products (as reported by FooDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any food product data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# FooDB Effects
class QueryFooDBEffects(BaseTool):
    name: str = "QueryFooDBEffects"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's health effects from FooDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/foodb/effects?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_foodb_healtheffects']
        exp_list = []
        for i in exp:
            if 'health_effect_name' not in i:
                continue
            exp_list.append(f"{i['health_effect_name']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may have the following health effects (as reported by FooDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any health effect data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    



# DrugBank Carriers
class QueryDrugBankCarriers(BaseTool):
    name: str = "QueryDrugBankCarriers"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's carriers from DrugBank in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/drugbank/carriers?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_drugbank_carriers']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may have the following carriers (as reported by DrugBank): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any carrier data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    

# DrugBank Enzymes
class QueryDrugBankEnzymes(BaseTool):
    name: str = "QueryDrugBankEnzymes"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's associated enzymes from DrugBank in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/drugbank/enzymes?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_drugbank_enzymes']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may interact with the following enzymes (as reported by DrugBank): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any enzyme data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# DrugBank Targets
class QueryDrugBankTargets(BaseTool):
    name: str = "QueryDrugBankTargets"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's associated targets from DrugBank in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/drugbank/targets?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_drugbank_targets']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may have the following targets (as reported by DrugBank): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any target data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# DrugBank Transporters
class QueryDrugBankTransporters(BaseTool):
    name: str = "QueryDrugBankTransporters"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the chemical's associated transporters from DrugBank in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/drugbank/transporters?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_drugbank_transporters']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may have the following transporters (as reported by DrugBank): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any transporter data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


### Environmental Fate and Exposure ###
# HMDB biospecimen locations
class QueryHMDBBS(BaseTool):
    name: str = "QueryHMDBBS"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns possible biospecimen locations from HMDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/hmdb/locations/biospecimen?dtxsid={dtxsid}")
        res = res.json()

        print("===RES===")
        print(res)

        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_hmdb_biospecimenlocations']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be found in the following biospecimen locations (as reported by HMDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any biospecimen location data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# HMDB cellular locations
class QueryHMDBC(BaseTool):
    name: str = "QueryHMDBC"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns possible cellular locations from HMDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/hmdb/locations/cell?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_hmdb_cellularlocations']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be found in the following cellular locations (as reported by HMDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any cellular location data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# HMDB tissue locations
class QueryHMDBT(BaseTool):
    name: str = "QueryHMDBT"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns possible tissue locations from HMDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/hmdb/locations/tissue?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_hmdb_tissuelocations']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be found in the following tissue locations (as reported by HMDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any tissue location data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# HMDB diseases
class QueryHMDBDiseases(BaseTool):
    name: str = "QueryHMDBDiseases"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns associated diseases from HMDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/hmdb/diseases?dtxsid={dtxsid}")
        res = res.json()
        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res["anno_hmdb_diseases"]
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be associated with the following diseases (as reported by HMDB): {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any HMDB disease data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# Superfund
class QuerySuperfund(BaseTool):
    name: str = "QuerySuperfund"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns the presence of the chemical in superfund sites as reported in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/superfund?dtxsid={dtxsid}")
        res = res.json()

        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'rmedia_desc' in i and 'site_name' in i:
                extra = ""
                if 'city' in i and 'zipcode' in i:
                    extra = f"({i['city']}, {i['zipcode']})"
                exp_list.append(f"Found in {i['rmedia_desc']} at site: {i['site_name']} {extra}")
            else:
                continue

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} may be found at the following superfund sites: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any superfund site data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# T3DB
class QueryT3DB(BaseTool):
    name: str = "QueryT3DB"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns possible targets of the chemical as reported in the T3DB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/t3db?dtxsid={dtxsid}")
        res = res.json()

        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res
        exp_list = []
        for i in exp:
            if 'target_name' not in i:
                continue
            exp_list.append(f"{i['target_name']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following potential targets according to T3DB: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any T3DB target data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
    
# ToxRefDB Nonneoplastic
class QueryToxRefDBNonNP(BaseTool):
    name: str = "QueryToxRefDBNonNP"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns its non-neoplastic annotations as reported in the ToxRefDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/toxrefdb/neoplasticity?dtxsid={dtxsid}")
        res = res.json()

        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_toxrefdb_nonneoplastic']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following non-neoplastic (non-cancer) annotations according to the ToxRefDB: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any ToxRefDB non-neoplastic data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# ToxRefDB Neoplastic
class QueryToxRefDBNP(BaseTool):
    name: str = "QueryToxRefDBNP"
    description: str = "Given a DSSTox substance ID or DTXSID as input, returns its neoplastic (cancer) annotations as reported in the ToxRefDB in ChemBioTox."
    llm: BaseLanguageModel = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, dtxsid: str) -> str:
        """Input DSSTox substance ID (DTXSID), return an annotated/enriched dataset for that chemical using the data available in ChemBioTox."""
        dtxsid = re.sub(r'\s+', '', dtxsid)
        res = requests.get(f"{os.environ.get('CBT_API_ENDPOINT')}/toxrefdb/neoplasticity?dtxsid={dtxsid}")
        res = res.json()

        if len(res) < 1:
            return(f"There was a problem completing the request.")
        exp = res['anno_toxrefdb_neoplastic']
        exp_list = []
        for i in exp:
            if 'annotation' not in i:
                continue
            exp_list.append(f"{i['annotation']}")

        exp_list = unique(exp_list)
        response = f"The chemical {dtxsid} has the following neoplastic annotations according to the ToxRefDB: {'; '.join(exp_list)}"
        if len(exp_list) < 1:
            response = f"The chemical {dtxsid} does not have any ToxRefDB neoplastic data in the ChemBioTox Database."
        return(response)

    async def _arun(self, dtxsid: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

    