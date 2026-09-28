"""DocSage — API de perguntas e respostas sobre documentos (RAG)."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.embeddings import warmup
from app.ingestion import ingest_document
from app.llm import answer_question
from app.models import Conversation, Document, Message
from app.retrieval import search_chunks
from app.schemas import AskRequest, AskResponse, Citation, DocumentOut

# Tipos de arquivo aceitos no upload.
ALLOWED_TYPES = {"application/pdf", "text/plain"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas (a extensão pgvector já foi habilitada pelo db/init.sql).
    Base.metadata.create_all(bind=engine)
    # "Aquece" o modelo de embeddings para a 1ª requisição não ficar lenta.
    warmup()
    yield


app = FastAPI(title="DocSage", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    """Verificação simples de que a app está no ar."""
    return {"status": "ok"}


@app.post("/documents", response_model=DocumentOut, status_code=201)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Recebe um PDF/TXT, processa e indexa (ingestão)."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Apenas arquivos PDF ou TXT são aceitos.")

    content = file.file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Arquivo acima do limite de {settings.max_upload_mb} MB.")

    try:
        document = ingest_document(
            db,
            filename=file.filename,
            content_type=file.content_type,
            content=content,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

    return document


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    """Lista os documentos já indexados, do mais recente ao mais antigo."""
    return db.query(Document).order_by(Document.created_at.desc()).all()


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    """Responde uma pergunta com base nos documentos indexados (RAG)."""
    question = payload.question.strip()
    if not question:
        raise HTTPException(400, "A pergunta não pode estar vazia.")

    # 1) Busca semântica pelos trechos mais relevantes.
    chunks = search_chunks(db, question, settings.top_k)
    if not chunks:
        raise HTTPException(404, "Nenhum documento indexado ainda. Faça upload primeiro.")

    # 2) Geração da resposta com o LLM, usando só esses trechos.
    answer = answer_question(question, chunks)

    # 3) Registra a conversa (cria uma nova se não veio um id).
    conversation = None
    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
    if conversation is None:
        conversation = Conversation(title=question[:80])
        db.add(conversation)
        db.flush()

    db.add(Message(conversation_id=conversation.id, role="user", content=question))
    db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
    db.commit()

    # 4) Monta as citações (mesma ordem/numeração usada no prompt).
    citations = [
        Citation(
            document_id=c.document_id,
            filename=c.document.filename,
            chunk_index=c.chunk_index,
            snippet=c.content[:200],
        )
        for c in chunks
    ]
    return AskResponse(answer=answer, citations=citations, conversation_id=conversation.id)
