from fastapi import FastAPI, Query
import pandas as pd

app = FastAPI()

# Load CSV into DataFrame
df = pd.read_csv("cleaned_legal_faq.csv")

@app.get("/")
def home():
    return {"message": "Legal FAQ API is running"}

@app.get("/faqs")
def get_faqs(query: str = Query(None, description="Search keyword")):
    if query:
        # Simple keyword search (case-insensitive)
        results = df[df['question'].str.contains(query, case=False, na=False) |
                     df['answer'].str.contains(query, case=False, na=False)]
        if results.empty:
            return {"result": "No matching FAQ found."}
        return results.to_dict(orient="records")
    else:
        return df.to_dict(orient="records")
