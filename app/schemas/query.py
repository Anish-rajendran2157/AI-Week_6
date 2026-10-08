from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    channel: str = "api"

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    trace_id: Optional[str] = None
