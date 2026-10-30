from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor
from DB import get_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="template")

@router.get("/register/{activity_id}", response_class=HTMLResponse)
def show_registration_form(request: Request, activity_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM activities WHERE id = %s;", (activity_id,))
    activity = cursor.fetchone()
    cursor.close()
    conn.close()
    if not activity:
        raise HTTPException(status_code=404, detail="Kegiatan tidak ditemukan")
    return templates.TemplateResponse("register.html", {"request": request, "activity": activity})

@router.post("/register/{activity_id}")
def submit_registration(request: Request, activity_id: int, name: str = Form(...), phone: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Cek duplikat
    cursor.execute("SELECT id FROM registrations WHERE activity_id = %s AND name = %s AND phone = %s;", (activity_id, name, phone))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return templates.TemplateResponse("register.html", {"request": request, "activity": {"id": activity_id}, "error": "Anda sudah mendaftar di kegiatan ini!"})

    cursor.execute("INSERT INTO registrations (activity_id, name, phone) VALUES (%s, %s, %s);", (activity_id, name, phone))
    conn.commit()
    cursor.close()
    conn.close()
    return templates.TemplateResponse("register.html", {"request": request, "activity": {"id": activity_id}, "success": "Pendaftaran berhasil!"})