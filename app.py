# app.py (no Jinja templates used for the results)
from flask import Flask, request, Response, render_template
from html import escape

app = Flask(__name__)

def render_job_cards(jobs):
    """Return a safe HTML snippet for the jobs list without using Jinja."""
    if not jobs:
        return '<p style="color:#6b7280">No jobs found.</p>'

    parts = []
    for job in jobs:
        title = escape(job.get("title") or "Untitled role")
        location = escape(job.get("location") or "")
        jtype = escape(job.get("type") or "")
        salary = escape(job.get("salary") or "")
        summary = escape(job.get("summary") or "")
        url = job.get("url") or ""

        # Build the meta line with separators only for non-empty fields
        bits = [b for b in (location, jtype, salary) if b]
        meta = " • ".join(bits)

        # Button vs link depending on url presence (url also escaped if shown)
        if url:
            url_attr = escape(url, quote=True)
            cta = f'<a class="btn-outline" href="{url_attr}" target="_blank" rel="noopener">View job</a>'
        else:
            cta = '<button class="btn-outline" disabled>View job</button>'

        card_html = f"""
        <article class="job-card">
          <h3>{title}</h3>
          <p class="meta">{meta}</p>
          <p>{summary}</p>
          {cta}
        </article>
        """
        parts.append(card_html)

    return "\n".join(parts)

@app.route("/")
def index():
    # Keep your existing index.html for the page chrome (that one uses Flask's file serving,
    # not Jinja templating for the results snippet).
    return render_template("index.html")

@app.route("/api/seek", methods=["POST"])
def seek():
    data = request.get_json(silent=True) or {}
    print("Search payload:", data)

    # --- mock results (replace with real search) ---
    jobs = [
        {
            "title": "Senior Recommender Systems Scientist",
            "location": "Melbourne, VIC",
            "type": "Full-time",
            "salary": "$165k–$185k",
            "summary": "Own offline evaluation and A/B tests for personalization models at scale.",
            "url": "https://example.com/job/1"
        },
        {
            "title": "Machine Learning Engineer — Ranking",
            "location": "Sydney, NSW",
            "type": "Hybrid",
            "salary": "$150k–$170k",
            "summary": "Productionize L2R pipelines and model serving for search relevance.",
            "url": "https://example.com/job/2"
        },
        {
            "title": "Data Scientist (Experimentation)",
            "location": "Remote (AU)",
            "type": "Contract",
            "salary": "$120/hr",
            "summary": "Design bandit strategies and run end-to-end experiments on the jobs marketplace.",
            "url": "https://example.com/job/3"
        }
    ]
    # ------------------------------------------------

    html = render_job_cards(jobs)
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True)
