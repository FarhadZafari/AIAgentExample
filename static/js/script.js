document.addEventListener('DOMContentLoaded', () => {
    // Module 1: Candidate Greeting
    document.getElementById('submit_name').addEventListener('click', async () => {
        const name = document.getElementById('candidate_name').value;

        const response = await fetch('/api/greet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({candidate_name: name})
        });

        const data = await response.json();
        document.getElementById('greeting').innerText = data.greeting;
    });

    // Module 2: Skill Check
    document.getElementById('submit_skill').addEventListener('click', async () => {
        const skill = document.getElementById('skill_input').value;

        const response = await fetch('/api/check_skill', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({skill: skill})
        });

        const data = await response.json();
        document.getElementById('skill_result').innerText = data.message;
    });
});
