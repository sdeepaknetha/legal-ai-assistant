from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from database import SessionLocal, engine
import models
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

templates = Jinja2Templates(directory="templates")


# ----------------------------
# Seed Data
# ----------------------------
def seed_data():
    db = SessionLocal()
    if db.query(models.LegalSection).count() == 0:
        sections = [
            models.LegalSection(
                section="420",
                crime="Cheating",
                punishment="Imprisonment up to 7 years and fine"
            ),
            models.LegalSection(
                section="376",
                crime="Rape",
                punishment="Imprisonment not less than 10 years"
            ),
            models.LegalSection(
                section="354D",
                crime="Cyber Stalking",
                punishment="Imprisonment up to 3 years and fine"
            ),
        ]
        db.add_all(sections)
        db.commit()
    db.close()


seed_data()


# ----------------------------
# Home
# ----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------
# LOGIN PAGE (GET)
# ----------------------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ----------------------------
# LOGIN PROCESS (POST)
# ----------------------------
@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):

    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")

    if username == admin_user and password == admin_pass:
        request.session["user"] = username
        return RedirectResponse(url="/all", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid Credentials"
    })


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# ----------------------------
# Show All
# ----------------------------
@app.get("/all", response_class=HTMLResponse)
def show_all(request: Request):
    db = SessionLocal()
    sections = db.query(models.LegalSection).all()
    db.close()

    return templates.TemplateResponse(
        "all.html",
        {"request": request, "sections": sections}
    )


# ----------------------------
# Add Page
# ----------------------------
@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("add.html", {"request": request})


@app.post("/add")
def add_section(
    request: Request,
    section: str = Form(...),
    crime: str = Form(...),
    punishment: str = Form(...)
):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    new_section = models.LegalSection(
        section=section,
        crime=crime,
        punishment=punishment
    )
    db.add(new_section)
    db.commit()
    db.close()

    return RedirectResponse(url="/all", status_code=303)


# ----------------------------
# Edit Page
# ----------------------------
@app.get("/edit/{section_id}", response_class=HTMLResponse)
def edit_page(request: Request, section_id: int):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    section = db.query(models.LegalSection).filter(
        models.LegalSection.id == section_id
    ).first()
    db.close()

    if not section:
        return RedirectResponse(url="/all", status_code=303)

    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "section": section}
    )


@app.post("/edit/{section_id}")
def update_section(
    request: Request,
    section_id: int,
    section: str = Form(...),
    crime: str = Form(...),
    punishment: str = Form(...)
):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    db_section = db.query(models.LegalSection).filter(
        models.LegalSection.id == section_id
    ).first()

    if db_section:
        db_section.section = section
        db_section.crime = crime
        db_section.punishment = punishment
        db.commit()

    db.close()
    return RedirectResponse(url="/all", status_code=303)


# ----------------------------
# Delete
# ----------------------------
@app.get("/delete/{section_id}")
def delete_section(request: Request, section_id: int):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    section = db.query(models.LegalSection).filter(
        models.LegalSection.id == section_id
    ).first()

    if section:
        db.delete(section)
        db.commit()

    db.close()
    return RedirectResponse(url="/all", status_code=303)