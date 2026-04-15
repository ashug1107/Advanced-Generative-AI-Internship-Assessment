import os
from typing import List, TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from prompts.templates import extraction_template, scoring_template

load_dotenv()

# 1. Define TWO Schemas
class ExtractedData(TypedDict):
    skills: List[str]
    experience_years: float
    tools: List[str]

class ScreeningReport(TypedDict):
    score: int
    explanation: str

# Add a prompt hint to the LLM itself
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0, # Keep it at 0 for consistency
    groq_api_key=os.getenv("GROQ_API_KEY")
).bind(tool_choice="required") # This forces the model to use the tool correctly

# 3. Create TWO Structured LLMs
# This forces the model to stick to specific outputs for each step
extraction_llm = llm.with_structured_output(ExtractedData)
scoring_llm = llm.with_structured_output(ScreeningReport)

# 4. Orchestration
extraction_chain = extraction_template | extraction_llm
scoring_chain = scoring_template | scoring_llm