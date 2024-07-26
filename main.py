# -*- coding: utf-8 -*-
import os
from datetime import date
from typing import List, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="ToxPipe API",
    description="The ToxPipe API assists in finding relevant toxicological data"
    "for performing agentic queries.",
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}