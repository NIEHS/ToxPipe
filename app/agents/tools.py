from langchain.base_language import BaseLanguageModel

from .tp_tools import *

def make_tools(llm: BaseLanguageModel, verbose=True):
    all_tools = [
        Query2SMILES(),
        Query2CAS(),
        PatentCheck(),
        MolSimilarity(),
        SMILES2Weight(),
        FuncGroups(),
        ExplosiveCheck(),
        ControlChemCheck(),
        Scholar2ResultLLM(llm=llm),
        SafetySummary(llm=llm),
        GeneExpression(llm=llm),
        HallmarkGeneAnalyzer(llm=llm),
        Rat2HumanGene(llm=llm),
        Human2RatGene(llm=llm),
        QueryCBTFooDB(),
        QueryCBTChemicalVendors(),
        QueryCBTGRAS(),
        QueryCBTTox21Models(),
        Query2DTXSID(),
        SMILES2DTXSID(),

        StructuralSimilarity(),
        FunctionalSimilarity(), # Proprietary
        QueryCBTLeadscope(llm=llm), # Proprietary
        QueryCBTADMET(llm=llm), # Proprietary
        QueryCBTMetabolites(llm=llm), # Proprietary
        QueryCBTAlerts(llm=llm),
        QueryCBTAlertsMulti(llm=llm),
        QueryCBTSEEM3(llm=llm),
        QueryCBTDrugBankTransporters(llm=llm),

        QueryCBTVendors(llm=llm),
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






    ]
    return all_tools
