from typing import List
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.schema import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.prompts import PromptTemplate


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

    return stuff_chain.invoke(docs)
