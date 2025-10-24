import streamlit as st
import requests
import json
import pandas as pd
from etrade import get_etrade_session, get_options_chain

# --- Config ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  # change if you want another model

# --- Function to query Ollama ---
def query_ollama(prompt):
    response = requests.post(
        OLLAMA_API_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
        stream=True
    )
    collected = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                chunk = data["response"]
                collected += chunk
                yield chunk
    return collected

# --- Streamlit UI ---
st.set_page_config(page_title="AI Financial Assistant", layout="wide")
st.title("📈 AI Financial Assistant (E*TRADE + Local LLM)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Create three columns for the main layout
col1, col2, col3 = st.columns([1, 1, 1])

# --- E*TRADE Integration ---
with col1:
    st.subheader("E*TRADE Data")
    
    # Connect to E*TRADE
    session, base_url = get_etrade_session("sandbox")

    # User selects ticker
    ticker = st.text_input("Enter ticker symbol:", "AAPL")

    if st.button("Get Quote"):
        url = f"{base_url}/v1/market/quote/{ticker}.json"
        r = session.get(url)
        if r.status_code == 200:
            data = r.json()
            st.json(data)
        else:
            st.error(f"Failed to fetch quote: {r.status_code} {r.text}")
            
with col2:
    st.subheader("Options Chain")
    expiry = st.text_input("Expiry date (YYYY-MM-DD):", "2025-09-19")
    if st.button("Get E*TRADE Option Chain"):
        url = f"{base_url}/v1/market/optionchains.json"
        params = {"symbol": ticker, "expiryDate": expiry}
        r = session.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            if "OptionChainResponse" in data and "OptionPair" in data["OptionChainResponse"]:
                options_data = data["OptionChainResponse"]["OptionPair"]
                # Convert to DataFrame for better display
                st.json(data)  # For now showing raw data, can be improved to show as table
            else:
                st.warning("No options data available")
        else:
            st.error(f"Failed to fetch option chain: {r.status_code} {r.text}")

with col3:
    st.subheader("Upload Custom Data")
    # --- File uploader ---
    uploaded_file = st.file_uploader("Upload Options Chain (CSV)", type=["csv"])
    options_chain = None

    if uploaded_file is not None:
        try:
            options_chain = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(options_chain.head(5))
        except Exception as e:
            st.error(f"Error reading file: {e}")

# Chat interface below the three columns
st.markdown("---")  # Add a visual separator
st.subheader("AI Chat Interface")
user_input = st.text_area("Your question about the data:", height=100)

if st.button("Send"):
    if user_input.strip():
        # If options chain is uploaded, summarize + add to prompt
        if options_chain is not None:
            summary = options_chain.head(30).to_string(index=False)
            prompt = f"User question: {user_input}\n\nHere is a preview of the uploaded options chain:\n{summary}\n\nAnalyze this chain and answer the user's question."
        else:
            prompt = user_input

        st.session_state.chat_history.append(("You", user_input))
        st.write("**AI:** ")
        placeholder = st.empty()
        ai_reply = ""
        for chunk in query_ollama(prompt):
            ai_reply += chunk
            placeholder.markdown(ai_reply)
        st.session_state.chat_history.append(("AI", ai_reply))

if st.session_state.chat_history:
    st.subheader("Chat History")
    for role, text in st.session_state.chat_history:
        st.markdown(f"**{role}:** {text}")
