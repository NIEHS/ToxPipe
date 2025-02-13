from langchain.base_language import BaseLanguageModel
from .tp_tools import *

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
        Scholar2ResultLLM(llm=llm), # Note: very slow
        #SafetySummary(llm=llm),
        GeneExpression(llm=llm),
        HallmarkGeneAnalyzer(llm=llm),
        Rat2HumanGene(llm=llm),
        Human2RatGene(llm=llm),
        QueryCBTFooDB(),
        QueryCBTChemicalVendors(),
        QueryCBTGRAS(),
        QueryCBTTox21Models(),
        Name2DTXSID(),
        Query2DTXSID(),
        SMILES2DTXSID(),

        StructuralSimilarity(),

        #QueryCBTAlerts(llm=llm), # These are really hard for the LLM to parse in a meaningful way right now
        #QueryCBTAlertsMulti(llm=llm),
        QueryCBTSEEM3(llm=llm),
        QueryCBTDrugBankTransporters(llm=llm),

        QueryCBTInVitroDB(llm=llm),
        QueryCTDDiseases(llm=llm),
        QueryCTDGenes(llm=llm),
        QueryCTDCC(llm=llm),
        QueryCTDMF(llm=llm),
        QueryCTDBP(llm=llm),
        QueryPubChemProperties(llm=llm),
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

        QueryToxRefDBNonNP(llm=llm),
        QueryToxRefDBNP(llm=llm),

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
