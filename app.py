# app.py
from flask import Flask, request, Response, render_template, abort
from html import escape
from markupsafe import Markup
from src.utils import load_jobs_from_persona_folder

class API:
    JOBS = {}
    # ---- Mock store (replace with your real data layer) ----
    # JOBS = {
    #     "1": {
    #         "id": "1",
    #         "title": "Senior Recommender Systems Scientist",
    #         "location": "Melbourne, VIC",
    #         "type": "Full-time",
    #         "salary": "$165k–$185k",
    #         "summary": "Own offline evaluation and A/B tests for personalization models at scale.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Join our AI &amp; Personalisation team to design, evaluate, and productionize state-of-the-art recommender systems that power experiences for millions of users.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Design and ship algorithms across MF, bandits, and sequential/transformer-based recommenders.</li>
    #               <li>Own offline evaluation pipelines and run online A/B tests to validate impact.</li>
    #               <li>Define success metrics with Product and translate problems into ML solutions.</li>
    #               <li>Document models, ensure reproducibility, and uphold model governance.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Python (PyTorch/TensorFlow), Spark/Databricks for large-scale data.</li>
    #               <li>Experimentation &amp; ranking metrics (NDCG, MAP, CTR lift, uplift).</li>
    #               <li>AWS (SageMaker, ECS/ECR, S3) and modern ML tooling.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>5+ years building recommender/personalisation systems.</li>
    #               <li>Comfortable partnering across Product, Engineering, and Design.</li>
    #               <li>Balanced research depth with pragmatic delivery.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/1",
    #     },
    #     "2": {
    #         "id": "2",
    #         "title": "Machine Learning Engineer — Ranking",
    #         "location": "Sydney, NSW",
    #         "type": "Hybrid",
    #         "salary": "$150k–$170k",
    #         "summary": "Productionize L2R pipelines and model serving for search relevance.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Scale and harden learning-to-rank models that deliver fast, relevant search results in a high-traffic environment.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Build training/serving pipelines and feature stores for ranking.</li>
    #               <li>Optimize latency/throughput of inference services and caches.</li>
    #               <li>Operationalize models with CI/CD, blue/green, and canary releases.</li>
    #               <li>Own observability: tracing, drift/quality dashboards, and alerts.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Python/Scala/Go; XGBoost/LightGBM/LambdaMART; ANN (Faiss/ScaNN).</li>
    #               <li>AWS (SageMaker, DynamoDB, Lambda, ECS) and Terraform.</li>
    #               <li>Kubernetes, Docker, Prometheus, Grafana.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>4+ years as an ML/Platform Engineer.</li>
    #               <li>Strong systems thinking and perf tuning skills.</li>
    #               <li>Comfortable owning production SLAs.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/2",
    #     },
    #     "3": {
    #         "id": "3",
    #         "title": "Data Scientist (Experimentation)",
    #         "location": "Remote (AU)",
    #         "type": "Contract",
    #         "salary": "$120/hr",
    #         "summary": "Design bandit strategies and run end-to-end experiments on the jobs marketplace.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Lead online experimentation and causal analysis to accelerate decision making across product surfaces.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Design/analyse RCTs and adaptive tests (multi-armed bandits).</li>
    #               <li>Develop uplift models and sequential testing methodologies.</li>
    #               <li>Educate teams on experiment design, power, and interpretation.</li>
    #               <li>Standardize documentation and reproducibility.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Python (pandas, scikit-learn, statsmodels), SQL.</li>
    #               <li>Causal inference (DoWhy/EconML) and Bayesian methods a plus.</li>
    #               <li>Dashboarding &amp; results pipelines.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>3+ years in experimentation/statistics roles.</li>
    #               <li>Clear communicator to technical and non-technical audiences.</li>
    #               <li>Thrives in remote, outcome-oriented settings.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/3",
    #     },
    #     "4": {
    #         "id": "4",
    #         "title": "NLP Research Scientist",
    #         "location": "Canberra, ACT",
    #         "type": "Full-time",
    #         "salary": "$155k–$175k",
    #         "summary": "Advance natural language understanding for conversational agents.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Push the frontier of language understanding/generation for dialogue, summarisation, and classification at scale.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Prototype transformer architectures for production-ready NLP.</li>
    #               <li>Publish results; collaborate with engineering for deployment.</li>
    #               <li>Evaluate for robustness, bias, safety, and fairness.</li>
    #               <li>Curate datasets and define eval benchmarks.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>PyTorch/TF, HuggingFace; optionally JAX/Flax.</li>
    #               <li>Distributed training and efficient inference.</li>
    #               <li>Prompting, fine-tuning, and retrieval-augmented generation.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>PhD or equivalent research experience in NLP/ML.</li>
    #               <li>Publication record at ACL/EMNLP/NeurIPS/ICML/ICLR.</li>
    #               <li>Bridges research rigor with product realities.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/4",
    #     },
    #     "5": {
    #         "id": "5",
    #         "title": "Cloud Data Engineer",
    #         "location": "Brisbane, QLD",
    #         "type": "Full-time",
    #         "salary": "$130k–$150k",
    #         "summary": "Design and maintain large-scale data pipelines in the cloud.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Build reliable, cost-efficient data platforms that power analytics, ML, and product features.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Design/operate ETL/ELT on Databricks, Airflow, and AWS.</li>
    #               <li>Optimize Spark and warehouse workloads for performance/cost.</li>
    #               <li>Implement DQ checks, lineage, and governance.</li>
    #               <li>Partner with analysts/DS for schema design and serving layers.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Databricks (Spark, Delta), Airflow; strong SQL.</li>
    #               <li>AWS: S3, Glue, Redshift, Lambda; IaC (Terraform).</li>
    #               <li>Testing/CI for data (dbt/Great Expectations a plus).</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>3+ years in data engineering.</li>
    #               <li>Pragmatic, metrics-driven, and cost-aware.</li>
    #               <li>Great collaborator across product &amp; analytics.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/5",
    #     },
    #     "6": {
    #         "id": "6",
    #         "title": "Computer Vision Engineer",
    #         "location": "Adelaide, SA",
    #         "type": "Hybrid",
    #         "salary": "$140k–$160k",
    #         "summary": "Develop vision-based solutions for image and video analytics.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Deliver real-time image/video analytics for detection, tracking, and recognition use cases.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Train/deploy CNN/ViT models for detection/segmentation.</li>
    #               <li>Optimize inference on GPUs and edge devices (TensorRT/ONNX).</li>
    #               <li>Own data pipelines: labeling, augmentation, evaluation.</li>
    #               <li>Monitor drift and maintain model quality in production.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>PyTorch/TF, OpenCV, ONNX Runtime, TensorRT.</li>
    #               <li>Streaming/video processing fundamentals.</li>
    #               <li>MLOps for vision: packaging, telemetry, retraining loops.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>3+ years in applied computer vision.</li>
    #               <li>Solid grounding in modern architectures (YOLO/Mask R-CNN/ViT).</li>
    #               <li>Curious, performance-minded, and product-focused.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/6",
    #     },
    #     "7": {
    #         "id": "7",
    #         "title": "AI Product Manager",
    #         "location": "Melbourne, VIC",
    #         "type": "Full-time",
    #         "salary": "$145k–$165k",
    #         "summary": "Bridge AI research and product delivery for customer-facing solutions.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Own the roadmap for AI-powered personalisation and search features that drive measurable customer value.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Translate customer problems into ML-backed product requirements.</li>
    #               <li>Prioritise experiments and features with DS/Eng; define success metrics.</li>
    #               <li>Run discovery, synthesize insights, and communicate outcomes.</li>
    #               <li>Ensure ethical, safe, and compliant use of AI.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Working knowledge of recommender/search concepts and A/B testing.</li>
    #               <li>Data literacy: SQL/BI; hypothesis &amp; metric design.</li>
    #               <li>Agile product delivery.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>4+ years in product management (ML/AI products a plus).</li>
    #               <li>Excellent stakeholder management and storytelling.</li>
    #               <li>Customer-obsessed, outcome-driven.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/7",
    #     },
    #     "8": {
    #         "id": "8",
    #         "title": "MLOps Engineer",
    #         "location": "Sydney, NSW",
    #         "type": "Full-time",
    #         "salary": "$135k–$155k",
    #         "summary": "Automate ML workflows from training to deployment and monitoring.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Build the tooling and automation that lets data scientists ship reliable models quickly and safely.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Implement continuous training/deployment pipelines and model registries.</li>
    #               <li>Own containerisation/orchestration and environment parity.</li>
    #               <li>Build monitoring for drift, bias, and performance regression.</li>
    #               <li>Establish incident response/runbooks for ML systems.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Docker, Kubernetes, GitHub Actions/CircleCI.</li>
    #               <li>MLflow or similar; feature stores; IaC (Terraform).</li>
    #               <li>Observability: Prometheus, Grafana, OpenTelemetry.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>3+ years in MLOps/DevOps/ML Eng.</li>
    #               <li>Automation-first mindset; strong reliability focus.</li>
    #               <li>Great collaborator with platform thinking.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/8",
    #     },
    #     "9": {
    #         "id": "9",
    #         "title": "Quantitative Analyst",
    #         "location": "Sydney, NSW",
    #         "type": "Full-time",
    #         "salary": "$150k–$180k",
    #         "summary": "Build models for financial risk and portfolio optimization.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Develop quantitative models and analytics to inform trading, hedging, and risk decisions.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Design/validate risk and pricing models; maintain model documentation.</li>
    #               <li>Backtest strategies, perform scenario analysis and stress testing.</li>
    #               <li>Partner with engineering to productionize algorithms.</li>
    #               <li>Communicate insights to senior stakeholders and risk committees.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>Python/R, NumPy/Pandas/Stats; strong SQL.</li>
    #               <li>Time series, stochastic calculus, and optimization methods.</li>
    #               <li>Cloud analytics (AWS/GCP) experience desirable.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>5+ years in financial services/trading analytics.</li>
    #               <li>Rigorous, detail-oriented, and calm under pressure.</li>
    #               <li>Excellent communicator with commercial mindset.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/9",
    #     },
    #     "10": {
    #         "id": "10",
    #         "title": "Generative AI Engineer",
    #         "location": "Remote (AU)",
    #         "type": "Contract",
    #         "salary": "$110/hr",
    #         "summary": "Prototype and deploy generative models for creative applications.",
    #         "description": """
    #             <h5>Role Focus</h5>
    #             <p>Prototype, evaluate, and deploy LLM- and diffusion-powered features across text, code, and media workflows.</p>
    #             <h5>Core Responsibilities</h5>
    #             <ul>
    #               <li>Fine-tune/align LLMs; build RAG and evaluation harnesses.</li>
    #               <li>Develop microservices/APIs to serve generative models at scale.</li>
    #               <li>Explore prompt engineering, safety filters, and guardrails.</li>
    #               <li>Work with Product to identify high-value, feasible use cases.</li>
    #             </ul>
    #             <h5>Technical Skills</h5>
    #             <ul>
    #               <li>OpenAI/HuggingFace/LangChain; PyTorch/TensorFlow.</li>
    #               <li>Vector DBs (FAISS/pgvector), embeddings, evaluators.</li>
    #               <li>Deploy on AWS/GCP with CI/CD.</li>
    #             </ul>
    #             <h5>About You</h5>
    #             <ul>
    #               <li>3+ years in NLP or generative AI.</li>
    #               <li>Rapid prototyper with product sense.</li>
    #               <li>Strong collaborator and communicator.</li>
    #             </ul>
    #         """,
    #         "url": "https://example.com/job/10",
    #     },
    # }

    def __init__(self, app: Flask):
        self.app = app
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/", view_func=self.index)
        app.add_url_rule("/api/seek", view_func=self.seek, methods=["POST"])
        app.add_url_rule("/api/tailor-cv", view_func=self.tailor_cv, methods=["POST"])
        app.add_url_rule("/api/job/<job_id>", view_func=self.job_detail, methods=["GET"])

    def _meta_line(self, job: dict) -> str:
        bits = [job.get("location") or "", job.get("type") or "", job.get("salary") or ""]
        bits = [escape(b) for b in bits if b]
        return " • ".join(bits)

    def render_job_cards(self, jobs: list[dict]) -> str:
        """Return safe HTML snippet for the jobs list. Cards include data-job-id for clicks."""
        if not jobs:
            return '<p style="color:#6b7280">No jobs found.</p>'

        parts = []
        for job in jobs:
            title = escape(job.get("title") or "Untitled role")
            summary = escape(" ".join(job.get("summary")) or "")
            meta = self._meta_line(job)
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

    def render_detail_panel(self, job: dict) -> str:
        title = escape(job.get("title") or "Job")
        meta  = self._meta_line(job)
        # Treat description as trusted server-side HTML
        desc_html = Markup(job.get("description") or "<p>No description available.</p>")
        url = job.get("url") or ""

        if url:
            url_attr = escape(url, quote=True)
            apply_cta = f'<a class="btn-seek" href="{url_attr}" target="_blank" rel="noopener">Apply now</a>'
        else:
            apply_cta = '<button class="btn-seek" disabled>Apply now</button>'

        # NOTE: Add data-action="tailor" so the delegated listener can target reliably
        return f"""
        <h4 class="title">{title}</h4>
        {'<p class="meta">' + meta + '</p>' if meta else ''}
        <div class="body">{desc_html}</div>
        <div class="actions">
          {apply_cta}
          <button class="btn-outline" type="button">Save</button>
          <button class="btn-outline" type="button">Share</button>
          <button id="tailorBtn" class="btn-outline" type="button" data-action="tailor">Tailor CV</button>
        </div>
        """

    def index(self):
        return render_template("index.html")

    def seek(self):
        data = request.get_json(silent=True) or {}
        print("Search payload:", data)

        keywords = data.get("keywords", [])
        jobs = []
        if keywords:
            # Use the first keyword as the persona folder name
            jobs = load_jobs_from_persona_folder(keywords)
            self.JOBS = {job["id"]: job for job in jobs}
        html = self.render_job_cards(jobs)
        return Response(html, mimetype="text/html")

    def tailor_cv(self):
        data = request.get_json(silent=True) or {}
        print("Tailor CV payload:", data)

        # For now just return a simple text response
        return Response(
            "<p style='color:#166534'>CV tailoring endpoint hit successfully!</p>",
            mimetype="text/html"
        )

    def job_detail(self, job_id: str):
        print("-----------> Job detail request for ID:", job_id)
        print(self.JOBS)
        job = self.JOBS.get(job_id)
        if not job:
            abort(404)
        html = self.render_detail_panel(job)
        return Response(html, mimetype="text/html")

app = Flask(__name__)
api = API(app)

if __name__ == "__main__":
    app.run(debug=True)
