from .utils import State
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

class UserQueryKeywordsSchema(BaseModel):
    '''
    Represents the list of keyphrases extracted from user query
    to get context on.
    '''
    keyphrases: list[str] = Field('List of maximum 10 keywords', max_length=10)

class AnalyzeQueryOutputParser(JsonOutputParser):

    def __init__(self, output_parser=UserQueryKeywordsSchema):
        super().__init__(pydantic_object=output_parser)

    def parseOutput(self, data):
        response = self.parse(data.content)
        return response

class AnalyzeQuery:

    analyze_query_system_prompt = '''
        You will be given a query. Analyze the query and find a list of independent 'keyphrases' on which you need information to answer the query. Always follow the rules below

        ** Rules **
        - List maximum of 10 key phrases. THE LIST MUST NOT BE MORE THAN 10.
        - Answer the query in the JSON format

        ```json
        {{
            "keyphrases": ["keyphrase 1", "keyphrase 2", "keyphrase 3", ...]
        }}
        ```
        '''

    analyze_query_user_prompt = '''Given a query text, find a list of independent 'keyphrases' on which you need information to answer the query.

        ** Query **
        {query}
        '''

    analyze_query_prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                analyze_query_system_prompt,
            ),
            (
                'human',
                analyze_query_user_prompt,
            ),
        ]
    )

    def __init__(self, llm):
        # Will be used in future
        # self.analyze_query_chain = analyze_query_prompt | llm.with_structured_output(UserQueryKeywordsSchema)
        self.analyze_query_chain = self.analyze_query_prompt | llm | AnalyzeQueryOutputParser().parseOutput

    def analyze_query(self, state: State) -> State:
        '''
        Extracts keyphrases from user query
        '''

        keyphrases = self.analyze_query_chain.invoke(
            {
                'query': state.get('query')
            }
        )
        return {**keyphrases, **{'steps': ['analyze_query']}}