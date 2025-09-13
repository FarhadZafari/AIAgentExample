import json
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
from reportlab.lib.units import inch
import re
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

# def save_resume_as_pdf(tailored_resume: str, persona_dir: str, job_id: str) -> bool:
#     pdf_filename = f"updated_resume_job{job_id}.pdf"
#     pdf_path = os.path.join(persona_dir, pdf_filename)
#
#     # Write the tailored resume text to a PDF
#     c = canvas.Canvas(pdf_path, pagesize=letter)
#     width, height = letter
#     lines = tailored_resume.split('\n')
#     y = height - 40
#     for line in lines:
#         c.drawString(40, y, line)
#         y -= 15
#         if y < 40:
#             c.showPage()
#             y = height - 40
#     c.save()
#
#     return True

def save_resume_as_pdf(tailored_resume: str, persona_dir: str, job_id: str) -> bool:
    os.makedirs(persona_dir, exist_ok=True)
    pdf_filename = f"updated_resume_job{job_id}.pdf"
    pdf_path = os.path.join(persona_dir, pdf_filename)

    # --- Styles ---
    styles = getSampleStyleSheet()
    by = styles.byName  # dict of existing styles

    if "ResumeBody" not in by:
        styles.add(ParagraphStyle(name="ResumeBody", parent=styles["Normal"],
                                  fontName="Helvetica", fontSize=10.5, leading=13.5))
    if "Small" not in by:
        styles.add(ParagraphStyle(name="Small", parent=styles["ResumeBody"],
                                  fontSize=8.5, leading=11))
    if "H1" not in by:
        styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"],
                                  fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=6))
    if "H2" not in by:
        styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"],
                                  fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=8, spaceAfter=4))
    if "ResumeBullet" not in by:
        styles.add(ParagraphStyle(name="ResumeBullet", parent=styles["ResumeBody"],
                                  leftIndent=14, bulletIndent=6, spaceBefore=0, spaceAfter=2))

    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=0.7*inch, bottomMargin=0.7*inch
    )

    # --- Minimal Markdown -> RL Paragraph text ---
    def md_inline_to_html(s: str) -> str:
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)                # bold
        s = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<i>\1</i>", s)        # italics
        s = s.replace("<br>", "<br/>").replace("<br />", "<br/>")     # line breaks
        return s

    elements = []
    lines = tailored_resume.splitlines()
    pending_list_items = []

    def flush_list():
        nonlocal pending_list_items
        if pending_list_items:
            lst = ListFlowable(
                [ListItem(Paragraph(md_inline_to_html(item), styles["ResumeBody"])) for item in pending_list_items],
                bulletType='bullet', leftIndent=10
            )
            elements.append(lst)
            pending_list_items = []

    for raw in lines:
        line = raw.rstrip()

        # horizontal rule
        if line.strip().lower() == "<hr>":
            flush_list()
            elements.append(Spacer(1, 6))
            elements.append(HRFlowable(width="100%", thickness=0.8, spaceBefore=4, spaceAfter=6))
            continue

        # headings
        if line.startswith("## "):
            flush_list()
            elements.append(Paragraph(md_inline_to_html(line[3:].strip()), styles["H2"]))
            continue
        if line.startswith("# "):
            flush_list()
            elements.append(Paragraph(md_inline_to_html(line[2:].strip()), styles["H1"]))
            continue

        # bullets
        if line.lstrip().startswith("- "):
            pending_list_items.append(line.lstrip()[2:].strip())
            continue

        # blank line
        if line.strip() == "":
            flush_list()
            elements.append(Spacer(1, 6))
            continue

        # regular paragraph (with <small> support)
        flush_list()
        if "<small>" in line.lower():
            text = md_inline_to_html(line.replace("<small>", "").replace("</small>", ""))
            elements.append(Paragraph(f'<font size="8.5">{text}</font>', styles["ResumeBody"]))
        else:
            elements.append(Paragraph(md_inline_to_html(line), styles["ResumeBody"]))

    flush_list()
    elements.append(Spacer(1, 4))
    doc.build(elements)
    return True
