# Akhar Light Billing — Local Dev & Deployment

This repository contains a small React frontend (Vite) and FastAPI backend to create invoices and letter pads with Gujarati support.

Repository layout
- backend/
  - app/main.py             # FastAPI app and endpoints
  - templates/              # Jinja2 templates (bill_template.html, letter_pad_demo.html)
  - templates/fonts/        # fonts (NotoSansGujarati.ttf)
  - requirements.txt       # Python deps
- frontend/
  - src/App.jsx            # Main React app
  - index.html, package.json
- bill_template.html       # standalone templates (development)

Quick local run (macOS)
1. Backend
   - Create a Python venv and install deps:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

   - (Optional) If using WeasyPrint on macOS install system libs:

   ```bash
   brew install pango cairo gdk-pixbuf glib libffi
   ```

   - Set env vars (see `.env.example`) and run:

   ```bash
   export OPENAI_API_KEY="your_key_here"  # if using AI features
   uvicorn app.main:app --reload --port 8000 --app-dir backend/app
   ```

2. Frontend

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Notes about persistence and users
- Currently the app stores invoices and letters in `localStorage` per browser user. Keys are scoped by email (logged-in user). This means saved letters and invoices are visible only inside the browser profile and account that created them.
- For production (multi-user server), migrate storage to a backend DB (Postgres/SQLite) and add authentication.

Environment / deployment notes
- Add `.env` with `OPENAI_API_KEY` to enable AI autofill endpoints.
- In production, serve the built frontend (`npm run build`) from a static server and run the FastAPI app with a process manager (gunicorn/uvicorn + systemd).

Deploying to Railway (frontend + backend)
- This repo can be deployed to Railway as two services: a static frontend and a Dockerized backend (required for WeasyPrint). High-level steps:
  1. Frontend (Static):
     - Build the frontend: `cd frontend && npm install && npm run build`.
     - In Railway create a new Static Site service or a Node service pointing to the `frontend/` directory. Set `Build Command` to `npm run build` and `Publish Directory` to `dist`.
     - Set the frontend environment variable `VITE_API_URL` to the backend service URL after you create the backend service.
  2. Backend (Docker):
     - Railway's default Python environment may not include the native libs WeasyPrint needs. Use the provided `backend/Dockerfile` to ensure the correct system packages are available.
     - In Railway create a new Service and choose Dockerfile deploy, or in the project set the `Dockerfile` path to `backend/Dockerfile`.
     - Configure environment variables in Railway for `OPENAI_API_KEY` and any other secrets.
     - Railway will build the Docker image and run the backend; copy the produced service URL and paste into the frontend `VITE_API_URL`.

Notes & tips
- Fonts: I copied the Gujarati font to `public/fonts/NotoSansGujarati-Regular.ttf` and updated templates to load `/fonts/NotoSansGujarati-Regular.ttf`. This ensures static pages on Railway or Vercel can load the font directly.
- CORS: enable CORS in `backend/app/main.py` so the frontend can call `/api` endpoints from the deployed domain.
- Quick test (locally): serve the root folder and open `bill_template.html`:

```bash
python -m http.server 5173
# or
npx serve . -l 5173
```

- If you want, I can:
  - Add a `railway.json` template or GitHub Action to automate deployment.
  - Deploy both services to Railway for you (you'll need to connect your GitHub and allow Railway access).

Contact
- Tell me if you want me to push a `railway.json` and set up GitHub -> Railway automated deploys, or if you want me to deploy the services directly (I'll need your Railway project access).
# Akhar Light Billing

Project structure:

- `frontend/` React app with the billing UI.
- `backend/` Python FastAPI service that renders the bill template and returns PDF output.
- `bill_template.html` visual reference of the paper layout.

Run locally:

1. Start the backend from `backend/`:
   - create a virtual environment
   - install `requirements.txt`
   - run `uvicorn app.main:app --reload --port 8000`
2. Start the frontend from `frontend/`:
   - run `npm install`
   - run `npm run dev`

The frontend sends invoice data to `POST /api/invoice/pdf`, and the backend generates the PDF using the bill template layout.
