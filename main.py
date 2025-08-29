import os
import re
import json
import tempfile
import subprocess
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv

import pandas as pd
import numpy as np
import requests
from io import BytesIO, StringIO
from bs4 import BeautifulSoup

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

app = FastAPI(title="Python Data Analyst Agent")

LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 120))

# --- Tool: scrape URL into DataFrame ---
@tool
def scrape_url_to_dataframe(url: str) -> Dict[str, Any]:
    """
    Fetch a URL and return structured data as JSON (table or text).
    Supports CSV, Excel, Parquet, JSON, HTML tables, and fallback to raw text.
    """
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "").lower()

        df = None
        if "text/csv" in ctype or url.endswith(".csv"):
            df = pd.read_csv(BytesIO(resp.content))
        elif "spreadsheetml" in ctype or url.endswith((".xls", ".xlsx")):
            df = pd.read_excel(BytesIO(resp.content))
        elif url.endswith(".parquet"):
            df = pd.read_parquet(BytesIO(resp.content))
        elif "application/json" in ctype or url.endswith(".json"):
            try:
                data = resp.json()
                df = pd.json_normalize(data)
            except Exception:
                df = pd.DataFrame([{"text": resp.text}])
        elif "text/html" in ctype:
            try:
                tables = pd.read_html(StringIO(resp.text))
                df = tables[0] if tables else None
            except Exception:
                df = None
            if df is None:
                text = BeautifulSoup(resp.text, "html.parser").get_text(separator="\n", strip=True)
                df = pd.DataFrame({"text": [text]})
        else:
            df = pd.DataFrame({"text": [resp.text]})

        return {
            "status": "success",
            "columns": df.columns.astype(str).tolist(),
            "data": df.to_dict(orient="records"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "data": [], "columns": []}

# --- JSON cleaner ---
def clean_llm_output(output: str) -> Dict[str, Any]:
    try:
        s = output.strip()
        s = re.sub(r"^```(json)?", "", s).strip("` \n")
        return json.loads(s)
    except Exception as e:
        return {"error": f"Failed to parse JSON: {e}", "raw": output}

# --- Code execution helper ---
def run_user_code(code: str, injected_pickle: str = None, timeout: int = 60) -> Dict[str, Any]:
    preamble = [
        "import json, pandas as pd, numpy as np, matplotlib",
        "matplotlib.use('Agg')",
        "import matplotlib.pyplot as plt",
        "from io import BytesIO",
        "import base64",
    ]
    if injected_pickle:
        preamble.append(f"df = pd.read_pickle(r'''{injected_pickle}''')")
        preamble.append("data = df.to_dict(orient='records')")

    helper = r"""
def plot_to_base64():
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')
"""

    script = "\n".join(preamble) + "\n" + helper + "\nresults = {}\n" + code + \
             "\nprint(json.dumps({'status':'success','result':results}, default=str))"

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
    tmp.write(script)
    tmp.close()

    try:
        completed = subprocess.run(
            ["python3", tmp.name],
            capture_output=True, text=True, timeout=timeout
        )
        if completed.returncode != 0:
            return {"status": "error", "message": completed.stderr}
        return json.loads(completed.stdout)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        os.unlink(tmp.name)
        if injected_pickle and os.path.exists(injected_pickle):
            os.unlink(injected_pickle)

# --- LLM setup ---
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GOOGLE_MODEL", "gemini-2.5-pro"),
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Python data analyst agent. Always return valid JSON with 'questions' and 'code'."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm=llm, tools=[scrape_url_to_dataframe], prompt=prompt)

agent_executor = AgentExecutor(agent=agent, tools=[scrape_url_to_dataframe], verbose=True)

# --- API endpoints ---
@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("<h1>Python Agent is running</h1>")

@app.post("/api")
async def analyze(request: Request):
    try:
        data = await request.json()
        llm_input = data.get("input", "")
        if not llm_input:
            raise HTTPException(400, "Missing input")

        response = agent_executor.invoke({"input": llm_input})
        parsed = clean_llm_output(response.get("output", ""))
        if "code" not in parsed:
            raise HTTPException(500, f"Invalid LLM response: {parsed}")

        exec_result = run_user_code(parsed["code"])
        return JSONResponse(exec_result)
    except Exception as e:
        raise HTTPException(500, str(e))
