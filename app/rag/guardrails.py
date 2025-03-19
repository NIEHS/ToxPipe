from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from .utils import State

domain = 'either of toxicology, chemicals, chemical compound and biological terms'

class GuardrailsOutput(BaseModel):
    decision: Literal['tox', 'end'] = Field(
        description=f'Decision on whether the question is related to {domain}'
    )

class GuardrailsOutputParser(JsonOutputParser):

    def __init__(self, output_parser=GuardrailsOutput):
        super().__init__(pydantic_object=output_parser)

    def parseOutput(self, data):
        response = self.parse(data.content)
        return response

class Guardrails:

    guardrails_system = f'''
    As an intelligent assistant, your primary objective is to decide whether a given question is related to {domain}. 
    If the question is related to {domain}, output 'tox'. Otherwise, output 'end'.
    To make this decision, assess the content of the question and determine if it refers to {domain}. Provide only the specified output: 'tox' or 'end'.
    '''
    guardrails_prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                guardrails_system,
            ),
            (
                'human',
                ('{question}'),
            ),
        ]
    )

    def __init__(self, llm):
        # Will be used in future
        #self.guardrails_chain = self.guardrails_prompt | llm.with_structured_output(GuardrailsOutput)
        self.guardrails_chain = self.guardrails_prompt | llm | GuardrailsOutputParser().parseOutput


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