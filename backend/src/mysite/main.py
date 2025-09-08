from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId, Binary
import uuid
import os

MONGODB_CONNECTION_STRING = os.environ["MONGODB_CONNECTION_STRING"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
db = client["mybooks"]
todos_collection = db["todos"]

class TodoItem(BaseModel):
    id: uuid.UUID
    content: str

class TodoItemCreate(BaseModel):
    content: str

def todo_helper(todo) -> dict:
    return {
        "id": todo["id"].as_uuid() if isinstance(todo["id"], Binary) else todo["id"],
        "content": todo["content"]
    }

@app.post("/todos", response_model=TodoItem)
async def create_todo(item: TodoItemCreate):
    new_id = uuid.uuid4()
    todo_doc = {"id": Binary.from_uuid(new_id), "content": item.content}
    await todos_collection.insert_one(todo_doc)
    # Hole das gespeicherte Dokument, um die UUID korrekt zurückzugeben
    todo = await todos_collection.find_one({"id": Binary.from_uuid(new_id)})
    return todo_helper(todo)

@app.get("/todos", response_model=list[TodoItem])
async def read_todos():
    todos = []
    async for todo in todos_collection.find():
        todos.append(todo_helper(todo))
    return todos

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: uuid.UUID):
    result = await todos_collection.delete_one({"id": Binary.from_uuid(todo_id)})
    if result.deleted_count == 1:
        return {"message": "Todo deleted successfully"}
    raise HTTPException(status_code=404, detail="Todo not found")