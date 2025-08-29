
# 🌐 LLM Agent [TDS LLM](https://tds-bonus-project-llm-agent.vercel.app/) — Browser-Based Multi-Tool Reasoning

This project is a **proof-of-concept (POC)** for building a **browser-based LLM agent** that can combine **natural language reasoning** with **external tools** like search engines, pipelined APIs, and even **live JavaScript execution**.  

Modern LLM agents aren’t limited to text — they dynamically integrate multiple tools and loop until tasks are solved. This app demonstrates that idea with a **minimal, hackable UI + JavaScript agent core**.


---

  


---

## 📋 Project Overview

### Goal
Build a minimal JavaScript-based agent that can:
1. Accept user input in the browser.
2. Query an LLM for reasoning.
3. Dynamically trigger **tool calls** (search, AI workflows, code execution).
4. Loop until the LLM decides no more tools are needed.

### Agent Logic (Conceptual)
```python
def loop(llm):
    msg = [user_input()]
    while True:
        output, tool_calls = llm(msg, tools)
        print("Agent: ", output)
        if tool_calls:
            msg += [handle_tool_call(tc) for tc in tool_calls]
        else:
            msg.append(user_input())
````

### JavaScript Implementation

This POC reimplements the above loop in **browser JavaScript**, connected to provider APIs.

---

## 🛠️ Getting Started

### Prerequisites

* A modern browser (Chrome/Edge/Firefox).
* API keys for:

  * [AI Pipe](https://aipipe.org/) proxy API (recommended)
  * Optional: OpenAI, Gemini, or other providers.

✨ Features

Chat with OpenAI models (default: gpt-4o-mini).

Clean UI with chat bubbles + typing indicator.

Supports user, assistant, and system messages.

Public deployment: no need for each user to bring their own API key.

Backend proxy with Vercel Serverless Function (/api/chat.js) keeps your API key safe.

📂 Project Structure
├── index.html       # Main frontend (UI)
├── agent.js         # Frontend logic
├── api/
│   └── chat.js      # Serverless backend for OpenAI
└── README.md        # This file

⚡ Quick Start (Local Preview)

You can preview the frontend by just opening index.html in your browser.
👉 API calls won’t work locally without a backend — for that, deploy on Vercel.

🌐 Deployment on Vercel
1. Clone this repo
git clone https://github.com/YOUR-USERNAME/LLM-Agent-bonus-tds.git
cd LLM-Agent-bonus-tds

2. Push to your own GitHub

If you forked it, skip this. Otherwise:

git remote remove origin
git remote add origin https://github.com/YOUR-USERNAME/LLM-Agent-bonus-tds.git
git push -u origin main

3. Set up Vercel

Go to Vercel
 and sign in with GitHub.

Click New Project → import your repo.

Settings:

Framework Preset → Other

Build Command → (leave empty)

Output Directory → .

4. Add Environment Variable

In Vercel Dashboard → Project → Settings → Environment Variables

Add:

OPENAI_API_KEY = sk-xxxxxxx

5. Deploy 🎉

Click Deploy.

Vercel will give you a live URL like:

https://llm-agent-bonus-tds.vercel.app/

🖥 Usage

Visit your deployed app.

Type your message in the input box and hit Send.

The assistant will reply using OpenAI models via the serverless backend.

🔒 Security

Your OpenAI API key is never exposed to users.

The frontend talks only to /api/chat.

The backend calls OpenAI with your key (stored in Vercel environment variables).
* Add **conversation persistence** with IndexedDB/localStorage.
* Enable **streaming token-by-token responses**.
* Expand tools: file parsing, charting, SQL, etc.

---
