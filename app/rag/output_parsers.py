from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json

class PreRetrievalOutputParserSchema(BaseModel):
    Keywords: list[str] = Field("List of maximum 10 keywords", max_length=10)

class CustomPreRetrievalOutputParser(JsonOutputParser):

    def __init__(self, output_parser=PreRetrievalOutputParserSchema):
        super().__init__(pydantic_object=output_parser)

    def parseOutput(self, data):
        response = self.parse(data.content)
        return response
    
class CustomOutputParser():
    
    def parseOutput(self, data):
        return {'Response':data.content}
