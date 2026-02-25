from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from database import SessionLocal, engine
import models
import os
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

templates = Jinja2Templates(directory="templates")


# ----------------------------
# Seed Data From JSON
# ----------------------------
def seed_data():
    db = SessionLocal()

    if db.query(models.LegalSection).count() == 0:
        try:
            with open("ipc_data.json", "r") as file:
                data = json.load(file)

                for item in data:
                    new_section = models.LegalSection(
                        section=item["section"],
                        crime=item["crime"],
                        punishment=item["punishment"]
                    )
                    db.add(new_section)

                db.commit()

        except Exception as e:
            print("Error loading IPC data:", e)

    db.close()


seed_data()


# ----------------------------
# Home
# ----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------
# Login
# ----------------------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


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
# Show All with Pagination
# ----------------------------
@app.get("/all", response_class=HTMLResponse)
def show_all(request: Request, page: int = 1):
    db = SessionLocal()

    per_page = 10
    total = db.query(models.LegalSection).count()

    sections = db.query(models.LegalSection) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    db.close()

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "all.html",
        {
            "request": request,
            "sections": sections,
            "page": page,
            "total_pages": total_pages
        }
    )


# ----------------------------
# Search
# ----------------------------
@app.post("/search_section", response_class=HTMLResponse)
def search_section(request: Request, section: str = Form(...)):
    db = SessionLocal()
    result = db.query(models.LegalSection).filter(
        models.LegalSection.section == section
    ).all()
    db.close()

    return templates.TemplateResponse(
        "all.html",
        {"request": request, "sections": result, "page": 1, "total_pages": 1}
    )


@app.post("/search_crime", response_class=HTMLResponse)
def search_crime(request: Request, crime: str = Form(...)):
    db = SessionLocal()
    result = db.query(models.LegalSection).filter(
        models.LegalSection.crime.ilike(f"%{crime}%")
    ).all()
    db.close()

    return templates.TemplateResponse(
        "all.html",
        {"request": request, "sections": result, "page": 1, "total_pages": 1}
    )
