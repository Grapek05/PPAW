from fastapi import FastAPI, Response
from pydantic import BaseModel

app = FastAPI(title="TaskBoard")

class TaskIn(BaseModel):
    title: str
    status: str = "open"
    priority: str = "medium"

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Przygotować środowisko",
        "status": "done", "priority": "high"},
    2: {"id": 2, "title": "Przeczytać RFC 9110",
        "status": "open", "priority": "medium"}
}

NEXT_ID = 3

@app.get("/tasks")
def list_tasks():
    return {"items": list(TASKS.values()), "total": len(TASKS)}

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    return task


@app.get("/")
def root():
    return {"message": "Hello Web"}

@app.get("/health")
def root():
    return {"status":"ok"}

@app.get("/tasks")
def list_tasks(status: str | None = None, limit: int = 20):
    items = list(TASKS.values())
    if status is not None:
        items = [t for t in intems if t ["status"] == status]
    return {"items": items[:limit], "total": len(items)}

@app.post("/tasks", status_code=201)
def create_task(payload: TaskIn, response: Response):
        task = {
        "id": NEXT_ID,
        "title": payload["title"],
        "status": payload.get("status", "open"),
    }
        response.headers["Location"] = f"/tasks/{NEXT_ID}"
        return task
    
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    del TASKS[task_id]