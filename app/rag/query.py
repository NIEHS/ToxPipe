    
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import State

class Query:

    system_prompt = f'''
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

    user_prompt_with_context = '''
    You will be given a query followed by resources. Answer the query based on the resources provided.

    When providing answer, STRICTLY FOLLOW the rules below:
    1. If the resources do not have information regarding the query, output in following format: "resources_irrelevant"
    2. DO NOT ANSWER the query using information outside the resources.

    ----------------------------------------------
    ** Query **
    {query}

    ** Resources ** 
    ----------------------------------------------
    {resources}
    '''

    user_prompt_without_context = '''
    ----------------------------------------------
    Answer the following query:

    ** Query **
    {query}
    '''
        
    query_with_context_prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                (system_prompt),
            ),
            (
                'human',
                (user_prompt_with_context),
            ),
        ]
    )

    query_without_context_prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                (system_prompt),
            ),
            (
                'human',
                (user_prompt_without_context),
            ),
        ]
    )

    def __init__(self, llm):
        self.query_with_context_chain = (self.query_with_context_prompt | llm | StrOutputParser())
        self.query_without_context_chain = (self.query_without_context_prompt | llm | StrOutputParser())

    def query_with_context(self, state: State) -> State:
        '''
        Get llm response with context
        '''
        
        response = self.query_with_context_chain.invoke({'query': state.get('query'), 'resources': state.get('resources')})

        if 'irrelevant' in response: 
            return {**state, **{'next_action': 'query_without_context', 'steps': ['query_with_context']}}
        
        return {'response': response,
                'next_action': 'end', 
                'steps': ['query_with_context']} 

    def query_without_context(self, state: State) -> State:
        '''
        Get llm response without context
        '''
        
        return {'response': self.query_without_context_chain.invoke({'query': state.get('query')}), 
                'steps': ['query_without_context']}
