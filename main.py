import csv
import fcntl
import random
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

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DEFAULT_YAML_FILES = ["pages.yaml", "pages2.yaml"]


def get_available_yaml_files():
    available = [name for name in DEFAULT_YAML_FILES if (BASE_DIR / name).exists()]
    return available if available else ["pages.yaml"]


def get_csv_file(yaml_file):
    yaml_name = Path(yaml_file).stem
    return BASE_DIR / "data" / f"answers_{yaml_name}.csv"


def load_pages(yaml_file=None):
    if yaml_file is None:
        yaml_file = "pages.yaml"
    yaml_path = BASE_DIR / yaml_file
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["pages"]


def read_answer(session_id: str, page_index: int, yaml_file=None):
    csv_file = get_csv_file(yaml_file or "pages.yaml")
    if not csv_file.exists():
        return None
    
    pages = load_pages(yaml_file)
    col = page_index_to_quiz_col(pages, page_index)
    if col is None:
        return None
    
    lock_file = csv_file.with_suffix(".lock")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_SH)
        try:
            with open(csv_file, "r", newline="", encoding="utf-8") as f:
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


def get_input_indices(pages):
    return [i for i, p in enumerate(pages) if p["type"] == "input"]


def get_slider_indices(pages):
    return [i for i, p in enumerate(pages) if p["type"] == "slider"]


def count_total_sliders(pages):
    total = 0
    for p in pages:
        if p["type"] == "slider":
            total += len(p.get("sliders", []))
    return total


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


def page_index_to_input_col(pages, page_index):
    quiz_indices = get_quiz_indices(pages)
    input_indices = get_input_indices(pages)
    if page_index in input_indices:
        return len(quiz_indices) + input_indices.index(page_index) + 1
    return None


def page_index_to_slider_col(pages, page_index):
    quiz_indices = get_quiz_indices(pages)
    input_indices = get_input_indices(pages)
    slider_indices = get_slider_indices(pages)
    
    if page_index in slider_indices:
        base_col = len(quiz_indices) + len(input_indices) + 1
        slider_offset = 0
        for idx in slider_indices:
            if idx == page_index:
                return base_col + slider_offset
            slider_offset += len(pages[idx].get("sliders", []))
    return None


def save_answer(session_id: str, page_index: int, answer: str, yaml_file=None):
    csv_file = get_csv_file(yaml_file or "pages.yaml")
    pages = load_pages(yaml_file)
    quiz_indices = get_quiz_indices(pages)
    input_indices = get_input_indices(pages)
    slider_indices = get_slider_indices(pages)
    num_quizzes = len(quiz_indices)
    num_inputs = len(input_indices)
    total_sliders = count_total_sliders(pages)
    
    header = (["session_id"] + 
              [f"quiz_{i}" for i in range(num_quizzes)] + 
              [f"input_{i}" for i in range(num_inputs)] +
              [f"slider_{i}" for i in range(total_sliders)])

    col = page_index_to_quiz_col(pages, page_index)
    if col is None:
        col = page_index_to_input_col(pages, page_index)
    if col is None:
        col = page_index_to_slider_col(pages, page_index)
    if col is None:
        return

    lock_file = csv_file.with_suffix(".lock")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            rows = []
            if csv_file.exists():
                with open(csv_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)

            session_row = None
            for i, row in enumerate(rows):
                if row and row[0] == session_id:
                    session_row = i
                    break

            if session_row is None:
                new_row = [""] * (num_quizzes + num_inputs + total_sliders + 1)
                new_row[0] = session_id
                new_row[col] = answer
                rows.append(new_row)
            else:
                rows[session_row][col] = answer

            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows[1:] if rows and rows[0][0] == "session_id" else rows)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def save_slider_answers(session_id: str, page_index: int, values: list, yaml_file=None):
    csv_file = get_csv_file(yaml_file or "pages.yaml")
    pages = load_pages(yaml_file)
    quiz_indices = get_quiz_indices(pages)
    input_indices = get_input_indices(pages)
    slider_indices = get_slider_indices(pages)
    num_quizzes = len(quiz_indices)
    num_inputs = len(input_indices)
    total_sliders = count_total_sliders(pages)
    
    header = (["session_id"] + 
              [f"quiz_{i}" for i in range(num_quizzes)] + 
              [f"input_{i}" for i in range(num_inputs)] +
              [f"slider_{i}" for i in range(total_sliders)])

    base_col = page_index_to_slider_col(pages, page_index)
    if base_col is None:
        return

    lock_file = csv_file.with_suffix(".lock")
    with open(lock_file, "w") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            rows = []
            if csv_file.exists():
                with open(csv_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)

            session_row = None
            for i, row in enumerate(rows):
                if row and row[0] == session_id:
                    session_row = i
                    break

            if session_row is None:
                new_row = [""] * (num_quizzes + num_inputs + total_sliders + 1)
                new_row[0] = session_id
                for idx, value in enumerate(values):
                    new_row[base_col + idx] = value
                rows.append(new_row)
            else:
                for idx, value in enumerate(values):
                    rows[session_row][base_col + idx] = value

            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows[1:] if rows and rows[0][0] == "session_id" else rows)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    session_id = str(uuid.uuid4())
    yaml_file = random.choice(get_available_yaml_files())
    response = RedirectResponse(url="/page/0")
    response.set_cookie("session_id", session_id)
    response.set_cookie("yaml_file", yaml_file)
    return response


@app.get("/page/{page_index}", response_class=HTMLResponse)
async def get_page(request: Request, page_index: int):
    yaml_file = request.cookies.get("yaml_file", "pages.yaml")
    pages = load_pages(yaml_file)
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
        answer_result = read_answer(session_id, ref_page, yaml_file)
        is_correct = answer_result == "richtig"
        return templates.TemplateResponse(request, "feedbackpage.html", {
            "page": page,
            "page_index": page_index,
            "next_index": page_index + 1,
            "is_last": is_last,
            "is_correct": is_correct,
        })
    elif page["type"] == "input":
        return templates.TemplateResponse(request, "inputpage.html", {
            "page": page,
            "page_index": page_index,
            "next_index": page_index + 1,
            "is_last": is_last,
        })
    elif page["type"] == "slider":
        return templates.TemplateResponse(request, "sliderpage.html", {
            "page": page,
            "page_index": page_index,
            "next_index": page_index + 1,
            "is_last": is_last,
        })


@app.post("/answer/{page_index}", response_class=HTMLResponse)
async def answer(request: Request, page_index: int):
    form = await request.form()
    answer = form.get("answer", "")
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    yaml_file = request.cookies.get("yaml_file", "pages.yaml")

    pages = load_pages(yaml_file)
    page = pages[page_index]
    
    save_value = ""
    if page["type"] == "quiz" and "correct_answer" in page:
        correct = page["correct_answer"]
        save_value = "richtig" if answer == correct else "falsch"
    elif page["type"] == "input":
        save_value = answer
    elif page["type"] == "slider":
        slider_values = []
        for i in range(len(page.get("sliders", []))):
            slider_values.append(form.get(f"slider_{i}", ""))
        if page.get("save", True):
            save_slider_answers(session_id, page_index, slider_values, yaml_file)
        next_index = page_index + 1
        redirect_url = "/" if next_index >= len(pages) else f"/page/{next_index}"
        return Response(headers={"HX-Redirect": redirect_url})

    if page.get("save", True):
        save_answer(session_id, page_index, save_value, yaml_file)

    next_index = page_index + 1
    redirect_url = "/" if next_index >= len(pages) else f"/page/{next_index}"

    return Response(headers={"HX-Redirect": redirect_url})
