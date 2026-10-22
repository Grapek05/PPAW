from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TaskBoard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["GET", "POST"],
)


TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Przygotować środowisko", "status": "done", "priority": "high"},
    2: {"id": 2, "title": "Przeczytać RFC 9110", "status": "open", "priority": "medium"},
    3: {"id": 3, "title": "Zaprojektować API", "status": "open", "priority": "low"},
}

NEXT_ID = 4


class TaskIn(BaseModel):
    title: str
    status: str = "open"
    priority: str = "medium"


def find_by_title(title: str) -> dict | None:
    for task in TASKS.values():
        if task["title"] == title:
            return task
    return None


@app.get("/")
def root():
    return {"message": "Hello Web"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(response: Response, status: str | None = None, limit: int = 20):
    items = list(TASKS.values())
    if status is not None:
        items = [task for task in items if task["status"] == status]
    response.headers["X-Total-Count"] = str(len(items))
    return {"items": items[:limit], "total": len(items)}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    return task


@app.post("/tasks", status_code=201)
def create_task(payload: TaskIn, response: Response):
    global NEXT_ID
    if find_by_title(payload.title) is not None:
        raise HTTPException(status_code=409, detail="Zadanie o tym tytule już istnieje")
    task = {
        "id": NEXT_ID,
        "title": payload.title,
        "status": payload.status,
        "priority": payload.priority,
    }
    TASKS[NEXT_ID] = task
    response.headers["Location"] = f"/tasks/{NEXT_ID}"
    NEXT_ID += 1
    return task


@app.put("/tasks/{task_id}")
def replace_task(task_id: int, payload: TaskIn):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    task = {
        "id": task_id,
        "title": payload.title,
        "status": payload.status,
        "priority": payload.priority,
    }
    TASKS[task_id] = task
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    del TASKS[task_id]
