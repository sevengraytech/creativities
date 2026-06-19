"""
main.py
FormRelay – FastAPI application entry point.

Run locally:
    uvicorn main:app --reload

Run in Docker:
    docker compose up --build
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.database import init_db
from app.core.deps import get_optional_current_user
from app.models.user import User
from app.routers import auth, endpoints, submissions, admin
from app.routers import chat, subscriptions, admin_subscriptions

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()      # create tables + seed admin
    yield


app = FastAPI(
    title="FormRelay",
    description="Form-to-email forwarding service",
    version="1.1.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static & templates ────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(endpoints.router)
app.include_router(submissions.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(subscriptions.router)
app.include_router(admin_subscriptions.router)


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "base_url": settings.BASE_URL}
    )


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})


@app.get("/forgot-password", response_class=HTMLResponse, include_in_schema=False)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
async def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse, include_in_schema=False)
async def pricing_page(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})


@app.get("/subscribe", response_class=HTMLResponse, include_in_schema=False)
async def subscribe_page(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("subscribe.html", {"request": request})


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/admin-dashboard", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard_page(
    request: Request,
    current_user: User | None = Depends(get_optional_current_user),
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    if not current_user.is_admin:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def spa_catch_all(request: Request, full_path: str):
    if full_path.startswith("api") or full_path.startswith("static"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "base_url": settings.BASE_URL},
    )
