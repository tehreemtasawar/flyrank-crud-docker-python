from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3

class CreateTask(BaseModel):
    title: Optional[str] = None

app=FastAPI()

def get_connection():
    return sqlite3.connect("tasks.db")

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL
        )
    """)
    cursor = conn.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy groceries", False))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Clean the Room", False))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Complete assignment", True))
    conn.commit()
    conn.close()

init_db()

@app.get("/", summary="API info")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", summary="Health check")
def health():
    return { "status": "ok" }

@app.get("/tasks", summary="List all tasks")
def get_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
    conn.close()
    result = [{"id": row[0], "title": row[1], "done": bool(row[2])} for row in rows]
    return result

@app.get("/tasks/{task_id}", summary="Get a single task")
def get_one_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )
    return {"id": row[0], "title": row[1], "done": bool(row[2])}

@app.post("/tasks", summary="Create a new task")
def create_task(new_task: CreateTask):
    if not new_task.title or not new_task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"}
        )
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (new_task.title, False)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    task = {"id": new_id, "title": new_task.title, "done": False}
    return JSONResponse(status_code=201, content=task)

class UpdateTask(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, updates: UpdateTask):
    conn = get_connection()
    row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )
    new_title = updates.title if updates.title is not None else row[1]
    new_done = updates.done if updates.done is not None else bool(row[2])
    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id)
    )
    conn.commit()
    conn.close()
    return {"id": task_id, "title": new_title, "done": new_done}

@app.delete("/tasks/{task_id}", summary="Delete a task")
def delete_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=204, content=None)