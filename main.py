import sqlite3
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="活動報名系統")

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

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

class RegisterCreate(BaseModel):
    name: str
    phone: str

# ----------------- 前端首頁 -----------------
@app.get("/")
def serve_index():
    return FileResponse("index.html")

# ----------------- 功能 1：新增活動 -----------------
@app.post("/api/events")
def create_event(event: EventCreate):
    if not event.title.strip():
        raise HTTPException(status_code=400, detail="活動名稱不得為空！")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (title, description) VALUES (?, ?)",
        (event.title.strip(), event.description.strip())
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return {"message": "活動新增成功！", "event_id": event_id}

# ----------------- 功能 2：截止報名 -----------------
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

# ----------------- 功能 3：活動清單與報名人數 -----------------
@app.get("/api/events")
def list_events():
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT e.id, e.title, e.description, e.is_closed, COUNT(r.id) as participant_count
    FROM events e
    LEFT JOIN registrations r ON e.id = r.event_id
    GROUP BY e.id
    ORDER BY e.id DESC
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# ----------------- 功能 4：報名活動（含電話驗證與防重複） -----------------
@app.post("/api/events/{event_id}/register")
def register_event(event_id: int, data: RegisterCreate):
    # 嚴格電話驗證：必須符合台灣手機 09 開頭 10 碼數字，或一般電話 7~10 碼純數字
    phone_cleaned = re.sub(r"[\s-]", "", data.phone)
    if not re.match(r"^09\d{8}$", phone_cleaned) and not re.match(r"^\d{7,10}$", phone_cleaned):
        raise HTTPException(status_code=400, detail="電話格式不正確！請輸入有效的電話號碼（例如：0912345678）")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT is_closed FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    if not event:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到該活動")
    if event["is_closed"] == 1:
        conn.close()
        raise HTTPException(status_code=400, detail="該活動已截止報名！")

    cursor.execute(
        "SELECT id FROM registrations WHERE event_id = ? AND name = ? AND phone = ?",
        (event_id, data.name.strip(), phone_cleaned)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="您已報名過此活動，請勿重複報名！")

    cursor.execute(
        "INSERT INTO registrations (event_id, name, phone) VALUES (?, ?, ?)",
        (event_id, data.name.strip(), phone_cleaned)
    )
    conn.commit()
    conn.close()
    return {"message": "報名成功！"}

# ----------------- 功能 5：查看報名清單 -----------------
@app.get("/api/events/{event_id}/registrations")
def get_event_registrations(event_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, phone, created_at FROM registrations WHERE event_id = ? ORDER BY id ASC",
        (event_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows