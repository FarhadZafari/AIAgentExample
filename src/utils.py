import os
import json
from pathlib import Path

def load_jobs_from_persona_folder(persona_keyword: str) -> list[dict]:
    persona_dir = os.path.join("personas", persona_keyword)
    print(persona_dir)
    jobs = []
    if not os.path.isdir(persona_dir):
        return jobs

    for fname in os.listdir(persona_dir + "/jobs"):
        if fname.startswith("job") and fname.endswith("-card.json"):
            job_id = fname.split("-")[0][3:]  # Extract i from job{i}-card.json
            card_path = os.path.join(persona_dir, "jobs" / Path(fname))
            desc_path = os.path.join(persona_dir, "jobs" / Path(f"job{job_id}-description.txt"))
            try:
                with open(card_path, "r", encoding="utf-8") as f:
                    print(f)
                    job = json.load(f)
                if os.path.exists(desc_path):
                    with open(desc_path, "r", encoding="utf-8") as f:
                        job["description"] = f.read()
                else:
                    job["description"] = "<p>No description available.</p>"
                jobs.append(job)
            except Exception as e:
                print(f"Error loading job {fname}: {e}")
    print(jobs)
    return jobs