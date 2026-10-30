import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from route.registration import router as registration_router
app.include_router(registration_router)

app = FastAPI(title="活動報名系統")

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# 讀取剛剛 push 的 schema.sql 初始化資料庫
def init_db():
    conn = get_db()
    with open("schema.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.commit()
    conn.close()

init_db()

class EventCreate(BaseModel):
    title: str
    description: str = ""

# 1. 基本款：新增新的活動
@app.post("/api/events")
def create_event(event: EventCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (title, description) VALUES (?, ?)",
        (event.title, event.description)
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return {"message": "活動新增成功", "event_id": event_id}

# 2. Pro版：增加截止報名功能
@app.put("/api/events/{event_id}/close")
def close_event(event_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM events WHERE id = ?", (event_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="找不到該活動")
        
    cursor.execute("UPDATE events SET is_closed = 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return {"message": f"活動編號 {event_id} 已成功截止報名"}