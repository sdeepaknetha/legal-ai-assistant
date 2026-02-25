from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔥 AUTO INSERT DEFAULT IPC SECTIONS
def seed_data():
    db = SessionLocal()
    if db.query(models.LegalSection).count() == 0:
        default_sections = [
            {"section": "302", "crime": "Murder", "punishment": "Life imprisonment or death"},
            {"section": "420", "crime": "Cheating", "punishment": "7 years imprisonment"},
            {"section": "376", "crime": "Rape", "punishment": "Rigorous imprisonment not less than 10 years"},
            {"section": "499", "crime": "Defamation", "punishment": "2 years imprisonment"},
            {"section": "378", "crime": "Theft", "punishment": "3 years imprisonment"},
        ]

        for item in default_sections:
            db.add(models.LegalSection(**item))

        db.commit()
    db.close()


seed_data()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})


@app.post("/add")
def add_section(
    section: str = Form(...),
    crime: str = Form(...),
    punishment: str = Form(...),
    db: Session = Depends(get_db)
):
    new_section = models.LegalSection(
        section=section,
        crime=crime,
        punishment=punishment
    )
    db.add(new_section)
    db.commit()
    return RedirectResponse(url="/all", status_code=303)


@app.post("/search_section", response_class=HTMLResponse)
def search_section(request: Request, section: str = Form(...), db: Session = Depends(get_db)):
    result = db.query(models.LegalSection)\
        .filter(models.LegalSection.section == section)\
        .first()

    if result:
        return templates.TemplateResponse("home.html", {"request": request, "result": result})
    else:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Section not found"})


@app.post("/search_crime", response_class=HTMLResponse)
def search_crime(request: Request, crime: str = Form(...), db: Session = Depends(get_db)):
    result = db.query(models.LegalSection)\
        .filter(models.LegalSection.crime.ilike(f"%{crime}%"))\
        .first()

    if result:
        return templates.TemplateResponse("home.html", {"request": request, "result": result})
    else:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Crime not found"})


@app.get("/section/{section_id}", response_class=HTMLResponse)
def section_detail(section_id: str, request: Request, db: Session = Depends(get_db)):
    section = db.query(models.LegalSection)\
        .filter(models.LegalSection.section == section_id)\
        .first()

    explanation = f"""
    Section {section.section} deals with {section.crime}.
    This offence is punishable with {section.punishment}.
    It is considered a serious legal offence under Indian Penal Code.
    """

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "section": section,
        "explanation": explanation
    })


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
