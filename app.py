# legal_faq_api/app.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd
import logging

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal FAQ API")

# Allow CORS for local development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CSV robustly relative to this file
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "cleaned_legal_faq.csv"

def load_faq_df(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        # Ensure there's an id column; create one if not present
        if "id" not in df.columns:
            df.insert(0, "id", range(1, len(df) + 1))
        return df
    except FileNotFoundError:
        logger.error(f"CSV file not found at {path}")
        return pd.DataFrame(columns=["id", "question", "answer"])
    except Exception as e:
        logger.exception(f"Error loading CSV: {e}")
        return pd.DataFrame(columns=["id", "question", "answer"])

df = load_faq_df(CSV_PATH)

@app.get("/")
def home():
    return {"message": "Legal FAQ API is running"}

@app.get("/faqs")
def get_faqs(
    query: str | None = Query(None, description="Search keyword"),
    limit: int = Query(20, ge=1, le=500, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Returns a paginated list of FAQ records. If `query` is provided, returns
    matched records (case-insensitive) from question or answer fields.
    """
    if df.empty:
        return {"result": [], "total": 0}

    result_df = df

    if query:
        mask = (
            result_df["question"].astype(str).str.contains(query, case=False, na=False) |
            result_df["answer"].astype(str).str.contains(query, case=False, na=False)
        )
        result_df = result_df[mask]

    total = len(result_df)
    # simple pagination
    page = result_df.iloc[offset: offset + limit]
    records = page.to_dict(orient="records")
    return {"total": total, "offset": offset, "limit": limit, "results": records}

@app.get("/faqs/{faq_id}")
def get_faq_by_id(faq_id: int):
    """
    Get a single FAQ by numeric id (the CSV is assigned an `id` column if one doesn't exist).
    """
    if df.empty:
        raise HTTPException(status_code=404, detail="No FAQ data available")
    matched = df[df["id"] == faq_id]
    if matched.empty:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return matched.iloc[0].to_dict()
