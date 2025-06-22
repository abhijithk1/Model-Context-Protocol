# from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

provider = os.getenv("LLM_PROVIDER", "gemini")

LLM_LIST = {
    # "openai" : ChatOpenAI(model_name="gpt-4", temperature=0.0),
    "gemini" : ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    )
}


llm = LLM_LIST.get(provider)

if llm is None:
    logger.warning(f"LLM Provider '{provider}' not found in LLM_LIST. Using default model 'openai'.")
    llm = LLM_LIST["gemini"]