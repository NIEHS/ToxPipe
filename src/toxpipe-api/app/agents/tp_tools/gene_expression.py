import pandas as pd
import numpy as np
import re
import langchain
from langchain.base_language import BaseLanguageModel
from langchain.llms import BaseLLM
from langchain.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
import concurrent.futures
from ..prompts_gene import GENE_PREFIX, GENE_FORMAT_INSTRUCTIONS, GENE_QUESTION_PROMPT, GENE_REPHRASE_TEMPLATE, GENE_SUFFIX
from .search import *

import os
dir_path = os.path.dirname(os.path.realpath(__file__))


def ge_search(llm, query: str):
    """
    Given a gene and tissue, query the LLM to find the gene expression.
    """
    gene_prompt = ChatPromptTemplate.from_template(f"{GENE_PREFIX}\n\n{GENE_FORMAT_INSTRUCTIONS}\n\n{GENE_QUESTION_PROMPT}\n\n{GENE_SUFFIX}")
    model = llm
    chain = gene_prompt | model
    res = chain.invoke({"query": query})
    return(res.content)


class GeneExpression(BaseTool):
    name: str = "GeneExpression"
    description: str = (
        "Given a gene and tissue, query the LLM to find the gene expression."
    )
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, query, **kwargs) -> str:
        return ge_search(self.llm, query)

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")

data_path = os.path.join(dir_path, "data/rat2human.csv")
gene_mapping = pd.read_csv(data_path, sep="\t")

# TODO: include sources for these mappings
class Rat2HumanGene(BaseTool):
    name: str = "Rat2HumanGene"
    description: str = (
        "Given a rat gene, convert to a human gene. A result of nan indicates that there is no equivalent human gene for the given rat gene."
    )
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, query, **kwargs) -> str:
        mapped = gene_mapping.loc[gene_mapping['Rat Gene Symbol'] == query]['Human Gene Symbol'].values[0]
        if mapped is None or mapped == "nan":
            return f"No human gene found for the rat gene {query}."
        return f"The human gene corresponding to the rat gene {query} is {mapped}."

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")
    
class Human2RatGene(BaseTool):
    name: str = "Human2RatGene"
    description: str = (
        "Given a human gene, convert to a rat gene. A result of nan indicates that there is no equivalent rat gene for the given human gene."
    )
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, query, **kwargs) -> str:
        mapped = gene_mapping.loc[gene_mapping['Human Gene Symbol'] == query]['Rat Gene Symbol'].values[0]
        if mapped is None or np.isnan(mapped) or mapped == "nan":
            return f"No rat gene found for the human gene {query}."
        return f"The rat gene corresponding to the human gene {query} is {mapped}."

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")

# Pre-load Hallmark dataset
data_path = os.path.join(dir_path, "data/hallmark_genes.csv")
hallmark_genes = pd.read_csv(data_path, sep="\t")
hallmark_adipogenesis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_ADIPOGENESIS']
hallmark_allograft_rejection = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_ALLOGRAFT_REJECTION']
hallmark_androgen_response = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_ANDROGEN_RESPONSE']
hallmark_angiogenesis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_ANGIOGENESIS']
hallmark_apical_junction = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_APICAL_JUNCTION']
hallmark_apical_surface = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_APICAL_SURFACE']
hallmark_apoptosis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_APOPTOSIS']
hallmark_bile_acid_metabolism = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_BILE_ACID_METABOLISM']
hallmark_cholesterol_homeostasis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_CHOLESTEROL_HOMEOSTASIS']
hallmark_coagulation = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_COAGULATION']
hallmark_complement = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_COMPLEMENT']
hallmark_dna_repair = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_DNA_REPAIR']
hallmark_e2f_targets = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_E2F_TARGETS']
hallmark_epithelial_mesenchymal_transition = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION']
hallmark_estrogen_response_early = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_ESTROGEN_RESPONSE_EARLY']
hallmark_estrogen_response_late = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_ESTROGEN_RESPONSE_LATE']
hallmark_fatty_acid_metabolism = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_FATTY_ACID_METABOLISM']
hallmark_g2m_checkpoint = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_G2M_CHECKPOINT']
hallmark_glycolysis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_GLYCOLYSIS']
hallmark_hedgehog_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_HEDGEHOG_SIGNALING']
hallmark_heme_metabolism = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_HEME_METABOLISM']
hallmark_hypoxia = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_HYPOXIA']
hallmark_il2_stat5_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_IL2_STAT5_SIGNALING']
hallmark_il6_jak_stat3_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_IL6_JAK_STAT3_SIGNALING']
hallmark_inflammatory_response = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_INFLAMMATORY_RESPONSE']
hallmark_interferon_alpha_response = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_INTERFERON_ALPHA_RESPONSE']
hallmark_interferon_gamma_response = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_INTERFERON_GAMMA_RESPONSE']
hallmark_kras_signaling_dn = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_KRAS_SIGNALING_DN']
hallmark_kras_signaling_up = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_KRAS_SIGNALING_UP']
hallmark_mitotic_spindle = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_MITOTIC_SPINDLE']
hallmark_mtorc1_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_MTORC1_SIGNALING']
hallmark_myc_targets_v1 = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_MYC_TARGETS_V1']
hallmark_myc_targets_v2 = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_MYC_TARGETS_V2']
hallmark_myogenesis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_MYOGENESIS']
hallmark_notch_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_NOTCH_SIGNALING']
hallmark_oxidative_phosphorylation = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_OXIDATIVE_PHOSPHORYLATION']
hallmark_p53_pathway = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_P53_PATHWAY']
hallmark_pancreas_beta_cells = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_PANCREAS_BETA_CELLS']
hallmark_peroxisome = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_PEROXISOME']
hallmark_pi3k_akt_mtor_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_PI3K_AKT_MTOR_SIGNALING']
hallmark_protein_secretion = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_PROTEIN_SECRETION']
hallmark_reactive_oxygen_species_pathway = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_REACTIVE_OXYGEN_SPECIES_PATHWAY']
hallmark_spermatogenesis = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_SPERMATOGENESIS']
hallmark_tgf_beta_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_TGF_BETA_SIGNALING']
hallmark_tnfa_signaling_via_nfkb = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_TNFA_SIGNALING_VIA_NFKB']
hallmark_unfolded_protein_response = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_UNFOLDED_PROTEIN_RESPONSE']
hallmark_uv_response_dn = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_UV_RESPONSE_DN']
hallmark_uv_response_up = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_UV_RESPONSE_UP']
hallmark_wnt_beta_catenin_signaling = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_WNT_BETA_CATENIN_SIGNALING']
hallmark_xenobiotic_metabolism = hallmark_genes[hallmark_genes['Label'] == 'HALLMARK_XENOBIOTIC_METABOLISM']
hallmark_genes_dict = {
    "hallmark_adipogenesis": hallmark_adipogenesis,
    "hallmark_allograft_rejection": hallmark_allograft_rejection,
    "hallmark_androgen_response": hallmark_androgen_response,
    "hallmark_angiogenesis": hallmark_angiogenesis,
    "hallmark_apical_junction": hallmark_apical_junction,
    "hallmark_apical_surface": hallmark_apical_surface,
    "hallmark_apoptosis": hallmark_apoptosis,
    "hallmark_bile_acid_metabolism": hallmark_bile_acid_metabolism,
    "hallmark_cholesterol_homeostasis": hallmark_cholesterol_homeostasis,
    "hallmark_coagulation": hallmark_coagulation,
    "hallmark_complement": hallmark_complement,
    "hallmark_dna_repair": hallmark_dna_repair,
    "hallmark_e2f_targets": hallmark_e2f_targets,
    "hallmark_epithelial_mesenchymal_transition": hallmark_epithelial_mesenchymal_transition,
    "hallmark_estrogen_response_early": hallmark_estrogen_response_early,
    "hallmark_estrogen_response_late": hallmark_estrogen_response_late,
    "hallmark_fatty_acid_metabolism": hallmark_fatty_acid_metabolism,
    "hallmark_g2m_checkpoint": hallmark_g2m_checkpoint,
    "hallmark_glycolysis": hallmark_glycolysis,
    "hallmark_hedgehog_signaling": hallmark_hedgehog_signaling,
    "hallmark_heme_metabolism": hallmark_heme_metabolism,
    "hallmark_hypoxia": hallmark_hypoxia,
    "hallmark_il2_stat5_signaling": hallmark_il2_stat5_signaling,
    "hallmark_il6_jak_stat3_signaling": hallmark_il6_jak_stat3_signaling,
    "hallmark_inflammatory_response": hallmark_inflammatory_response,
    "hallmark_interferon_alpha_response": hallmark_interferon_alpha_response,
    "hallmark_interferon_gamma_response": hallmark_interferon_gamma_response,
    "hallmark_kras_signaling_dn": hallmark_kras_signaling_dn,
    "hallmark_kras_signaling_up": hallmark_kras_signaling_up,
    "hallmark_mitotic_spindle": hallmark_mitotic_spindle,
    "hallmark_mtorc1_signaling": hallmark_mtorc1_signaling,
    "hallmark_myc_targets_v1": hallmark_myc_targets_v1,
    "hallmark_myc_targets_v2": hallmark_myc_targets_v2,
    "hallmark_myogenesis": hallmark_myogenesis,
    "hallmark_notch_signaling": hallmark_notch_signaling,
    "hallmark_oxidative_phosphorylation": hallmark_oxidative_phosphorylation,
    "hallmark_p53_pathway": hallmark_p53_pathway,
    "hallmark_pancreas_beta_cells": hallmark_pancreas_beta_cells,
    "hallmark_peroxisome": hallmark_peroxisome,
    "hallmark_pi3k_akt_mtor_signaling": hallmark_pi3k_akt_mtor_signaling,
    "hallmark_protein_secretion": hallmark_protein_secretion,
    "hallmark_reactive_oxygen_species_pathway": hallmark_reactive_oxygen_species_pathway,
    "hallmark_spermatogenesis": hallmark_spermatogenesis,
    "hallmark_tgf_beta_signaling": hallmark_tgf_beta_signaling,
    "hallmark_tnfa_signaling_via_nfkb": hallmark_tnfa_signaling_via_nfkb,
    "hallmark_unfolded_protein_response": hallmark_unfolded_protein_response,
    "hallmark_uv_response_dn": hallmark_uv_response_dn,
    "hallmark_uv_response_up": hallmark_uv_response_up,
    "hallmark_wnt_beta_catenin_signaling": hallmark_wnt_beta_catenin_signaling,
    "hallmark_xenobiotic_metabolism": hallmark_xenobiotic_metabolism
}

def gene_search_multi(self, gene) -> str:
        #return (gene, scholar2result_llm(self.llm, f"{gene} gene toxicological effects"))
        return (gene, scholar2result_llm(self.llm, f"{gene} gene toxicity"))

class HallmarkGeneAnalyzer(BaseTool):
    name: str = "HallmarkGeneAnalyzer"
    description: str = (
        "Given a ranked list of genes as input, with each entry formatted as [rank].[gene] and separated by a comma, analyzes the genes with respect to the Hallmark gene set."
    )
    llm: BaseLLM = None

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(self, query, **kwargs) -> str:
        # Load user file
        try:

            genes = re.sub(r'\s+', '', query)
            genes = set(genes.split(","))
            genes = {(i.split(".")[0], i.split(".")[1]) for i in genes}
            ranked_genes = sorted(genes, key=lambda x: int(x[0]))
            genes = {i[1] for i in ranked_genes}
            ranked_genes_rank = [int(i[0]) for i in ranked_genes]
            ranked_genes_gene = [i[1] for i in ranked_genes]
            ranked_genes = pd.DataFrame.from_dict({"Rank": ranked_genes_rank, "Gene": ranked_genes_gene})
            
            # Count the number of genes in each Hallmark gene set (knowledge file) that overlap with the user uploaded list.
            #hallmark_genes_result_dict = {}
            hallmark_genes_result_list = []
            for k in hallmark_genes_dict.keys():
                geneset = set(hallmark_genes_dict[k]['Data'])
                intersecting_genes = genes.intersection(geneset)
                overlap = len(intersecting_genes)/len(geneset)*100 # keep only categories with at least 5% overlap
                avg_ranking = ranked_genes[ranked_genes['Gene'].isin(intersecting_genes)]['Rank'].mean()
                hallmark_genes_result_list.append((k, intersecting_genes, len(geneset), overlap, avg_ranking))
            
            # Sort in desc order by percent overlap and take top 5 gene sets
            hallmark_genes_result_list = sorted(hallmark_genes_result_list, key=lambda x: x[3], reverse=True)[:5]

            # Sort by potency ranking (lower avg. potency rank == higher potency)
            hallmark_genes_result_list = sorted(hallmark_genes_result_list, key=lambda x: x[4])

            # Get unique genes so we only have to fetch toxicological data once
            unique_genes = []
            for i in hallmark_genes_result_list:
                for j in i[1]:
                    unique_genes.append(j)
            unique_genes = set(unique_genes)

            # Fetch tox studies for genes concurrently
            """
            proc = []
            res = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                for gene in unique_genes:
                    proc.append(executor.submit(gene_search_multi, self, gene))
            for future in concurrent.futures.as_completed(proc):
                res[future.result()[0]] = future.result()[1]
            """

            proc = []
            res = {}
            
            for gene in unique_genes:
                proc.append(gene_search_multi(self, gene))
            for future in proc:
                res[future[0]] = future[1]
            

            response = ""
            for i in hallmark_genes_result_list:
                response += f"\n\nHallmark gene set: {i[0]}\n\n"
                response += f"Overlapping genes: {i[1]}\n\n"
                response += f"Total genes in set: {i[2]}\n\n"
                response += f"Percent overlap: {i[3]}%\n\n"
                response += f"Average potency ranking: {i[4]}\n\n"
                response += f"Gene toxicological information:\n\n"
                ind = 1
                for j in i[1]:
                    response += f"{ind}. {j}: {res[j]}\n"
            
            return response

        except Exception as e:
            print(e)
            return "There was an error processing the input."
        

    async def _arun(self, query) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("this tool does not support async")