from __future__ import annotations
from typing import Optional
from langchain_community.vectorstores import FAISS
from pathlib import Path
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
import os
import traceback
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # Load environment variables from .env file
hugging_face_token = os.getenv("HUGGINGFACE_TOKEN")
gemini_api_key = os.getenv("GEMINI_API_KEY")
BASE_DIR = Path(__file__).resolve().parent
FAISS_PATH = str(BASE_DIR/ "medical_rag_embeddings")

_rag_chain: Optional[Runnable] = None
_rag_retriever: Optional[BaseRetriever] = None


def init_rag():
    """
    Initialize the RAG chain and retriever.
    """
    global _rag_chain, _rag_retriever
    # Create embeddings using HuggingFace
    try:
        print("loading embeddings...")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(model_name = model_name, model_kwargs={"device": "cpu", "token":hugging_face_token}) 
        # Retrieve embeddings
        print("loading vectorstore...")
        vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)

        # Create a retriever from the vectorstore
        print("creating retriever")
        retriever = vectorstore.as_retriever(
        search_type="mmr",  
        search_kwargs = {'k':5,
                        "fetch_k": 20}
                        )
        
        print("loading LLM...")
        llm = GoogleGenerativeAI(
        model= "gemini-2.5-flash",
        temperature=0,
        api_key = gemini_api_key
                )
        
        # create prompt template for the RAG model
        prompt = PromptTemplate.from_template("""
        You are Smart Pocket Doctor.

        Use ONLY the provided context to answer.

        If the answer is not in the context, say:
        "I could not find enough information in the medical database. Kindly consult a healthcare professional for accurate guidance."

        Context:
        {context}

        Question:
        {question}

        Answer:
        """) 

        rag_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
        )


        _rag_chain = rag_chain
        _rag_retriever = retriever

        print("RAG chain and retriever initialized successfully.")
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError("Failed to initialize RAG chain and retriever.") 

def get_rag_chain() -> Runnable:
    if _rag_chain is None:
        raise RuntimeError("RAG chain is not initialized. Call init_rag() first.")
    return _rag_chain

def get_rag_retriever() -> BaseRetriever:
    if _rag_retriever is None:
        raise RuntimeError("RAG retriever is not initialized. Call init_rag() first.")
    return _rag_retriever

# from __future__ import annotations
# from typing import Optional
# from pathlib import Path
# from langchain_community.vectorstores import FAISS
# from langchain_core.runnables import Runnable, RunnablePassthrough
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import PromptTemplate
# from langchain_google_genai import GoogleGenerativeAI
# from langchain_core.retrievers import BaseRetriever
# from langchain_huggingface import HuggingFaceEmbeddings
# import os
# import traceback
# from dotenv import load_dotenv, find_dotenv

# load_dotenv(find_dotenv())  # walks up to find .env wherever it lives

# hugging_face_token = os.getenv("HUGGINGFACE_TOKEN")
# gemini_api_key     = os.getenv("GEMINI_API_KEY")

# # FAISS index is stored relative to this file's location
# BASE_DIR   = Path(__file__).resolve().parent.parent.parent  # → backend/
# FAISS_PATH = str(BASE_DIR / "medical_rag_embeddings")

# _rag_chain:     Optional[Runnable]      = None
# _rag_retriever: Optional[BaseRetriever] = None


# def init_rag():
#     global _rag_chain, _rag_retriever

#     # ── Startup diagnostics ──────────────────────────────────────────────
#     print(f"[RAG] .env found at     : {find_dotenv()}")
#     print(f"[RAG] FAISS path        : {FAISS_PATH}")
#     print(f"[RAG] FAISS path exists : {Path(FAISS_PATH).exists()}")
#     print(f"[RAG] HF token loaded   : {'yes' if hugging_face_token else 'NO - missing'}")
#     print(f"[RAG] Gemini key loaded : {'yes' if gemini_api_key else 'NO - missing'}")
#     # ────────────────────────────────────────────────────────────────────

#     try:
#         print("[RAG] Loading embeddings...")
#         embeddings = HuggingFaceEmbeddings(
#             model_name="sentence-transformers/all-MiniLM-L6-v2",
#             model_kwargs={"device": "cpu", "token": hugging_face_token},
#         )

#         print("[RAG] Loading vectorstore...")
#         vectorstore = FAISS.load_local(
#             FAISS_PATH,
#             embeddings,
#             allow_dangerous_deserialization=True,
#         )

#         print("[RAG] Creating retriever...")
#         retriever = vectorstore.as_retriever(
#             search_type="mmr",
#             search_kwargs={"k": 5, "fetch_k": 20},
#         )

#         print("[RAG] Loading LLM...")
#         llm = GoogleGenerativeAI(
#             model="gemini-1.5-flash",   # gemini-2.5-flash is not publicly available yet
#             temperature=0,
#             api_key=gemini_api_key,
#         )

#         prompt = PromptTemplate.from_template("""
#             You are Smart Pocket Doctor.

#             Use ONLY the provided context to answer.

#             If the answer is not in the context, say:
#             "I could not find enough information in the medical database. Kindly consult a healthcare professional for accurate guidance."

# Context:
# {context}

# Question:
# {question}

# Answer:
# """)

#         rag_chain = (
#             {"context": retriever, "question": RunnablePassthrough()}
#             | prompt
#             | llm
#             | StrOutputParser()
#         )

#         _rag_chain     = rag_chain
#         _rag_retriever = retriever
#         print("[RAG] Initialized successfully.")

#     except Exception:
#         traceback.print_exc()   # prints the REAL error with line number
#         raise RuntimeError("Failed to initialize RAG chain and retriever.")


# def get_rag_chain() -> Runnable:
#     if _rag_chain is None:
#         raise RuntimeError("RAG chain not initialized. Call init_rag() first.")
#     return _rag_chain


# def get_rag_retriever() -> BaseRetriever:
#     if _rag_retriever is None:
#         raise RuntimeError("RAG retriever not initialized. Call init_rag() first.")
#     return _rag_retriever