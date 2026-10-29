from http import HTTPStatus
from itertools import count
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException


USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Anna Nowak", "email": "anna.nowak@example.com"},
    2: {"id": 2, "name": "Jan Kowalski", "email": "jan.kowalski@example.com"},
    3: {"id": 3, "name": "Ewa Wiśniewska", "email": "ewa.wisniewska@example.com"},
}

PROJECTS: dict[int, dict] = {
    1: {"id": 1, "name": "TaskBoard", "description": "Aplikacja rozwijana na laboratoriach"},
    2: {"id": 2, "name": "Praca dyplomowa", "description": None},
}

TASKS: dict[int, dict] = {
    1: {"id": 1, "project_id": 1, "title": "Przygotować środowisko", "status": "done", "priority": "high", "assignee_id": 1},
    2: {"id": 2, "project_id": 1, "title": "Przeczytać RFC 9110", "status": "in_progress", "priority": "medium", "assignee_id": 2},
    3: {"id": 3, "project_id": 1, "title": "Zaprojektować API", "status": "open", "priority": "low", "assignee_id": None},
    4: {"id": 4, "project_id": 2, "title": "Wybrać temat", "status": "open", "priority": "high", "assignee_id": 3},
}

next_project_id = count(3)
next_task_id = count(5)

def not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Wartość nie może składać się z samych białych znaków")
    return value


Title = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(not_blank)]
Name = Annotated[str, Field(min_length=1, max_length=100), AfterValidator(not_blank)]
Description = Annotated[str, Field(max_length=500)]
Status = Literal["open", "in_progress", "done"]
Priority = Literal["low", "medium", "high"]

class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int
    title: Title
    status: Status = "open"
    priority: Priority = "medium"
    assignee_id: int | None = None

class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    status: Status | None = None
    priority: Priority | None = None
    assignee_id: int | None = None

    @field_validator("title", "status", "priority")
    @classmethod
    def reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Pole nie może mieć wartości null")
        return value


class TaskOut(BaseModel):
    id: int
    project_id: int
    title: str
    status: Status
    priority: Priority
    assignee_id: int | None


class TaskPage(BaseModel):
    items: list[TaskOut]
    total: int

class UserOut(BaseModel):
    id: int
    name: str


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    description: Description | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    task_count: int

class FieldError(BaseModel):
    location: str
    field: str
    message: str


class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    errors: list[FieldError] | None = None

app = FastAPI(title="TaskBoard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    expose_headers=["X-Total-Count"],
)


def problem(status: int, detail: str, errors: list[dict] | None = None, headers: dict | None = None) -> JSONResponse:
    body = Problem(title=HTTPStatus(status).phrase, status=status, detail=detail, errors=errors)
    return JSONResponse(
        body.model_dump(exclude_none=True),
        status_code=status,
        headers=headers,
        media_type="application/problem+json",
    )

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return problem(exc.status_code, str(exc.detail), headers=exc.headers)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    if any(error["type"] == "json_invalid" for error in exc.errors()):
        return problem(400, "Ciało żądania nie jest poprawnym dokumentem JSON")
    errors = [
        {
            "location": error["loc"][0],
            "field": ".".join(str(part) for part in error["loc"][1:]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return problem(422, "Dane wejściowe nie spełniają kontraktu API", errors)


def invalid_reference(field: str, message: str) -> RequestValidationError:
    return RequestValidationError([{"type": "invalid_reference", "loc": ("body", field), "msg": message}])


def get_task_or_404(task_id: int) -> dict:
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Zadanie {task_id} nie istnieje")
    return task

def get_project_or_404(project_id: int) -> dict:
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Projekt {project_id} nie istnieje")
    return project


def project_out(project: dict) -> dict:
    task_count = sum(1 for task in TASKS.values() if task["project_id"] == project["id"])
    return {**project, "task_count": task_count}


def check_unique_title(project_id: int, title: str, task_id: int | None = None) -> None:
    for task in TASKS.values():
        if task["project_id"] == project_id and task["title"] == title and task["id"] != task_id:
            raise HTTPException(status_code=409, detail="Zadanie o tym tytule już istnieje w projekcie")


@app.get("/")
def root():
    return {"message": "Hello Web"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/users", response_model=list[UserOut])
def list_users():
    return list(USERS.values())


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Użytkownik {user_id} nie istnieje")
    return user


@app.get("/projects", response_model=list[ProjectOut])
def list_projects():
    return [project_out(project) for project in PROJECTS.values()]


@app.post("/projects", status_code=201, response_model=ProjectOut)
def create_project(payload: ProjectCreate, response: Response):
    if any(project["name"] == payload.name for project in PROJECTS.values()):
        raise HTTPException(status_code=409, detail="Projekt o tej nazwie już istnieje")
    project_id = next(next_project_id)
    project = {"id": project_id, **payload.model_dump()}
    PROJECTS[project_id] = project
    response.headers["Location"] = f"/projects/{project_id}"
    return project_out(project)


@app.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    return project_out(get_project_or_404(project_id))


@app.get("/tasks", response_model=TaskPage)
def list_tasks(
    response: Response,
    status: Status | None = None,
    project_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items = list(TASKS.values())
    if status is not None:
        items = [task for task in items if task["status"] == status]
    if project_id is not None:
        items = [task for task in items if task["project_id"] == project_id]
    response.headers["X-Total-Count"] = str(len(items))
    return {"items": items[:limit], "total": len(items)}

@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate):
    task = get_task_or_404(task_id)
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes:
        check_unique_title(task["project_id"], changes["title"], task_id)
    task.update(changes)
    return task


@app.post("/tasks", status_code=201, response_model=TaskOut)
def create_task(payload: TaskCreate, response: Response):
    if payload.project_id not in PROJECTS:
        raise invalid_reference("project_id", f"Projekt {payload.project_id} nie istnieje")
    check_unique_title(payload.project_id, payload.title)
    task_id = next(next_task_id)
    task = {"id": task_id, **payload.model_dump()}
    TASKS[task_id] = task
    response.headers["Location"] = f"/tasks/{task_id}"
    return task


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    return get_task_or_404(task_id)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    get_task_or_404(task_id)
    del TASKS[task_id]
