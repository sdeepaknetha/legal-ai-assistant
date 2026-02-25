from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
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
