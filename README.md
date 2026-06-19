# FormRelay

A self-hosted form-to-email forwarding service — your own Web3Forms.  
Point any HTML form at a unique endpoint URL, and submissions land in your inbox.

```
┌──────────────┐   POST /f/{token}   ┌────────────────┐   SMTP   ┌──────────────┐
│  Your Form   │ ──────────────────► │   FormRelay    │ ───────► │  Your Email  │
└──────────────┘                     └────────────────┘          └──────────────┘
```

---

## Features

- **User accounts** – register, log in, manage your own endpoints
- **Unique endpoint URLs** – each endpoint gets a random token (`/f/<token>`)
- **Flexible intake** – accepts JSON, multipart/form-data, and URL-encoded forms
- **Email forwarding** – async SMTP delivery (Gmail, Mailgun, SendGrid, etc.)
- **Submission history** – view every submission and its delivery status
- **Redirect support** – send users to a thank-you page after submission
- **Dashboard SPA** – clean single-page UI, no framework required

---

## Quick Start

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/yourname/formrelay.git
cd formrelay
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt aiosqlite
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` – the minimum required fields:

```ini
SECRET_KEY=replace-with-a-long-random-string   # openssl rand -hex 32

# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # Gmail App Password
SMTP_FROM_EMAIL=you@gmail.com
```

> **Gmail App Password**: go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), create a password for "Mail / Other".  
> If you skip SMTP config, submissions are still stored but emails won't be sent.

### 4. Run

```bash
uvicorn main:app --reload
```

Open **http://localhost:8000** → register → create an endpoint → copy your URL.

---

## Using Your Endpoint

### HTML form

```html
<form action="http://localhost:8000/f/YOUR_TOKEN" method="POST">
  <input type="text"  name="name"    placeholder="Name" />
  <input type="email" name="email"   placeholder="Email" />
  <textarea           name="message"></textarea>
  <!-- Optional: redirect after submit -->
  <input type="hidden" name="_redirect" value="https://yoursite.com/thanks" />
  <button type="submit">Send</button>
</form>
```

### JavaScript / fetch

```js
fetch('http://localhost:8000/f/YOUR_TOKEN', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Alice', email: 'alice@example.com', message: 'Hi!' })
});
```

### curl

```bash
curl -X POST http://localhost:8000/f/YOUR_TOKEN \
  -F "name=Alice" -F "email=alice@example.com" -F "message=Hello"
```

---

## API Reference

All API routes are under `/api/`.  
Authentication uses an **HttpOnly cookie** (set on `/api/auth/login`) or  
a `Authorization: Bearer <token>` header.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in, get cookie |
| POST | `/api/auth/logout` | Clear cookie |
| GET  | `/api/auth/me` | Current user info |
| GET  | `/api/endpoints` | List your endpoints |
| POST | `/api/endpoints` | Create endpoint |
| GET  | `/api/endpoints/{id}` | Get endpoint |
| PATCH| `/api/endpoints/{id}` | Update endpoint |
| DELETE|`/api/endpoints/{id}` | Delete endpoint |
| POST | `/f/{token}` | **Public** – submit form data |
| GET  | `/api/submissions/{endpoint_id}` | Submission history |

Interactive docs: **http://localhost:8000/docs**

---

## Project Structure

```
formrelay/
├── main.py                    # FastAPI app, startup, routes
├── requirements.txt
├── .env.example
└── app/
    ├── core/
    │   ├── config.py          # Settings (pydantic-settings)
    │   ├── database.py        # Async SQLAlchemy engine + session
    │   ├── security.py        # JWT + bcrypt
    │   ├── email.py           # Async SMTP delivery
    │   └── deps.py            # FastAPI dependencies (auth)
    ├── models/
    │   ├── user.py            # User ORM model
    │   ├── endpoint.py        # Endpoint ORM model
    │   └── submission.py      # Submission ORM model
    ├── schemas/
    │   └── schemas.py         # Pydantic request/response models
    ├── routers/
    │   ├── auth.py            # /api/auth/*
    │   ├── endpoints.py       # /api/endpoints/*
    │   └── submissions.py     # /f/{token} + /api/submissions/*
    ├── templates/
    │   └── index.html         # Single-page frontend
    └── static/                # (CSS/JS assets if needed)
```

---

## Production Checklist

| Item | Detail |
|------|--------|
| **Secret key** | Set a long random `SECRET_KEY` in `.env` |
| **Database** | Switch `DATABASE_URL` to `postgresql+asyncpg://...` and run `alembic upgrade head` |
| **CORS** | Lock `allow_origins` in `main.py` to your actual domain |
| **HTTPS** | Put behind nginx / Caddy with TLS |
| **Process manager** | `gunicorn -k uvicorn.workers.UvicornWorker main:app` |
| **Rate limiting** | Add `slowapi` or nginx rate limits on `/f/{token}` |

---

## PostgreSQL (production)

```bash
pip install asyncpg psycopg2-binary
pip install alembic
alembic init alembic
# edit alembic/env.py to use async engine + import your models
alembic revision --autogenerate -m "init"
alembic upgrade head
```

Then set `DATABASE_URL=postgresql+asyncpg://user:pass@host/formrelay` in `.env`.

---

## License

MIT
