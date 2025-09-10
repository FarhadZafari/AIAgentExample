# resume_agent.py
# A minimal LangGraph agent that:
# 1) fetches job, 2) fetches resume, 3) analyzes & maybe asks,
# 4) tailors resume, 5) saves it. Uses a MemorySaver + thread_id.

from __future__ import annotations
from typing import TypedDict, List, Optional, Literal
from typing_extensions import Annotated
import operator
import os
from dataclasses import dataclass

from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

class AgentState(TypedDict):
    job_id: Optional[str]
    candidate_id: Optional[str]
    job_text: Optional[str]
    resume_text: Optional[str]
    needs_clarification: Optional[bool]
    question: Optional[str]
    clarification_response: Optional[str]
    tailored_resume: Optional[str]
    # Log of what happened (reducer = list concat)
    messages: Annotated[List[BaseMessage], operator.add]


@dataclass
class JobStore:
    data: dict

@dataclass
class ResumeStore:
    data: dict

job_store = JobStore(
    data={
        "job-123": (
            "Data Scientist at ExampleCo. Responsibilities: build LTR models; "
            "Python, PySpark, AWS; experience with bandits; strong A/B testing."
        )
    }
)

resume_store = ResumeStore(
    data={
        "cand-999": (
            "Farhad Zafari — ML/DS. Skills: Python, PySpark, Databricks, AWS, "
            "RL bandits, LTR, A/B testing; Publications; Productionized models at SEEK."
        )
    }
)

@tool("fetch_job")
def fetch_job(job_id: str) -> str:
    """Fetch full job posting text by job_id."""
    return job_store.data.get(job_id, "")

@tool("fetch_resume")
def fetch_resume(candidate_id: str) -> str:
    """Fetch candidate resume text by candidate_id."""
    return resume_store.data.get(candidate_id, "")

@tool("ask_candidate")
def ask_candidate(question: str) -> str:
    """
    Ask the candidate a clarifying question.
    This implementation pauses and waits for the candidate to type their answer.
    """
    print(f"\n--- Clarifying Question ---\n{question}")
    answer = input("Your answer: ")
    return answer.strip()

@tool("save_tailored_resume")
def save_tailored_resume(filename: str, content: str, directory: str = "./tailored") -> str:
    """Save the tailored resume to a directory and return the path."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path



# Ensure OPENAI_API_KEY is set in your environment.
llm = ChatOpenAI(model="gpt-4o-mini")  # swap to your preferred model


class ClarifyDecision(BaseModel):
    needs_clarification: bool = Field(
        description="True if a clarifying question is required to tailor effectively."
    )
    question: Optional[str] = Field(
        default=None,
        description="The single most important question to ask if clarification is needed."
    )

def node_fetch_job(state: AgentState) -> AgentState:
    job_id = state.get("job_id")
    job_text = fetch_job.invoke({"job_id": job_id})
    return {
        "job_text": job_text,
        "messages": [AIMessage(content=f"Fetched job: {job_id} ({len(job_text)} chars)")]
    }

def node_fetch_resume(state: AgentState) -> AgentState:
    cand_id = state.get("candidate_id")
    resume_text = fetch_resume.invoke({"candidate_id": cand_id})
    return {
        "resume_text": resume_text,
        "messages": [AIMessage(content=f"Fetched resume: {cand_id} ({len(resume_text)} chars)")]
    }

def node_analyze(state: AgentState) -> AgentState:
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
    decision: ClarifyDecision = llm.with_structured_output(ClarifyDecision).invoke([system, human])
    needs = bool(decision.needs_clarification)
    q = decision.question if needs else None
    return {
        "needs_clarification": needs,
        "question": q,
        "messages": [AIMessage(content=f"Analyze: needs_clarification={needs}; question={q or ''}")]
    }

def node_ask(state: AgentState) -> AgentState:
    q = state.get("question") or "Could you clarify any preferences or constraints?"
    answer = ask_candidate.invoke({"question": q})
    return {
        "clarification_response": answer,
        "messages": [AIMessage(content=f"Asked candidate: {q}\nAnswer: {answer}")]
    }

def node_tailor(state: AgentState) -> AgentState:
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
    tailored = llm.invoke([system, human]).content
    return {"tailored_resume": tailored, "messages": [AIMessage(content="Tailored resume created.")]}

def node_save(state: AgentState) -> AgentState:
    cand = state.get("candidate_id") or "candidate"
    job = state.get("job_id") or "job"
    filename = f"{cand}__for__{job}.md"
    path = save_tailored_resume.invoke({
        "filename": filename,
        "content": state.get("tailored_resume") or "",
        "directory": "./tailored"
    })
    return {"messages": [AIMessage(content=f"Saved tailored resume to: {path}")]}


def route_after_analyze(state: AgentState) -> Literal["ask", "tailor"]:
    return "ask" if state.get("needs_clarification") else "tailor"

def loop_back_or_tailor(state: AgentState) -> Literal["analyze", "tailor"]:
    """
    After asking, either:
      - go straight to tailor if we have a reply, or
      - loop once to analyze if still missing info.
    """
    if state.get("clarification_response"):
        return "tailor"
    return "analyze"


graph = StateGraph(AgentState)

graph.add_node("fetch_job", node_fetch_job)
graph.add_node("fetch_resume", node_fetch_resume)
graph.add_node("analyze", node_analyze)
graph.add_node("ask", node_ask)
graph.add_node("tailor", node_tailor)
graph.add_node("save", node_save)

graph.add_edge(START, "fetch_job")
graph.add_edge("fetch_job", "fetch_resume")
graph.add_edge("fetch_resume", "analyze")
graph.add_conditional_edges("analyze", route_after_analyze, {
    "ask": "ask",
    "tailor": "tailor",
})
graph.add_conditional_edges("ask", loop_back_or_tailor, {
    "analyze": "analyze",
    "tailor": "tailor",
})
graph.add_edge("tailor", "save")
graph.add_edge("save", END)

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    # Initial input state
    initial_state: AgentState = {
        "job_id": "job-123",
        "candidate_id": "cand-999",
        "messages": []
    }

    # IMPORTANT: Provide a configurable key (thread_id) when using a checkpointer
    cfg = {"configurable": {"thread_id": "cand-999__job-123"}}

    # Full, single-shot run
    final = app.invoke(initial_state, config=cfg)

    print("---- FINAL KEYS ----")
    print(list(final.keys()))
    print("\n---- LOG ----")
    for m in final.get("messages", [])[-4:]:
        # print last few log lines for brevity
        print(f"- {getattr(m, 'content', '')}")

    print("\n---- TAILORED RESUME PREVIEW ----")
    print((final.get("tailored_resume") or "")[:800])

    # -----------------------------------------------------------------
    # (Optional) Pause/Resume pattern:
    #
    # 1) First run up to ask (in production you'd configure a break/interrupt).
    # 2) Later, after the human replies, update state and continue.
    #
    # Example (commented because this demo already does a single-shot run):
    #
    # app.invoke({"job_id": "job-123", "candidate_id": "cand-999", "messages": []}, config=cfg)
    # # ... wait for human reply ...
    # app.update_state(cfg, {"clarification_response": "Open to Melbourne; Australian citizen."})
    # final2 = app.invoke({}, config=cfg)  # continue from checkpoint
    # print("Resumed -> saved:", [m.content for m in final2["messages"] if "Saved tailored resume" in m.content])
