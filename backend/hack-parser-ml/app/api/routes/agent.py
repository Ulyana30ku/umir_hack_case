

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter()




class RunRequest(BaseModel):

    query: str
    run_id: Optional[str] = None
    context: Optional[str] = None


class RunResponse(BaseModel):

    run_id: str
    query: str
    status: str
    result: dict = None
    error: str = None




@router.post("/agent/run", response_model=RunResponse)
async def run_agent(request: RunRequest) -> RunResponse:

    run_id = request.run_id or str(uuid.uuid4())
    
    try:
        from app.agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        result = await orchestrator.run(
            query=request.query,
            run_id=run_id,
        )
        
        return RunResponse(
            run_id=run_id,
            query=request.query,
            status=result.get("status", "success"),
            result=result,
        )
    except Exception as e:
        return RunResponse(
            run_id=run_id,
            query=request.query,
            status="failed",
            error=str(e),
        )


@router.get("/agent/run/{run_id}")
async def get_run(run_id: str) -> JSONResponse:

    from app.agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    
    trace = orchestrator.get_trace(run_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )
    
    return JSONResponse(content=trace.model_dump())


@router.get("/agent/run/{run_id}/trace")
async def get_trace(run_id: str) -> JSONResponse:

    from app.agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    
    trace = orchestrator.get_trace(run_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )
    
    return JSONResponse(content=trace.model_dump())




@router.post("/agent/debug/open-url")
async def debug_open_url(url: str) -> dict:
    """Debug endpoint to open URL."""
    from app.browser.session_manager import get_browser_manager
    manager = get_browser_manager()
    
    session_id = str(uuid.uuid4())
    await manager.create_session(session_id)
    result = await manager.navigate(session_id, url)
    
    return {
        "session_id": session_id,
        "result": result,
    }


@router.post("/agent/debug/click")
async def debug_click(session_id: str, selector: str) -> dict:

    from app.browser.browser_service import get_browser_service
    service = get_browser_service()
    
    result = await service.click(session_id, selector)
    return result


@router.post("/agent/debug/type")
async def debug_type(session_id: str, selector: str, text: str) -> dict:

    from app.browser.browser_service import get_browser_service
    service = get_browser_service()
    
    result = await service.type_text(session_id, selector, text)
    return result


@router.get("/agent/debug/get-page-text")
async def debug_get_page_text(session_id: str) -> dict:

    from app.browser.page_service import get_page_service
    service = get_page_service()
    
    result = await service.get_text(session_id)
    return result
