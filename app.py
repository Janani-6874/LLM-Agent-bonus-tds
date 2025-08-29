import streamlit as st
from main import agent_executor   # ✅ because it lives in main.py

st.title("AI Data Analyst")

user_input = st.text_area("Ask me a question:")

if st.button("Run"):
    if user_input:
        with st.spinner("Thinking..."):
            response = agent_executor.invoke({"input": user_input})
        st.json(response)
