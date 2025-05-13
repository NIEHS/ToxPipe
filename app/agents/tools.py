from langchain.base_language import BaseLanguageModel
from .tp_tools import *

# Instantiate tools available for agent use
def make_tools(llm: BaseLanguageModel, verbose=True, auth=False):
    all_tools = [
        Name2SMILES(),
        Query2CAS(),
        PatentCheck(),
        MolSimilarity(),
        SMILES2Weight(),
        FuncGroups(),
        ExplosiveCheck(),
        ControlChemCheck(),
        SafetySummary(llm=llm),
        QueryCBTChemicalVendors(),
        QueryCBTGRAS(),
        QueryCBTTox21Models(),
        Name2DTXSID(),
        Query2DTXSID(),
        SMILES2DTXSID(),
        CASRN2DTXSID(),

        StructuralSimilarity(),

        QueryCBTSEEM3(llm=llm),
        QueryCBTDrugBankTransporters(llm=llm),

        QueryCBTInVitroDB(llm=llm),
        QueryCTDDiseases(llm=llm),
        QueryCTDGenes(llm=llm),
        QueryCTDCC(llm=llm),
        QueryCTDMF(llm=llm),
        QueryCTDBP(llm=llm),

        QueryPubChemSynonyms(llm=llm),
        QueryPubChemMass(llm=llm),
        QueryPubChemFormula(llm=llm),
        QueryPubChemWeight(llm=llm),
        QueryPubChemXLogP(llm=llm),
        
        QueryPubChemBioassays(llm=llm),
        QueryEPAProperties(llm=llm),
        QueryCPD(llm=llm),
        QueryFooDBEnzymes(llm=llm),
        QueryFooDBFlavors(llm=llm),
        QueryFooDBContent(llm=llm),
        QueryFooDBEffects(llm=llm),

        QueryDrugBankCarriers(llm=llm),
        QueryDrugBankEnzymes(llm=llm),
        QueryDrugBankTargets(llm=llm),
        QueryDrugBankTransporters(llm=llm),

        QueryHMDBBS(llm=llm),
        QueryHMDBC(llm=llm),
        QueryHMDBT(llm=llm),
        QueryHMDBDiseases(llm=llm),

        QuerySuperfund(llm=llm),

        QueryT3DB(llm=llm),

        QueryToxRefDBStudies(llm=llm)

    ]

    if auth == True: # If authenticated, append proprietary tools
        all_tools.append(FunctionalSimilarity())
        all_tools.append(QueryCBTLeadscope(llm=llm))
        all_tools.append(QueryCBTADMET(llm=llm))
        all_tools.append(QueryCBTMetabolites(llm=llm))

    return all_tools

def make_translate_tools(llm: BaseLanguageModel):
    translate_tools = [
        Name2DTXSID(),
        SMILES2DTXSID(),
        CASRN2DTXSID(),
        Query2Disease(llm=llm),
    ]
    return translate_tools

def make_disease_tools(llm: BaseLanguageModel):
    disease_tools = [
        QueryHMDBDisease2Chemicals(llm=llm),
        QueryCTDDisease2Chemicals(llm=llm),
    ]
    return disease_tools


def make_rag_tools(llm: BaseLanguageModel):
    rag_tools = [
        QueryRAG(llm=llm),
    ]
    return rag_tools

def make_literature_tools(llm: BaseLanguageModel):
    literature_tools = [
        Scholar2ResultLLM(llm=llm),
    ]
    return literature_tools