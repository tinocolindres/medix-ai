"""
Medix AI — SESAL RAG Service
Retrieval-Augmented Generation con Normas de la Secretaría de Salud de Honduras.
Responde preguntas clínicas basándose en protocolos oficiales hondureños.
"""
import os
from pathlib import Path
from typing import Optional
import anthropic

from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# ── ChromaDB (lazy import para no bloquear startup) ───────────────────────────
_chroma_client = None
_collection = None


def get_chroma_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        _collection = _chroma_client.get_or_create_collection(
            name=settings.SESAL_COLLECTION,
            metadata={"description": "Normas SESAL Honduras — Guías y Protocolos Clínicos"}
        )
    return _collection


async def ingest_sesal_pdf(pdf_path: str, document_name: str) -> dict:
    """
    Ingesta un PDF de SESAL al vector store.
    Llamar una vez por cada guía clínica nueva.
    
    Uso desde CLI: python -m app.services.sesal_rag ingest /path/to/norma.pdf "Manejo Dengue 2024"
    """
    import pdfplumber
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    collection = get_chroma_collection()

    chunks = []
    chunk_size = 800  # caracteres por chunk

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"

    # Split en chunks con overlap
    words = full_text.split()
    current_chunk = []
    current_len = 0

    for word in words:
        current_chunk.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-50:]  # 50 palabras de overlap
            current_len = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Vectorizar e insertar
    embeddings = model.encode(chunks).tolist()
    ids = [f"{document_name}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": document_name, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas)

    return {"status": "ok", "chunks_ingested": len(chunks), "document": document_name}


async def query_sesal_context(query: str, n_results: int = 4) -> list[str]:
    """
    Busca los chunks más relevantes de las Normas SESAL para una query.
    Retorna lista de textos relevantes para inyectar al prompt.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        collection = get_chroma_collection()

        if collection.count() == 0:
            return []  # Sin documentos aún

        query_embedding = model.encode([query])[0].tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
        )
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []  # RAG opcional — no bloquear si no está disponible


async def generate_sesal_response(
    query: str,
    user_role: str = "medico_general",
) -> dict:
    """
    Genera respuesta clínica con RAG de Normas SESAL.
    Si hay contexto relevante, lo inyecta al prompt de Claude.
    """
    relevant_chunks = await query_sesal_context(query)

    if relevant_chunks:
        context_text = "\n\n---\n".join(relevant_chunks)
        rag_prompt = (
            f"Basándote EXCLUSIVAMENTE en los siguientes protocolos oficiales de la "
            f"Secretaría de Salud de Honduras (SESAL), responde la pregunta clínica:\n\n"
            f"[NORMAS SESAL]:\n{context_text}\n\n"
            f"[PREGUNTA CLÍNICA]: {query}\n\n"
            f"Si la información no está en las normas proporcionadas, indícalo explícitamente "
            f"y responde con conocimiento general marcado como '[Conocimiento General - verificar con SESAL]'."
        )
        source_note = "Basado en Normas SESAL Honduras"
    else:
        rag_prompt = (
            f"{query}\n\n"
            f"*Nota: Base de datos SESAL en construcción. "
            f"Respondiendo con guías OPS/OMS internacionales.*"
        )
        source_note = "Guías OPS/OMS (SESAL no disponible aún)"

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
        system=(
            "Eres Medix AI, experto en protocolos clínicos de Honduras. "
            "Responde con precisión, usa formato Markdown con bullet points. "
            "Sé específico sobre nombres comerciales y genéricos disponibles en Honduras."
        ),
        messages=[{"role": "user", "content": rag_prompt}],
    )

    return {
        "response": response.content[0].text,
        "source": source_note,
        "chunks_used": len(relevant_chunks),
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
    }
