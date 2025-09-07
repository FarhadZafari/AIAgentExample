from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# API for Module 1: Candidate Greeting
@app.route('/api/seek', methods=['POST'])
def seek():
    data = request.json  # {keywords, classification, where}
    print("Search payload:", data)

    # --- mock results from your backend ---
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
    # --------------------------------------

    return jsonify({"jobs": jobs})

if __name__ == "__main__":
    app.run(debug=True)
