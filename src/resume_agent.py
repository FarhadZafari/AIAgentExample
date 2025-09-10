# resume_agent.py
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict, List, Optional, Literal, Callable
from typing_extensions import Annotated
import operator
import os

from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool, Tool
from langchain_openai import ChatOpenAI


# -----------------------------
# State and IO Stores
# -----------------------------

class AgentState(TypedDict):
    job_id: Optional[str]
    candidate_id: Optional[str]
    job_text: Optional[str]
    resume_text: Optional[str]
    needs_clarification: Optional[bool]
    question: Optional[str]
    clarification_response: Optional[str]
    tailored_resume: Optional[str]
    messages: Annotated[List[BaseMessage], operator.add]  # reducer: concat


@dataclass
class JobStore:
    data: dict


@dataclass
class ResumeStore:
    data: dict


# -----------------------------
# Pydantic schema for LLM output
# -----------------------------

class ClarifyDecision(BaseModel):
    needs_clarification: bool = Field(
        description="True if a clarifying question is required to tailor effectively."
    )
    question: Optional[str] = Field(
        default=None,
        description="The single most important question to ask if clarification is needed."
    )


# -----------------------------
# Agent Class
# -----------------------------

class ResumeTailorAgent:
    """
    Encapsulates LangGraph construction, tools, and execution for the resume-tailoring agent.
    """

    def __init__(
        self,
        job_store: JobStore | None = None,
        resume_store: ResumeStore | None = None,
        save_dir: str = "./tailored",
        llm: ChatOpenAI | None = None,
        checkpointer: MemorySaver | None = None,
    ) -> None:
        # Dependencies (DI-friendly)
        self.job_store = job_store or JobStore(
            data={
                "job-123": (
                    "Data Scientist at ExampleCo. Responsibilities: build LTR models; "
                    "Python, PySpark, AWS; experience with bandits; strong A/B testing."
                )
            }
        )
        self.resume_store = resume_store or ResumeStore(
            data={
                "cand-999": (
                    "Farhad Zafari — ML/DS. Skills: Python, PySpark, Databricks, AWS, "
                    "RL bandits, LTR, A/B testing; Publications; Productionized models at SEEK."
                )
            }
        )
        self.save_dir = save_dir
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini")  # relies on OPENAI_API_KEY env var
        self.checkpointer = checkpointer or MemorySaver()

        # Build tools (as bound callables capturing `self`)
        self.fetch_job_tool: Tool = self._make_fetch_job_tool()
        self.fetch_resume_tool: Tool = self._make_fetch_resume_tool()
        self.ask_candidate_tool: Tool = self._make_ask_candidate_tool()
        self.save_tailored_resume_tool: Tool = self._make_save_resume_tool()

        # Build graph
        self.graph: CompiledGraph = self._build_graph()

    # -------------------------
    # Public API
    # -------------------------

    def run(self, initial_state: AgentState, thread_id: str) -> AgentState:
        """
        Execute the full workflow (start -> end) with a given thread_id.
        """
        cfg = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(initial_state, config=cfg)

    def update_state(self, thread_id: str, patch: dict) -> None:
        """
        Merge `patch` into persisted state (useful for injecting a human reply).
        """
        cfg = {"configurable": {"thread_id": thread_id}}
        self.graph.update_state(cfg, patch)

    def continue_run(self, thread_id: str) -> AgentState:
        """
        Continue running from the latest checkpoint (e.g., after update_state()).
        """
        cfg = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke({}, config=cfg)

    # -------------------------
    # Tool factories
    # -------------------------

    def _make_fetch_job_tool(self) -> Tool:
        @tool("fetch_job")
        def _fetch_job(job_id: str) -> str:
            """Fetch full job posting text by job_id."""
            return self.job_store.data.get(job_id, "")
        return _fetch_job

    def _make_fetch_resume_tool(self) -> Tool:
        @tool("fetch_resume")
        def _fetch_resume(candidate_id: str) -> str:
            """Fetch candidate resume text by candidate_id."""
            return self.resume_store.data.get(candidate_id, "")
        return _fetch_resume

    def _make_ask_candidate_tool(self) -> Tool:
        @tool("ask_candidate")
        def _ask_candidate(question: str) -> str:
            """
            Ask the candidate a clarifying question.
            This implementation pauses and waits for the candidate to type their answer.
            Swap this out to send via email/Slack/UI and return the real reply.
            """
            print(f"\n--- Clarifying Question ---\n{question}")
            answer = input("Your answer: ")
            return answer.strip()
        return _ask_candidate

    def _make_save_resume_tool(self) -> Tool:
        @tool("save_tailored_resume")
        def _save_tailored_resume(filename: str, content: str, directory: str | None = None) -> str:
            """Save the tailored resume to a directory and return the path."""
            target_dir = directory or self.save_dir
            os.makedirs(target_dir, exist_ok=True)
            path = os.path.join(target_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path
        return _save_tailored_resume

    # -------------------------
    # Graph construction
    # -------------------------

    def _build_graph(self):
        graph = StateGraph(AgentState)

        # Register nodes
        graph.add_node("fetch_job", self._node_fetch_job)
        graph.add_node("fetch_resume", self._node_fetch_resume)
        graph.add_node("analyze", self._node_analyze)
        graph.add_node("ask", self._node_ask)
        graph.add_node("tailor", self._node_tailor)
        graph.add_node("save", self._node_save)

        # Edges
        graph.add_edge(START, "fetch_job")
        graph.add_edge("fetch_job", "fetch_resume")
        graph.add_edge("fetch_resume", "analyze")
        graph.add_conditional_edges("analyze", self._route_after_analyze, {
            "ask": "ask",
            "tailor": "tailor",
        })
        graph.add_conditional_edges("ask", self._loop_back_or_tailor, {
            "analyze": "analyze",
            "tailor": "tailor",
        })
        graph.add_edge("tailor", "save")
        graph.add_edge("save", END)

        return graph.compile(checkpointer=self.checkpointer)

    # -------------------------
    # Node implementations
    # -------------------------

    def _node_fetch_job(self, state: AgentState) -> AgentState:
        job_id = state.get("job_id")
        job_text = self.fetch_job_tool.invoke({"job_id": job_id})
        return {
            "job_text": job_text,
            "messages": [AIMessage(content=f"Fetched job: {job_id} ({len(job_text)} chars)")]
        }

    def _node_fetch_resume(self, state: AgentState) -> AgentState:
        cand_id = state.get("candidate_id")
        resume_text = self.fetch_resume_tool.invoke({"candidate_id": cand_id})
        return {
            "resume_text": resume_text,
            "messages": [AIMessage(content=f"Fetched resume: {cand_id} ({len(resume_text)} chars)")]
        }

    def _node_analyze(self, state: AgentState) -> AgentState:
        system = SystemMessage(content=(
            "You are a resume-tailoring assistant. Decide if a clarification from the candidate is needed "
            "to tailor for the job. Only ask if missing critical info (location, work authorization/visa, "
            "seniority, domain focus, relocation, salary expectations if explicitly relevant). "
            "Return a JSON object with `needs_clarification` and, if true, a single concise `question`."
        ))
        human = HumanMessage(content=(
            f"JOB:\n{state.get('job_text')}\n\nRESUME:\n{state.get('resume_text')}\n\n"
            "Do you need a clarification? If yes, ask the highest-value single question."
        ))
        decision: ClarifyDecision = self.llm.with_structured_output(ClarifyDecision).invoke([system, human])
        needs = bool(decision.needs_clarification)
        q = decision.question if needs else None
        return {
            "needs_clarification": needs,
            "question": q,
            "messages": [AIMessage(content=f"Analyze: needs_clarification={needs}; question={q or ''}")]
        }

    def _node_ask(self, state: AgentState) -> AgentState:
        q = state.get("question") or "Could you clarify any preferences or constraints?"
        answer = self.ask_candidate_tool.invoke({"question": q})
        return {
            "clarification_response": answer,
            "messages": [AIMessage(content=f"Asked candidate: {q}\nAnswer: {answer}")]
        }

    def _node_tailor(self, state: AgentState) -> AgentState:
        system = SystemMessage(content=(
            "You tailor resumes for specific jobs. Preserve truthful content, amplify relevant experience, "
            "and trim unrelated material. Keep it concise, ATS-friendly, and easy to scan. "
            "Use Markdown (no code fences)."
        ))
        clar = state.get("clarification_response") or ""
        human = HumanMessage(content=(
            f"JOB:\n{state.get('job_text')}\n\nRESUME (ORIGINAL):\n{state.get('resume_text')}\n\n"
            f"CANDIDATE CLARIFICATIONS (if any): {clar}\n\n"
            "Produce a tailored resume suitable for this job."
        ))
        tailored = self.llm.invoke([system, human]).content
        return {"tailored_resume": tailored, "messages": [AIMessage(content="Tailored resume created.")]}

    def _node_save(self, state: AgentState) -> AgentState:
        cand = state.get("candidate_id") or "candidate"
        job = state.get("job_id") or "job"
        filename = f"{cand}__for__{job}.md"
        path = self.save_tailored_resume_tool.invoke({
            "filename": filename,
            "content": state.get("tailored_resume") or "",
            "directory": self.save_dir
        })
        return {"messages": [AIMessage(content=f"Saved tailored resume to: {path}")]}

    # -------------------------
    # Routing / conditionals
    # -------------------------

    def _route_after_analyze(self, state: AgentState) -> Literal["ask", "tailor"]:
        return "ask" if state.get("needs_clarification") else "tailor"

    def _loop_back_or_tailor(self, state: AgentState) -> Literal["analyze", "tailor"]:
        # One simple loop: if we already got a reply, go tailor; otherwise analyze again
        return "tailor" if state.get("clarification_response") else "analyze"


# -----------------------------
# Demo / CLI entrypoint
# -----------------------------

if __name__ == "__main__":

    agent = ResumeTailorAgent()

    initial: AgentState = {
        "job_id": "job-123",
        "candidate_id": "cand-999",
        "messages": []
    }
    thread_id = "cand-999__job-123"

    # Single-shot run (will ask on console if needed)
    final_state = agent.run(initial, thread_id)

    print("\n---- FINAL KEYS ----")
    print(list(final_state.keys()))
    print("\n---- LOG (last few) ----")
    for m in final_state.get("messages", [])[-4:]:
        print(f"- {getattr(m, 'content', '')}")

    print("\n---- TAILORED RESUME PREVIEW ----")
    print((final_state.get("tailored_resume") or "")[:800])

    # Example: Pause/Resume flow (uncomment to try)
    # agent.update_state(thread_id, {"clarification_response": "Open to Melbourne; citizen."})
    # continued = agent.continue_run(thread_id)
    # print("\nResumed & saved:", [m.content for m in continued["messages"] if "Saved tailored resume" in m.content])
