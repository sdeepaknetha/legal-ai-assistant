from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🔐 Session Middleware
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

templates = Jinja2Templates(directory="templates")


# 🔑 ADMIN CREDENTIALS
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔥 Seed Data
def seed_data():
    db = SessionLocal()
    if db.query(models.LegalSection).count() == 0:
        default_sections = [
            {"section": "302", "crime": "Murder", "punishment": "Life imprisonment or death"},
            {"section": "420", "crime": "Cheating", "punishment": "7 years imprisonment"},
        ]
        for item in default_sections:
            db.add(models.LegalSection(**item))
        db.commit()
    db.close()


seed_data()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


# 🔐 LOGIN PAGE
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse(url="/add", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid credentials"
    })


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# 🔐 PROTECTED ADD PAGE
@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("add.html", {"request": request})


@app.post("/add")
def add_section(
    request: Request,
    section: str = Form(...),
    crime: str = Form(...),
    punishment: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("admin"):
        return RedirectResponse(url="/login", status_code=303)

    new_section = models.LegalSection(
        section=section,
        crime=crime,
        punishment=punishment
    )
    db.add(new_section)
    db.commit()
    return RedirectResponse(url="/all", status_code=303)


@app.get("/all", response_class=HTMLResponse)
def view_all(request: Request, page: int = 1, db: Session = Depends(get_db)):
    per_page = 10
    total_records = db.query(models.LegalSection).count()
    total_pages = (total_records + per_page - 1) // per_page

    sections = db.query(models.LegalSection)\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()

    return templates.TemplateResponse("all.html", {
        "request": request,
        "sections": sections,
        "page": page,
        "total_pages": total_pages
    })
