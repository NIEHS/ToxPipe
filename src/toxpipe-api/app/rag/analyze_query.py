from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from pydantic import BaseModel, Field
from .utils import Config, State, setPrompt

# ---------------------------------------------------------------------------
class AnalyzeQuerySchema(BaseModel):
    '''
    Represents the list of keyphrases extracted from user query to get context on.
    '''
    keyphrases: list[str] = Field(f'List of maximum {Config.MAX_KEYPHRASES} keywords', max_length=Config.MAX_KEYPHRASES)

# ---------------------------------------------------------------------------
class AnalyzeQuery:

    # ---------------------------------------------------------------------------
    analyze_query_system_prompt = (f'''
        You will be given a query. Analyze the query and find a list of independent 'keyphrases' on which you need information to answer the query. Always follow the rules below,

        <Instructions>
        - List maximum of {Config.MAX_KEYPHRASES} key phrases. THE LIST MUST NOT BE MORE THAN {Config.MAX_KEYPHRASES}.
        - Each key phrase must be relevant to the query.
        - Each key phrase must be semantically independent of the query.
        </Instructions>
        ''')

    # ---------------------------------------------------------------------------
    analyze_query_human_prompt = '''Given a query text, find a list of independent 'keyphrases' on which you need information to answer the query.

        <Query>
        {query}
        </Query>

        ----------------------------------------------
        <Output format>
                                
        {format_instructions_example}

        - The answer must be in JSON format within `json` tags.
        </Output format>
        '''

    # ---------------------------------------------------------------------------
    def __init__(self, llm):
        
        parser = OutputFixingParser.from_llm(parser=PydanticOutputParser(pydantic_object=AnalyzeQuerySchema), llm=llm, max_retries=Config.RETRY_COUNTER)
        analyze_query_prompt = setPrompt(system_prompt=self.analyze_query_system_prompt,
                                         human_prompt=self.analyze_query_human_prompt).partial(format_instructions_example=parser.get_format_instructions())
        self.analyze_query_chain = analyze_query_prompt | llm | parser

    # ---------------------------------------------------------------------------
    def analyze_query(self, state: State) -> State:
        '''
        Extracts keyphrases from user query
        '''
        
        keyphrases = dict(self.analyze_query_chain.invoke({'query': state.get('query')}))['keyphrases']                
        return {'keyphrases': [state.get('query')] + keyphrases, 'steps': ['Analyze query']}