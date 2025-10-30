    
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain.output_parsers import OutputFixingParser
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import END
from .utils import Config, State, setPrompt

class QueryWithContextSchema(BaseModel):
    '''
    Represents if the provided resources are relevant to the provided query and if so, respond to the user query.
    '''
    decision: Literal["relevant", "irrelevant"] = Field(
        description="Decision on whether the provided resources are relevant and useful to answer the query"
    )
    response: str = Field(
        description="The appropriate answer to the query based on the provided resources" 
    )

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

    human_prompt_with_context = ''' 
    ----------------------------------------------
    <Query>
    {query}
    </Query>

    ----------------------------------------------
    <Resources>
    {resources}
    </Resources>

    ----------------------------------------------
    <Instructions>
    You are given a query followed by resources above. You will STRICTLY follow the two steps below.
    1. Decide if the resources are 'relevant' to answer the query. Answer either 'relevant' or 'irrelevant'.
    2. If your answer in step 1 is 'relevant', answer the query based on the resources. DO NOT ANSWER from your training data.
    </Instructions>
    
    ----------------------------------------------
    <Output format>
                            
    {format_instructions_example}

    - The answer must be in JSON format within `json` tags.
    </Output format>
    '''

    human_prompt_without_context = '''
    ----------------------------------------------
    Answer the following query:

    **Query**
    ----------------------------------------------
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
                (human_prompt_with_context),
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
                (human_prompt_without_context),
            ),
        ]
    )

    def __init__(self, llm):
        parser = OutputFixingParser.from_llm(parser=PydanticOutputParser(pydantic_object=QueryWithContextSchema), llm=llm, max_retries=Config.RETRY_COUNTER)
        query_with_context_prompt = setPrompt(system_prompt=self.system_prompt,
                                         human_prompt=self.human_prompt_with_context).partial(format_instructions_example=parser.get_format_instructions())
        self.query_with_context_chain = query_with_context_prompt | llm | parser
        self.query_without_context_chain = self.query_without_context_prompt | llm | StrOutputParser()
        

    def query_with_context(self, state: State) -> State:
        '''
        Get llm response with context
        '''
        response = dict(self.query_with_context_chain.invoke({'query': state.get('query'), 'resources': state.get('resources')}))
        
        if response['decision'] == 'relevant': 
            return {'response': response['response'], 
                    'next_action': END, 
                    'steps': ['query_with_context']}

        return {'response': response['response'],
                'next_action': 'query_without_context',
                'steps': ['query_with_context']} 

    def query_without_context(self, state: State) -> State:
        '''
        Get llm response without context
        '''

        response = self.query_without_context_chain.invoke({'query': state.get('query')}) 
        
        return {'response': response, 
                'steps': ['query_without_context']}
