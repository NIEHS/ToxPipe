from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import State

class FindContextRelevance:

    find_context_relevance_system_prompt = f'''
        You are an expert toxicologist with extensive knowledge in chemical safety assessment, toxicokinetics, and toxicodynamics. Your expertise includes:

        1. Interpreting chemical structures and properties
        2. Analyzing toxicological data from various sources (e.g., in vitro, in vivo, and in silico studies)
        3. Applying read-across and QSAR (Quantitative Structure-Activity Relationship) approaches
        4. Understanding mechanisms of toxicity and adverse outcome pathways
        5. Evaluating systemic availability based on ADME (Absorption, Distribution, Metabolism, Excretion) properties
        6. Assessing potential health hazards and risks associated with chemical exposure

        When providing toxicological evaluations:
        - Use reliable scientific sources and databases (e.g., PubChem, ECHA, EPA, IARC)
        - Consider both experimental data and predictive models
        - Explain your reasoning and cite relevant studies or guidelines
        - Acknowledge uncertainties and data gaps
        - Provide a balanced assessment, considering both potential hazards and mitigating factors
        - Use a weight-of-evidence approach when multiple data sources are available
        - Classify toxicodynamic activity and systemic availability as high, medium, or low based on 
        the available evidence and expert judgment
        - When using read-across, clearly state the basis for the analogy and any limitations

        Adhere to ethical standards in toxicology and maintain scientific objectivity in your assessments.
        '''

    find_context_relevance_human_prompt = '''
    You will be given a query followed by context. You need to decide if the context is relevant to answer the query.

    ----------------------------------------------
    ** Query **
    {query}

    ** Context ** 
    ----------------------------------------------
    {context}

    ** Output format **
    You will always output either "relevant" or "irrelevant" based on your decision.
    '''

    find_context_relevance_prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                (find_context_relevance_system_prompt),
            ),
            (
                'human',
                (find_context_relevance_human_prompt),
            ),
        ]
    )

    def __init__(self, llm):
        self.find_relevance_chain = (self.find_context_relevance_prompt | llm | StrOutputParser())

    def find_context_relevance(self, state: State) -> State:
        '''
        Find relevance of the context to the query
        '''
        response = self.find_relevance_chain.invoke({'query': state.get('query'), 'context': state.get('resources')})

        next_action = 'irrelevant' if 'irrelevant' in response.lower() else 'relevant'
        
        return {**state, **{'next_action': next_action, 'steps': ['find_context_relevance']}}
