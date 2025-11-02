from typing import Literal
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from pydantic import BaseModel, Field
from .utils import State, Config, setPrompt

domain = 'either of toxicology, chemicals, chemical compound and biological terms'

class GuardrailsSchema(BaseModel):
    decision: Literal['tox', 'end'] = Field(
        description=f'Decision on whether the question is related to {domain}'
    )

class Guardrails:

    system_prompt = f'''
    As an intelligent assistant, your primary objective is to decide whether a given question is related to {domain}. 
    If the question is related to {domain}, output 'tox'. Otherwise, output 'end'.
    To make this decision, assess the content of the question and determine if it refers to {domain}. Provide only the specified output: 'tox' or 'end'.
    '''

    human_prompt = '''
    <Question>
    {question}
    </Question>

    ----------------------------------------------
    <Output format>
                            
    {format_instructions_example}

    - The answer must be in JSON format within `json` tags.
    </Output format>
    '''

    def __init__(self, llm):
        parser = OutputFixingParser.from_llm(parser=PydanticOutputParser(pydantic_object=GuardrailsSchema), llm=llm, max_retries=Config.RETRY_COUNTER)
        guardrails_prompt = setPrompt(system_prompt=self.system_prompt, 
                                      human_prompt=self.human_prompt).partial(format_instructions_example=parser.get_format_instructions())
        self.guardrails_chain = guardrails_prompt | llm | parser

    def guardrails(self, state: State) -> State:
        '''
        Decides if the question is related to either of toxicology, chemicals and biological terms.
        '''
        guardrails_output = self.guardrails_chain.invoke({'question': state.get('question')})
        response = None
        if guardrails_output.decision == 'end':
            response = f'This questions is not about {domain}. Therefore I cannot answer this question.'
        return {
            'next_action': guardrails_output.decision,
            'response': response,
            'steps': ['guardrail'],
        }