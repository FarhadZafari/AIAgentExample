from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# API for Module 1: Candidate Greeting
@app.route('/api/greet', methods=['POST'])
def greet():
    data = request.json
    candidate_name = data.get('candidate_name', 'Guest')
    greeting = f"Hello, {candidate_name}! Welcome to the platform."
    return jsonify({"greeting": greeting})

# API for Module 2: Candidate Skill Level Check
@app.route('/api/check_skill', methods=['POST'])
def check_skill():
    data = request.json
    skill = data.get('skill', '').lower()
    level = "Advanced" if skill in ["python", "flask", "sql"] else "Beginner"
    message = f"Your skill level in {skill.title()} is {level}."
    return jsonify({"message": message})

if __name__ == "__main__":
    app.run(debug=True)
