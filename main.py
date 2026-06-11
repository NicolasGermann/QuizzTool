import csv
import fcntl
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

CSV_FILE = BASE_DIR / "data" / "answers.csv"
CSV_FILE.parent.mkdir(exist_ok=True)
YAML_FILE = BASE_DIR / "pages.yaml"


def load_pages():
    with open(YAML_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["pages"]


def read_answer(session_id: str, page_index: int):
    if not CSV_FILE.exists():
        return None
    
    pages = load_pages()
    col = page_index_to_quiz_col(pages, page_index)
    if col is None:
        return None
    
    lock_file = CSV_FILE.with_suffix(".lock")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_SH)
        try:
            with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    
    if not rows:
        return None
    for row in rows[1:]:
        if row and row[0] == session_id:
            return row[col] if col < len(row) else None
    return None


def get_quiz_indices(pages):
    return [i for i, p in enumerate(pages) if p["type"] == "quiz"]


def find_previous_quiz_page(pages, page_index):
    for i in range(page_index - 1, -1, -1):
        if pages[i]["type"] == "quiz":
            return i
    return page_index - 1


def page_index_to_quiz_col(pages, page_index):
    quiz_indices = get_quiz_indices(pages)
    if page_index in quiz_indices:
        return quiz_indices.index(page_index) + 1
    return None


def save_answer(session_id: str, page_index: int, answer: str):
    pages = load_pages()
    quiz_indices = get_quiz_indices(pages)
    num_quizzes = len(quiz_indices)
    header = ["session_id"] + [f"quiz_{i}" for i in range(num_quizzes)]

    col = page_index_to_quiz_col(pages, page_index)
    if col is None:
        return

    lock_file = CSV_FILE.with_suffix(".lock")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            rows = []
            if CSV_FILE.exists():
                with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)

            session_row = None
            for i, row in enumerate(rows):
                if row and row[0] == session_id:
                    session_row = i
                    break

            if session_row is None:
                new_row = [""] * (num_quizzes + 1)
                new_row[0] = session_id
                new_row[col] = answer
                rows.append(new_row)
            else:
                rows[session_row][col] = answer

            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows[1:] if rows and rows[0][0] == "session_id" else rows)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    session_id = str(uuid.uuid4())
    response = RedirectResponse(url="/page/0")
    response.set_cookie("session_id", session_id)
    return response


@app.get("/page/{page_index}", response_class=HTMLResponse)
async def get_page(request: Request, page_index: int):
    pages = load_pages()
    if page_index >= len(pages):
        return RedirectResponse(url="/")

    page = pages[page_index]
    is_last = page_index >= len(pages) - 1

    if page["type"] == "info":
        return templates.TemplateResponse(request, "infopage.html", {
            "page": page,
            "page_index": page_index,
            "next_index": page_index + 1,
            "is_last": is_last,
        })
    elif page["type"] == "quiz":
        return templates.TemplateResponse(request, "quizpage.html", {
            "page": page,
            "page_index": page_index,
            "next_index": page_index + 1,
            "is_last": is_last,
        })
    elif page["type"] == "quiz_feedback":
        session_id = request.cookies.get("session_id", "")
        ref_page = page.get("ref_page", find_previous_quiz_page(pages, page_index))
        answer_result = read_answer(session_id, ref_page)
        is_correct = answer_result == "richtig"
        return templates.TemplateResponse(request, "feedbackpage.html", {
            "page": page,
            "page_index": page_index,
            "next_index": page_index + 1,
            "is_last": is_last,
            "is_correct": is_correct,
        })


@app.post("/answer/{page_index}", response_class=HTMLResponse)
async def answer(request: Request, page_index: int):
    form = await request.form()
    answer = form.get("answer", "")
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))

    pages = load_pages()
    page = pages[page_index]
    
    is_correct = ""
    if page["type"] == "quiz" and "correct_answer" in page:
        correct = page["correct_answer"]
        is_correct = "richtig" if answer == correct else "falsch"

    if page.get("save", True):
        save_answer(session_id, page_index, is_correct)

    next_index = page_index + 1
    redirect_url = "/" if next_index >= len(pages) else f"/page/{next_index}"

    return Response(headers={"HX-Redirect": redirect_url})
