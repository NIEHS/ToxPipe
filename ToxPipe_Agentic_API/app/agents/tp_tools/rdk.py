from langchain.tools import BaseTool
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import requests
import os
import urllib.parse
from dotenv import load_dotenv
load_dotenv('../../../.config/.env')
from .utils import *


class MolSimilarity(BaseTool):
    name: str = "MolSimilarity"
    description: str = (
        "Input two molecule SMILES (separated by '.'), returns Tanimoto similarity."
    )

    def __init__(self):
        super().__init__()

    def _run(self, smiles_pair: str, **kwargs) -> str:
        smi_list = smiles_pair.split(".")
        if len(smi_list) != 2:
            return "Input error, please input two smiles strings separated by '.'"
        else:
            smiles1, smiles2 = smi_list

        similarity = tanimoto(smiles1, smiles2)

        if isinstance(similarity, str):
            return similarity

        sim_score = {
            0.9: "very similar",
            0.8: "similar",
            0.7: "somewhat similar",
            0.6: "not very similar",
            0: "not similar",
        }
        if similarity == 1:
            return "Error: Input Molecules Are Identical"
        else:
            val = sim_score[
                max(key for key in sim_score.keys() if key <= round(similarity, 1))
            ]
            message = f"The Tanimoto similarity between {smiles1} and {smiles2} is {round(similarity, 4)},\
            indicating that the two molecules are {val} (source: calculated with RDKit)."
        return message

    async def _arun(self, smiles_pair: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


class SMILES2Weight(BaseTool):
    name: str = "SMILES2Weight"
    description: str = "Input DTXSID, returns molecular weight."

    def __init__(
        self,
    ):
        super().__init__()

    def _run(self, smiles: str, **kwargs) -> str:
        mol = Chem.MolFromSmiles(smiles.rstrip())
        if mol is None:
            return "Invalid SMILES string"
        mol_weight = rdMolDescriptors.CalcExactMolWt(mol)
        return f"{mol_weight} (source: calculated with RDKit)."

    async def _arun(self, smiles: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


class FuncGroups(BaseTool):
    name: str = "FunctionalGroups"
    description: str = "Input SMILES, return list of functional groups in the molecule."
    dict_fgs: dict = None

    def __init__(
        self,
    ):
        super().__init__()

        # List obtained from https://github.com/rdkit/rdkit/blob/master/Data/FunctionalGroups.txt
        self.dict_fgs = {
            "furan": "o1cccc1",
            "aldehydes": " [CX3H1](=O)[#6]",
            "esters": " [#6][CX3](=O)[OX2H0][#6]",
            "ketones": " [#6][CX3](=O)[#6]",
            "amides": " C(=O)-N",
            "thiol groups": " [SH]",
            "alcohol groups": " [OH]",
            "methylamide": "*-[N;D2]-[C;D3](=O)-[C;D1;H3]",
            "carboxylic acids": "*-C(=O)[O;D1]",
            "carbonyl methylester": "*-C(=O)[O;D2]-[C;D1;H3]",
            "terminal aldehyde": "*-C(=O)-[C;D1]",
            "amide": "*-C(=O)-[N;D1]",
            "carbonyl methyl": "*-C(=O)-[C;D1;H3]",
            "isocyanate": "*-[N;D2]=[C;D2]=[O;D1]",
            "isothiocyanate": "*-[N;D2]=[C;D2]=[S;D1]",
            "nitro": "*-[N;D3](=[O;D1])[O;D1]",
            "nitroso": "*-[N;R0]=[O;D1]",
            "oximes": "*=[N;R0]-[O;D1]",
            "Imines": "*-[N;R0]=[C;D1;H2]",
            "terminal azo": "*-[N;D2]=[N;D2]-[C;D1;H3]",
            "hydrazines": "*-[N;D2]=[N;D1]",
            "diazo": "*-[N;D2]#[N;D1]",
            "cyano": "*-[C;D2]#[N;D1]",
            "primary sulfonamide": "*-[S;D4](=[O;D1])(=[O;D1])-[N;D1]",
            "methyl sulfonamide": "*-[N;D2]-[S;D4](=[O;D1])(=[O;D1])-[C;D1;H3]",
            "sulfonic acid": "*-[S;D4](=O)(=O)-[O;D1]",
            "methyl ester sulfonyl": "*-[S;D4](=O)(=O)-[O;D2]-[C;D1;H3]",
            "methyl sulfonyl": "*-[S;D4](=O)(=O)-[C;D1;H3]",
            "sulfonyl chloride": "*-[S;D4](=O)(=O)-[Cl]",
            "methyl sulfinyl": "*-[S;D3](=O)-[C;D1]",
            "methyl thio": "*-[S;D2]-[C;D1;H3]",
            "thiols": "*-[S;D1]",
            "thio carbonyls": "*=[S;D1]",
            "halogens": "*-[#9,#17,#35,#53]",
            "t-butyl": "*-[C;D4]([C;D1])([C;D1])-[C;D1]",
            "tri fluoromethyl": "*-[C;D4](F)(F)F",
            "acetylenes": "*-[C;D2]#[C;D1;H]",
            "cyclopropyl": "*-[C;D3]1-[C;D2]-[C;D2]1",
            "ethoxy": "*-[O;D2]-[C;D2]-[C;D1;H3]",
            "methoxy": "*-[O;D2]-[C;D1;H3]",
            "side-chain hydroxyls": "*-[O;D1]",
            "ketones": "*=[O;D1]",
            "primary amines": "*-[N;D1]",
            "nitriles": "*#[N;D1]",
        }

    def _is_fg_in_mol(self, mol, fg):
        fgmol = Chem.MolFromSmarts(fg)
        mol = Chem.MolFromSmiles(mol.strip())
        return len(Chem.Mol.GetSubstructMatches(mol, fgmol, uniquify=True)) > 0

    def _run(self, dtxsid: str, **kwargs) -> str:
        """
        Input a chemical DTXSID, returns a list of functional groups identified by their common name (in natural language).
        """

        dtxsid = dtxsid.rstrip()

        # Convert DTXSID to SMILES
        res = requests.get(
            f"{os.environ.get('CBT_API_ENDPOINT')}/dtxsid2smiles?dtxsid={urllib.parse.quote_plus(dtxsid)}",
            headers={'Authorization': f"Key {os.environ.get('CONNECT_API_KEY')}"}
        )
        res = res.json()
        smiles = res[0]["canonical_smiles"]

        try:
            fgs_in_molec = [
                name
                for name, fg in self.dict_fgs.items()
                if self._is_fg_in_mol(smiles, fg)
            ]
            if len(fgs_in_molec) > 1:
                return f"This molecule contains {', '.join(fgs_in_molec[:-1])}, and {fgs_in_molec[-1]} (source: calculated with RDKit)."
            else:
                return f"This molecule contains {fgs_in_molec[0]} (source: calculated with RDKit)."
        except:
            return "Wrong argument. Please input a valid molecular SMILES."

    async def _arun(self, smiles: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()
