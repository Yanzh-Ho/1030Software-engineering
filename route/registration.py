import sqlite3
from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="template")


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_event(conn, event_id):
    return conn.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()


# 1. 顯示報名表
@router.get("/register/{event_id}", response_class=HTMLResponse)
def show_registration_form(request: Request, event_id: int):
    conn = get_db()
    event = get_event(conn, event_id)
    conn.close()
    if not event:
        raise HTTPException(status_code=404, detail="找不到該活動")
    return templates.TemplateResponse(
        request, "register.html", {"event": event}
    )


# 2. 送出報名（含防重複）
@router.post("/register/{event_id}", response_class=HTMLResponse)
def submit_registration(
    request: Request,
    event_id: int,
    name: str = Form(...),
    phone: str = Form(...),
):
    conn = get_db()
    event = get_event(conn, event_id)
    if not event:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到該活動")

    if event["is_closed"]:
        conn.close()
        return templates.TemplateResponse(
            request, "register.html",
            {"event": event, "error": "此活動已截止報名"},
        )

    dup = conn.execute(
        "SELECT id FROM registrations WHERE event_id = ? AND name = ? AND phone = ?",
        (event_id, name, phone),
    ).fetchone()
    if dup:
        conn.close()
        return templates.TemplateResponse(
            request, "register.html",
            {"event": event, "error": "您已報名過此活動！"},
        )

    conn.execute(
        "INSERT INTO registrations (event_id, name, phone) VALUES (?, ?, ?)",
        (event_id, name, phone),
    )
    conn.commit()
    conn.close()
    return templates.TemplateResponse(
        request, "register.html",
        {"event": event, "success": "報名成功！"},
    )


# 3. 查看活動報名清單
@router.get("/events/{event_id}/registrations", response_class=HTMLResponse)
def show_registrations(request: Request, event_id: int):
    conn = get_db()
    event = get_event(conn, event_id)
    if not event:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到該活動")
    rows = conn.execute(
        "SELECT name, phone, created_at FROM registrations "
        "WHERE event_id = ? ORDER BY created_at",
        (event_id,),
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(
        request, "registrations.html",
        {"event": event, "registrations": rows},
    )