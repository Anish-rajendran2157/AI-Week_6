from fastapi import APIRouter, HTTPException
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    try:
        # Every answered query writes one trace; the id comes back so a reported
        # bad answer can be looked up later.
        result = await rag_service.answer_query(request.query, channel=request.channel)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
