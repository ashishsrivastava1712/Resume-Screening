# RecruitAI v2 - Resume Screening Application

A modern resume screening application using TF-IDF scoring with Supabase LLM integration.

## Features

- ✅ **TF-IDF Based Scoring** - Fast, keyword-based resume matching
- ✅ **Supabase Integration** - Enhanced evaluation with LLM fallback
- ✅ **Multiple File Formats** - Support for PDF, DOCX, DOC, TXT
- ✅ **Export Options** - CSV and Excel export
- ✅ **Production Ready** - Deployed on Railway + Vercel

## Project Structure

```
RecruitAI-Fresh/
├── app.py                 # Root entry point for gunicorn
├── requirements.txt       # Python dependencies
├── railway.toml          # Railway deployment config
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── Procfile              # Heroku/Railway process file
├── runtime.txt           # Python version
└── RecruitAI/
    ├── __init__.py
    ├── app.py            # Flask backend
    └── frontend/
        ├── index.html    # Web interface
        ├── app.js        # Frontend logic
        └── style.css     # Styling
```

## Setup

### Local Development

1. Clone the repository
2. Create Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

5. Add Supabase credentials to `.env`:
   ```
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

6. Run locally:
   ```bash
   python app.py
   ```
   Visit: http://localhost:5000

### Deployment to Railway

1. Push code to GitHub
2. In Railway Dashboard:
   - Create new project
   - Select GitHub repo
   - Configure environment variables (SUPABASE_URL, SUPABASE_KEY)
   - Deploy!

3. Update frontend API URL in `RecruitAI/frontend/app.js`:
   ```javascript
   const RAILWAY_BACKEND_URL = "https://your-railway-url.railway.app";
   ```

## Tech Stack

- **Backend**: Flask 3.0.3, Python 3.11
- **Scoring**: scikit-learn TF-IDF, Supabase LLM
- **File Processing**: PyPDF2, python-docx
- **Frontend**: Bootstrap 5, Vanilla JS
- **Deployment**: Railway (backend), Vercel (frontend)

## Endpoints

- `GET /` - Serve frontend
- `GET /health` - Health check
- `POST /screen` - Resume screening endpoint
- `GET /<path>` - Serve static assets

## License

MIT
