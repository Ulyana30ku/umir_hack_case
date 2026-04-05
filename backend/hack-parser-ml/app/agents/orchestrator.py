"""Agent Orchestrator - coordinates query parsing, planning, and execution."""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.mcp.models import (
    ExecutionContext,
    ExecutionPlan,
    ExecutionStep,
    SafetyConfig,
    ToolResult,
    BrowserState,
)
from app.mcp.server import get_mcp_server, MCPServer
from app.agents.parser import ParsedUserQuery, get_query_parser
from app.agents.planner import ExecutionPlanner, get_planner
from app.schemas.trace import AgentRunTrace, AgentTraceStep
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:

    
    def __init__(self, mcp_server: Optional[MCPServer] = None):
        """Initialize orchestrator."""
        self.mcp_server = mcp_server or get_mcp_server()
        self.parser = get_query_parser()
        self.planner = get_planner()
        self._runs: Dict[str, AgentRunTrace] = {}
    
    async def run(self, query: str, run_id: Optional[str] = None) -> Dict[str, Any]:

        run_id = run_id or str(uuid.uuid4())
        
        logger.info(f"Starting agent run {run_id}: {query}")
        

        trace = AgentRunTrace(
            run_id=run_id,
            user_query=query,
            steps=[],
            final_status="pending",
        )
        self._runs[run_id] = trace
        

        session_id = str(uuid.uuid4())
        context = ExecutionContext(
            run_id=run_id,
            session_id=session_id,
            browser_state=BrowserState(),
        )
        
        try:

            await self._execute_with_trace(
                trace,
                "parse_query",
                "Parsing user query to extract intent and entities",
                lambda: self.parser.parse(query),
            )
            
            parse_step = trace.get_step("parse_query")
            parsed_query: ParsedUserQuery = parse_step.output_payload.get("result")
            
            await self._execute_with_trace(
                trace,
                "create_plan",
                "Creating execution plan based on parsed query",
                lambda: self.planner.create_plan(parsed_query),
            )
            
            plan_step = trace.get_step("create_plan")
            execution_plan: ExecutionPlan = plan_step.output_payload.get("result")
            

            try:
                await asyncio.wait_for(
                    self._execute_plan(trace, execution_plan, context),
                    timeout=settings.agent_execution_timeout_seconds,
                )
            except asyncio.TimeoutError:
                trace.final_status = "partial"
                trace.partial_success_reason = (
                    f"Execution timed out after {settings.agent_execution_timeout_seconds:.0f}s"
                )
                trace.add_step(AgentTraceStep(
                    step_name="timeout",
                    status="failed",
                    error_message=trace.partial_success_reason,
                ))
                logger.warning(
                    f"Agent run {run_id} timed out after {settings.agent_execution_timeout_seconds}s"
                )
            
            failed_steps = [s for s in trace.steps if s.status == "failed"]
            if failed_steps:
                trace.final_status = "partial" if trace.steps else "failed"
                trace.partial_success_reason = f"{len(failed_steps)} steps failed"
            else:
                trace.final_status = "success"
            
            logger.info(f"Agent run {run_id} completed: {trace.final_status}")
            
        except Exception as e:
            logger.error(f"Agent run {run_id} failed: {e}")
            trace.final_status = "failed"
            trace.partial_success_reason = str(e)
            
            trace.add_step(AgentTraceStep(
                step_name="error",
                status="failed",
                error_message=str(e),
            ))
        
        return await self._build_response(trace, context)
    
    async def _execute_with_trace(
        self,
        trace: AgentRunTrace,
        step_name: str,
        reasoning: str,
        func,
    ) -> Any:
        step = AgentTraceStep(
            step_name=step_name,
            reasoning=reasoning,
            status="started",
            started_at=datetime.now(),
        )
        trace.add_step(step)
        
        try:
            result = func()
            
            if hasattr(result, '__await__'):
                result = await result
            
            step.status = "completed"
            step.output_payload = {"result": result}
            step.finished_at = datetime.now()
            
            if step.started_at:
                step.duration_ms = int(
                    (step.finished_at - step.started_at).total_seconds() * 1000
                )
            
            logger.info(f"Step {step_name} completed")
            return result
            
        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.finished_at = datetime.now()
            
            if step.started_at:
                step.duration_ms = int(
                    (step.finished_at - step.started_at).total_seconds() * 1000
                )
            
            logger.error(f"Step {step_name} failed: {e}")
            raise
    
    async def _execute_plan(
        self,
        trace: AgentRunTrace,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> None:
        for step in plan.steps:
            logger.info(f"Executing step {step.step_id}: {step.tool_name}")
            
            trace_step = AgentTraceStep(
                step_name=step.step_id,
                tool_name=step.tool_name,
                reasoning=step.reasoning,
                status="started",
                started_at=datetime.now(),
                input_payload=step.input_data,
            )
            trace.add_step(trace_step)
            
            try:
                result = await self.mcp_server.execute_tool(
                    tool_name=step.tool_name,
                    input_data=step.input_data,
                    context=context,
                    reasoning=step.reasoning,
                )
                
                trace_step.status = "completed" if result.success else "failed"
                trace_step.output_payload = result.output
                trace_step.error_message = result.error
                trace_step.finished_at = datetime.now()
                
                if trace_step.started_at:
                    trace_step.duration_ms = int(
                        (trace_step.finished_at - trace_step.started_at).total_seconds() * 1000
                    )
                
                if result.screenshot_path:
                    trace_step.screenshot_path = result.screenshot_path
                if result.html_snapshot:
                    trace_step.html_snapshot = result.html_snapshot[:1000]
                
                if result.success and step.tool_name == "browser.open_url":
                    context.browser_state.current_url = result.output.get("url", "")
                    context.browser_state.page_title = result.output.get("title", "")
                
                if not result.success:
                    logger.warning(f"Step {step.step_id} failed, stopping")
                    break
                    
            except Exception as e:
                trace_step.status = "failed"
                trace_step.error_message = str(e)
                trace_step.finished_at = datetime.now()
                logger.error(f"Step {step.step_id} error: {e}")
                break
    
    async def _build_response(
        self,
        trace: AgentRunTrace,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        completed_steps = [s for s in trace.steps if s.status == "completed"]
        

        browser_result = None
        for step in trace.steps:
            if step.tool_name == "browser.open_url":
                browser_result = {
                    "final_url": step.output_payload.get("url") if step.output_payload else None,
                    "page_title": step.output_payload.get("title") if step.output_payload else None,
                    "actions_completed": [s.tool_name for s in trace.steps if s.status == "completed" and s.tool_name],
                }
                break
        
        return {
            "run_id": trace.run_id,
            "query": trace.user_query,
            "status": trace.final_status,
            "result": {
                "summary": self._generate_summary(trace),
                "intent_type": trace.steps[0].output_payload.get("intent_type") if trace.steps else "unknown",
                "browser_result": browser_result,
                "trace": trace.model_dump(),
            },
            "error": trace.partial_success_reason if trace.final_status != "success" else None,
        }
    
    def _generate_summary(self, trace: AgentRunTrace) -> str:
        if trace.final_status == "success":
            return f"Successfully executed {len([s for s in trace.steps if s.status == 'completed'])} steps"
        elif trace.final_status == "partial":
            return f"Partially completed: {trace.partial_success_reason}"
        else:
            return f"Failed: {trace.partial_success_reason}"
    
    def get_trace(self, run_id: str) -> Optional[AgentRunTrace]:
        return self._runs.get(run_id)



_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
