from langchain_core.prompts import ChatPromptTemplate

# EXTRACTION: Be clear about what to do with missing data
extraction_template = ChatPromptTemplate.from_messages([
    ("system", "Extract skills, experience_years, and tools. If a value is missing, use 0 for years and empty lists for skills/tools."),
    ("user", "Resume: {resume_text}")
])

# SCORING: Provide a strict Rubric
scoring_template = ChatPromptTemplate.from_messages([
    ("system", """You are a Recruitment Expert. Score the candidate 0-100 based on the Job Description.
    
    SCORING RUBRIC:
    - 80-100: Strong match. Has Python and most GenAI skills.
    - 40-79: Average match. Has Python/coding but missing GenAI specific tools.
    - 0-39: Weak match. Missing core technical requirements.
    
    IMPORTANT RULES:
    1. 'MySQL' or 'PostgreSQL' counts as 'SQL' proficiency.
    2. You MUST return a score between 0 and 100. Never use a 1-10 scale.
    3. If the candidate is strong, do not give a score lower than 70.
    4. Provide the result ONLY as a structured tool call."""),
    ("user", "Extracted Data: {extracted_data}\n\nJob Description: {jd}")
])