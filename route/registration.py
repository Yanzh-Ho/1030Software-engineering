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
    
    # Fetch activity details
    cursor.execute("SELECT * FROM activities WHERE id = %s;", (activity_id,))
    activity = cursor.fetchone()
    
    if not activity:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Get current participant count
    cursor.execute("SELECT COUNT(*) as total FROM registrations WHERE activity_id = %s;", (activity_id,))
    count_result = cursor.fetchone()
    participant_count = count_result["total"] if count_result else 0
    
    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("register.html", {
        "request": request, 
        "activity": activity, 
        "participant_count": participant_count
    })

@router.post("/register/{activity_id}")
def submit_registration(request: Request, activity_id: int, name: str = Form(...), phone: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch activity details to pass back to template
    cursor.execute("SELECT * FROM activities WHERE id = %s;", (activity_id,))
    activity = cursor.fetchone()
    
    # Get current participant count
    cursor.execute("SELECT COUNT(*) as total FROM registrations WHERE activity_id = %s;", (activity_id,))
    count_result = cursor.fetchone()
    participant_count = count_result["total"] if count_result else 0
    
    # Check for duplicate registration (Same Name and Phone for the same Activity)
    cursor.execute("SELECT id FROM registrations WHERE activity_id = %s AND name = %s AND phone = %s;", (activity_id, name, phone))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "activity": activity, 
            "participant_count": participant_count,
            "error": "You have already registered for this activity!"
        })

    # Insert new registration record
    cursor.execute("INSERT INTO registrations (activity_id, name, phone) VALUES (%s, %s, %s);", (activity_id, name, phone))
    conn.commit()
    
    # Update participant count after successful registration
    participant_count += 1
    
    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("register.html", {
        "request": request, 
        "activity": activity, 
        "participant_count": participant_count,
        "success": "Registration successful!"
    })