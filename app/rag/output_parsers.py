from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
import json

class PreRetrievalOutputParserSchema(BaseModel):
    Keywords: list[str]

class OutputParserSchema(BaseModel):
    Response: str

class CustomOutputParser(JsonOutputParser):

    def __init__(self, output_parser=OutputParserSchema):
        super().__init__(pydantic_object=output_parser)

    def parseKWOutput(self, data):
        try:
            response = self.parse(data.content)
        except Exception as exp:
            print(str(exp))
            response = json.dumps({'Keywords':[data.content]})
        return response
    
    def parseResOutput(self, data):
        try:
            response = self.parse(data.content)
        except Exception as exp:
            print(str(exp))
            response = json.dumps({'Response':data.content})
        return response['Response']