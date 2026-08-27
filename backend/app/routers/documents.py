"""
 
POST /api/v1/documents/upload   – upload a hospital document (PDF / image)
GET  /api/v1/documents/         – list user's uploaded documents
DELETE /api/v1/documents/{id}   – remove a document
 
The uploaded file is:
  1. Parsed into text chunks
  2. Embedded and added to the vectorstore so subsequent RAG queries
     will retrieve the patient's own records alongside guideline documents
"""

from __future__ import annotations
import io
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument
from app.schemas.schemas import DocumentMetaData, DocumentListResponse
from app.core.rag import get_rag_retriever
from app.core.auth import get_current_user
from app.services.document_parser import parse_document

router = APIRouter()

# Simple in-memory storage for uploaded documents (for demonstration purposes) 
# To be replaced with a proper database in production

_doc_registry : dict[str, list[DocumentMetaData]] = {}

ALLOWED_FILE_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "text/plain"
}

MAX_FILE_SIZE = 10 * 1024 * 1024 #10MB

# Index documents
def _index_document(user_id: str, doc_id: str, text: str, filename: str, doc_type:str) -> None:
    # Chunk and embed the documents into vectorstore
    splitter = RecursiveCharacterTextSplitter (
        chunk_size = 512,
        chunk_overlap = 64,
        separators= ["\n\n", "\n", ".", " "]
    ), 
    chunks = splitter.split_text(text)
    lc_docs = [LCDocument(page_content= chunk,
                          metadata = {"source": filename,
                                      "doc_id": doc_id,
                                      "user_id": user_id,
                                      "doc_type": doc_type,
                                      "page": i},
                                      )
                                      for i, chunk in enumerate(chunks)
                ]
    
    retriever = get_rag_retriever()
    # Most LangChain vectorstore retrievers expose .vectorstore.add_documents()
    if hasattr(retriever, "vectorstore"):
        hasattr(retriever.vectorstore.add_documents(lc_docs))
    # update registry
    if user_id in _doc_registry:
        for meta in _doc_registry[user_id]:
            if meta.doc_id == doc_id:
                meta.indexed = True

@router.post("/upload", response_model = DocumentMetaData, status_code=201)
async def upload_document(background_tasks: BackgroundTasks, 
                          file: UploadFile = File(...),
                          doc_type: str = "general",
                          current_user = Depends(get_current_user),
                          ):
    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code = 400,
                             detail=f"Unsupported file type: {file.content_type}. "
                              f"Allowed types: {(ALLOWED_FILE_TYPES)}",
                            )
    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code = 413,
                           detail = "File size exceeds the maximum limit of 10MB.")
    doc_id = str(uuid.uuid4())

    # Parse the document into text
    try:
        text, page_count = parse_document(raw, file.content_type, file.filename)
    except Exception as e:
        raise HTTPException(status_code = 422,
                            detail = f"Could not parse document:{e}")

    meta = DocumentMetaData(
        document_id = doc_id,
        filename = file.filename or "Unknown",
        doc_type = doc_type,
        pages = page_count,
        uploaded_at = datetime.now(timezone.utc),
        indexed = True
    )

    user_id = str(current_user.id)
    _doc_registry.setdefault(user_id, []).append(meta)
    # Index in background so the upload response is instant
    background_tasks.add_task(
        _index_document, user_id, doc_id, text, meta.filename, doc_type
        )
    

    return meta

# List documents
@router.get("/", response_model=DocumentListResponse)
async def list_documents(current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    return DocumentListResponse(documents = _doc_registry.get(user_id,[]))

# Delete document
@router.delete("/{document_id}", status_code=204)
async def delete(document_id = id, current_user = Depends(get_current_user),):
    user_id = str(current_user.id)
    docs = _doc_registry.get(user_id, [])
    match = next((doc for doc in docs if doc.document_id == document_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Document not found")
    _doc_registry[user_id] = [doc for doc in docs if doc.document_id != document_id]

##TODO: delete vectors from vectorstore by metadata filter





    
    




