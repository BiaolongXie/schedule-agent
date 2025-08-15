import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(
    model=str(os.getenv('MODEL')),
    openai_api_key=str(os.getenv('MODEL_API_KEY')),
    base_url=str(os.getenv('BASE_URL')),
    temperature=0
)