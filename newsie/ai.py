from typing import List, Sequence
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.schema import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)
from langchain.prompts import PromptTemplate
from langchain_community.document_transformers.openai_functions import create_metadata_tagger

# SUMMARIZATION_AI_MODEL = "gpt-4-1106-preview"
SUMMARIZATION_AI_MODEL = "gpt-3.5-turbo-1106"
CHUNK_SIZE = 4000
MAX_TOKENS = 3000


def split_text_to_docs(text: str, chunk_size: int = CHUNK_SIZE) -> List[Document]:
    """Split the text into documents."""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=0,
    )
    return text_splitter.create_documents([text])


def generate_summary(
        text: str,
        model: str = SUMMARIZATION_AI_MODEL,
        chunk_size: int = CHUNK_SIZE,
        max_tokens: int = MAX_TOKENS,
):
    docs = split_text_to_docs(text)

    llm = ChatOpenAI(temperature=0, model_name=model)
    # Map
    map_template = """The following is a new article from the Utah newspaper, the Salt Lake Tribune
    {docs}
    Based on this set of chunks, identify the main themes with as much context as possible. 
    Authors and previous works cited should only be identified as a theme if it is imperative to the understanding 
    of the news article, otherwise just focus on the article's content.
    Helpful Answer:"""
    map_prompt = PromptTemplate.from_template(map_template)
    llm_chain = LLMChain(llm=llm, prompt=map_prompt)

    # Define StuffDocumentsChain
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="docs")

    summary = stuff_chain.invoke(docs)
    return summary


NEWS_CATEGORIES = [
    "local",
    "national",
    "international",
    "business",
    "technology",
    "science",
    "health",
    "sports",
    "entertainment",
    "arts",
    "lifestyle",
    "travel",
    "education",
    "politics",
    "environment",
    "opinion",
    "weather",
    "crime",
    "economy",
    "social issues"
]

METADATA_SCHEMA = {
    "properties": {
        "article_title": {"type": "string"},
        "author": {"type": "string"},
        "tone": {"type": "string", "enum": ["mostly negative", "negative", "neutral", "positive", "mostly positive"]},
        "news_category": {"type": "string", "enum": NEWS_CATEGORIES}
    },
    "required": ["article_title", "author"]
}


def generate_metadata(
        text: str,
        model: str = SUMMARIZATION_AI_MODEL
) -> Sequence[Document]:
    llm = ChatOpenAI(temperature=0, model=model)
    document_transformer = create_metadata_tagger(metadata_schema=METADATA_SCHEMA, llm=llm)
    docs = split_text_to_docs(text)
    enhanced_documents = document_transformer.transform_documents(docs)
    return enhanced_documents
