"""
NexusDB Sequential Multi-Agent Orchestrator
Executes the sequential agent pipeline:
Orchestrator -> Query Agent -> Analysis Agent -> Visualization Agent
Enforces 30-second global timeout and strictly typed JSON contract handoffs.
"""

import asyncio
import time
from typing import Callable, Awaitable, Any

from app.agents.contracts import QueryRequest, QueryResult, AnalysisResult, VizSpec
from app.agents.query_agent import QueryAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.viz_agent import VisualizationAgent
from app.llm.base import LLMClient


class Orchestrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.query_agent = QueryAgent(llm)
        self.analysis_agent = AnalysisAgent(llm)
        self.viz_agent = VisualizationAgent()

    async def run(
        self,
        request: QueryRequest,
        emit_stage: Callable[..., Awaitable[None]] | None = None,
        timeout_seconds: float = 30.0,
    ) -> tuple[QueryResult, AnalysisResult, VizSpec]:
        """Runs the multi-agent pipeline with global timeout enforcement."""
        async def _pipeline():
            # 1. Query Agent execution (Schema retrieval + Reflection loop)
            query_res = await self.query_agent.execute(request, emit_stage=emit_stage)

            # 2. Analysis Agent execution (Pandas metrics + narrative)
            if emit_stage:
                await emit_stage(stage=7, name="Analysis (Pandas)", status="start", ms=0)
            analysis_res = await self.analysis_agent.analyze(request.question, query_res)
            if emit_stage:
                await emit_stage(stage=7, name="Analysis (Pandas)", status="done", ms=20, detail=f"Computed statistics across {len(query_res.columns)} columns")

            # 3. Visualization Agent execution (rules-based chart selection)
            if emit_stage:
                await emit_stage(stage=8, name="Visualization", status="start", ms=0)
            viz_spec = self.viz_agent.generate_viz(query_res)
            if emit_stage:
                await emit_stage(stage=8, name="Visualization", status="done", ms=10, detail=f"Selected chart type: {viz_spec.chart_type}")

            return query_res, analysis_res, viz_spec

        return await asyncio.wait_for(_pipeline(), timeout=timeout_seconds)
