# app.py
from flask import Flask, request, Response, render_template, abort
from html import escape

app = Flask(__name__)

# ---- Mock store (replace with your real data layer) ----
JOBS = {
    "1": {
        "id": "1",
        "title": "Senior Recommender Systems Scientist",
        "location": "Melbourne, VIC",
        "type": "Full-time",
        "salary": "$165k–$185k",
        "summary": "Own offline evaluation and A/B tests for personalization models at scale.",
        "description": (
            "Lead the design of recommender models (MF, bandits, sequential), own metrics, "
            "and partner with engineering to ship experiments to production. "
            "Tech: PyTorch, Spark/Databricks, AWS."
        ),
        "url": "https://example.com/job/1",
    },
    "2": {
        "id": "2",
        "title": "Machine Learning Engineer — Ranking",
        "location": "Sydney, NSW",
        "type": "Hybrid",
        "salary": "$150k–$170k",
        "summary": "Productionize L2R pipelines and model serving for search relevance.",
        "description": (
            "Build and operate ranking services (Faiss/ANN, Triton, SageMaker), "
            "optimize latency/throughput, and harden CI/CD + monitoring."
        ),
        "url": "https://example.com/job/2",
    },
    "3": {
        "id": "3",
        "title": "Data Scientist (Experimentation)",
        "location": "Remote (AU)",
        "type": "Contract",
        "salary": "$120/hr",
        "summary": "Design bandit strategies and run end-to-end experiments on the jobs marketplace.",
        "description": (
            "Own experiment design, sequential testing, and bandit algorithms; "
            "drive insights from uplift modeling and causal inference."
        ),
        "url": "https://example.com/job/3",
    },
}

def _meta_line(job: dict) -> str:
    bits = [job.get("location") or "", job.get("type") or "", job.get("salary") or ""]
    bits = [escape(b) for b in bits if b]
    return " • ".join(bits)

def render_job_cards(jobs: list[dict]) -> str:
    """Return safe HTML snippet for the jobs list. Cards include data-job-id for clicks."""
    if not jobs:
        return '<p style="color:#6b7280">No jobs found.</p>'

    parts = []
    for job in jobs:
        title = escape(job.get("title") or "Untitled role")
        summary = escape(job.get("summary") or "")
        meta = _meta_line(job)
        jid = escape(job.get("id") or "", quote=True)

        card_html = f"""
        <article class="job-card" data-job-id="{jid}" tabindex="0" role="button" aria-label="View details for {title}">
          <h3>{title}</h3>
          {'<p class="meta">' + meta + '</p>' if meta else ''}
          {'<p class="excerpt">' + summary + '</p>' if summary else ''}
          <button class="btn-outline" type="button">View job</button>
        </article>
        """
        parts.append(card_html)

    return "\n".join(parts)

def render_detail_panel(job: dict) -> str:
    """Return safe HTML snippet for the right-hand detail panel content."""
    title = escape(job.get("title") or "Job")
    meta = _meta_line(job)
    desc = escape(job.get("description") or "No description available.")
    url = job.get("url") or ""

    if url:
        url_attr = escape(url, quote=True)
        apply_cta = f'<a class="btn-seek" href="{url_attr}" target="_blank" rel="noopener">Apply now</a>'
    else:
        apply_cta = '<button class="btn-seek" disabled>Apply now</button>'

    return f"""
    <h4 class="title">{title}</h4>
    {'<p class="meta">' + meta + '</p>' if meta else ''}
    <div class="body"><p>{desc}</p></div>
    <div class="actions">
      {apply_cta}
      <button class="btn-outline" type="button">Save</button>
      <button class="btn-outline" type="button">Share</button>
    </div>
    """

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/seek", methods=["POST"])
def seek():
    # You can use the payload to filter JOBS; here we just echo mock results.
    data = request.get_json(silent=True) or {}
    print("Search payload:", data)

    jobs = list(JOBS.values())  # TODO: replace with real search/filter
    html = render_job_cards(jobs)
    return Response(html, mimetype="text/html")

@app.route("/api/job/<job_id>", methods=["GET"])
def job_detail(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        abort(404)
    html = render_detail_panel(job)
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True)
