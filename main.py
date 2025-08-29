import os
import re
import pandas as pd
import requests
from io import BytesIO, StringIO
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# -----------------------------
# Scraper tool
# -----------------------------
def scrape_url_to_dataframe(url: str):
    """
    Fetch a URL and return data as a DataFrame (supports HTML tables, CSV, Excel, Parquet, JSON, and plain text).
    Always returns {"status": "success", "data": [...], "columns": [...]} if fetch works.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.google.com/",
        }

        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "").lower()
        df = None

        # --- CSV ---
        if "text/csv" in ctype or url.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(resp.content))

        # --- Excel ---
        elif any(url.lower().endswith(ext) for ext in (".xls", ".xlsx")) or "spreadsheetml" in ctype:
            df = pd.read_excel(BytesIO(resp.content))

        # --- Parquet ---
        elif url.lower().endswith(".parquet"):
            df = pd.read_parquet(BytesIO(resp.content))

        # --- JSON ---
        elif "application/json" in ctype or url.lower().endswith(".json"):
            try:
                data = resp.json()
                df = pd.json_normalize(data)
            except Exception:
                df = pd.DataFrame([{"text": resp.text}])

        # --- HTML / Fallback ---
        elif "text/html" in ctype:
            html_content = resp.text
            try:
                tables = pd.read_html(StringIO(html_content), flavor="bs4")
                if tables:
                    df = tables[0]
            except ValueError:
                pass
            if df is None:
                soup = BeautifulSoup(html_content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                df = pd.DataFrame({"text": [text]})

        # --- Unknown type fallback ---
        else:
            df = pd.DataFrame({"text": [resp.text]})

        df.columns = df.columns.map(str).str.replace(r"\[.*\]", "", regex=True).str.strip()

        return {"status": "success", "data": df.to_dict(orient="records"), "columns": df.columns.tolist()}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# -----------------------------
# OpenAI LLM setup
# -----------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",   # you can change to gpt-4o or gpt-3.5-turbo
    api_key=OPENAI_API_KEY,
    temperature=0
)

tools = [
    Tool(
        name="ScrapeURL",
        func=scrape_url_to_dataframe,
        description="Fetch a URL and return structured tabular/text data"
    )
]

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

if __name__ == "__main__":
    q = "Fetch this CSV https://people.sc.fsu.edu/~jburkardt/data/csv/airtravel.csv and tell me total passengers in 1958."
    result = agent_executor.run(q)
    print(result)
