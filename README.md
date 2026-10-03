# HerStyle AI

HerStyle AI is a fashion wardrobe assistant with:

- FastAPI backend for authentication, wardrobe management, image analysis and outfit recommendations.
- AI/CV pipeline for background removal, clothing attributes and compatibility scoring.
- PostgreSQL database with Alembic migrations.
- Next.js web frontend for the wardrobe, recognition, AI Stylist, planner and chat flows.

This repository intentionally contains source code and the small runtime model checkpoints needed by the API. It does **not** contain user uploads, database dumps, training datasets, virtual environments, dependency folders, model caches or secrets.

## Repository layout

```text
ai/
  src/herstyle_ai/       Backend, model inference and recommendation code
  alembic/                PostgreSQL schema migrations
  configs/                Model and styling configuration
  outputs/                Selected runtime checkpoints only
  requirements-*.txt     Python dependencies
herstyleai-client/
  apps/web/               Next.js web application
```

## Requirements

- Windows, macOS or Linux
- Python 3.10+
- Node.js 20+
- PostgreSQL 14+
- 8 GB RAM minimum; NVIDIA CUDA is recommended for faster inference
- Internet access on the first AI run so Hugging Face/rembg model assets can be downloaded

## 1. Clone the repository

```powershell
git clone https://github.com/kasum00/stt.git
Set-Location stt
```

On Windows, the fastest setup is:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```

The script creates the Python environment, installs the backend and frontend dependencies, and creates the local `.env` files from the safe templates. It does not create PostgreSQL databases or overwrite existing environment files.

## 2. Configure PostgreSQL

Create an empty database named `herstyleai`, then copy the backend environment template:

```powershell
createdb herstyleai
Set-Location .\ai
Copy-Item .env.example .env
```

Edit `ai/.env` and set at least:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/herstyleai
JWT_SECRET_KEY=replace-with-a-random-secret-at-least-32-characters
STORAGE_BACKEND=local
STORAGE_ROOT=./runtime-data
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Never commit `.env` or real credentials.

## 3. Install and run the backend

After PostgreSQL is configured, run this in a terminal from the repository root:

```powershell
.\scripts\start-backend.ps1
```

This applies the Alembic migrations and starts the API. Keep this terminal open.

The manual commands below are equivalent if you prefer to run each step yourself.

From the repository root:

```powershell
Set-Location .\ai
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements-backend.txt
pip install torch torchvision
pip install -r requirements-ai.txt

$env:PYTHONPATH = "$PWD\src"
alembic upgrade head
python -m uvicorn herstyle_ai.api.app:app --host 127.0.0.1 --port 8000 --reload
```

For an NVIDIA GPU, install the CUDA-compatible PyTorch build from the official PyTorch instructions instead of the default CPU build. The API will fall back to CPU when CUDA is unavailable, but image recognition and compatibility scoring will be slower.

Backend health check: <http://127.0.0.1:8000/health>  
API docs: <http://127.0.0.1:8000/docs>

The first startup may download Hugging Face/rembg assets and load the compatibility model. Keep the backend terminal open.

## 4. Install and run the web frontend

Open a second terminal from the repository root and run:

```powershell
.\scripts\start-web.ps1
```

The frontend helper creates `.env.local` when needed, installs npm packages, and starts Next.js.

The manual commands below are equivalent:

Open a second terminal from the repository root:

```powershell
Set-Location .\herstyleai-client\apps\web
npm install
Copy-Item .env.example .env.local
npm run dev
```

The default `NEXT_PUBLIC_API_BASE_URL` is `http://127.0.0.1:8000`. Open <http://localhost:3000> after the Next.js server is ready.

The browser communicates with FastAPI only. It never connects directly to PostgreSQL, and no backend secret belongs in `.env.local`.

## Main flows

1. Register or log in.
2. Upload one or more clothing images in **Nhận diện trang phục**.
3. Review the AI attributes and add the recognized item to the wardrobe.
4. Open **AI Stylist** and create a weekly outfit recommendation.
5. View saved outfits and the weekly planner.

The first outfit recommendation can take longer while image features are extracted. Subsequent recommendations are faster while the backend process remains running.

The repository includes the runtime checkpoints required by the local AI pipeline. Hugging Face/rembg assets are downloaded on first use, so the first recognition request needs internet access and can take longer than later requests.

## Verification

Backend:

```powershell
Set-Location .\ai
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$PWD\src"
pytest
```

Frontend:

```powershell
Set-Location .\herstyleai-client\apps\web
npm run typecheck
npm run lint
npm run build
```

## Production notes

- Use a managed PostgreSQL database and run `alembic upgrade head` during deployment.
- Set a strong random `JWT_SECRET_KEY` and use HTTPS.
- Set `REFRESH_COOKIE_SECURE=true` in production.
- Use a persistent object-storage or volume-backed `STORAGE_ROOT` for uploaded images.
- Set `FRONTEND_ORIGINS` and `TRUSTED_HOSTS` to the real deployment domains.
- Do not commit `.env`, user images, database backups, generated reports, or model caches.
- For public deployment, serve the frontend and API from stable HTTPS URLs and update `NEXT_PUBLIC_API_BASE_URL` accordingly.
