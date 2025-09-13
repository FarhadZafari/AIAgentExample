import json
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


def load_jobs_from_persona_folder(persona_keyword: str) -> (list[dict], str, str):
    persona_dir = os.path.join("personas", persona_keyword)
    print(persona_dir)
    jobs = []
    if not os.path.isdir(persona_dir):
        return jobs, ""

    jobs_dir = os.path.join(persona_dir, "jobs")
    for fname in os.listdir(jobs_dir):
        if fname.startswith("job") and fname.endswith("-card.json"):
            job_id = fname.split("-")[0][3:]
            card_path = os.path.join(jobs_dir, fname)
            desc_path = os.path.join(jobs_dir, f"job{job_id}-description.txt")
            try:
                with open(card_path, "r", encoding="utf-8") as f:
                    job = json.load(f)
                if os.path.exists(desc_path):
                    with open(desc_path, "r", encoding="utf-8") as f:
                        job["description"] = f.read()
                else:
                    job["description"] = "<p>No description available.</p>"
                jobs.append(job)
            except Exception as e:
                print(f"Error loading job {fname}: {e}")

    # Read resume.pdf as string
    resume_txt = ""
    resume_path = os.path.join(persona_dir, "resume.pdf")
    if os.path.exists(resume_path):
        try:
            reader = PdfReader(resume_path)
            resume_txt = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"Error reading resume.pdf: {e}")

    print(jobs)
    print(resume_txt)
    return jobs, resume_txt, persona_dir

def save_resume_as_pdf(tailored_resume: str, persona_dir: str, job_id: str) -> bool:
    pdf_filename = f"updated_resume_job{job_id}.pdf"
    pdf_path = os.path.join(persona_dir, pdf_filename)

    # Write the tailored resume text to a PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    lines = tailored_resume.split('\n')
    y = height - 40
    for line in lines:
        c.drawString(40, y, line)
        y -= 15
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()

    return True