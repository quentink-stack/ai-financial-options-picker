import streamlit as st
import requests
import json
import pandas as pd
from etrade import get_options_chain
import etrade.client as etrade_client
import webbrowser
import os

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

# --- Sidebar Authentication Controls ---
with st.sidebar:
    with st.expander("🔑 E*TRADE Authentication"):
        # Check if we have a valid session for the sidebar controls
        sidebar_session, _ = etrade_client.load_saved_session("sandbox")
        if sidebar_session is not None:
            st.success("E*TRADE Status: Authenticated")
            # Provide a quick re-auth path in case tokens are expired
            if st.button("Force Re-auth", help="Start new authorization flow (useful if tokens are expired)"):
                try:
                    # remove saved tokens file
                    if hasattr(etrade_client, 'TOKENS_FILE'):
                        tf = etrade_client.TOKENS_FILE
                    else:
                        tf = os.path.join(os.path.dirname(__file__), "etrade", "tokens.json")
                    if os.path.exists(tf):
                        os.remove(tf)

                    # start a new auth flow immediately and store request token info
                    authorize_url, req_token, req_secret, base = etrade_client.start_auth("sandbox")
                    st.session_state.etrade_oauth = {
                        "request_token": req_token,
                        "request_token_secret": req_secret,
                        "authorize_url": authorize_url,
                        "base_url": base
                    }
                    try:
                        webbrowser.open(authorize_url)
                    except Exception:
                        pass

                    # force reload so UI shows the authorize URL and PIN input
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to start re-auth: {e}")
        else:
            st.info("E*TRADE Status: Not authenticated")

st.title("📈 AI Financial Assistant (E*TRADE + Local LLM)")

# Project Overview
st.markdown("""
<div style='background-color:#e8f4fa; padding:20px; border-radius:10px; margin-bottom:20px'>
    <h2 style='margin-top:0'>Welcome to the AI Financial Assistant!</h2>
    <p style='font-size:20px'>This tool helps you analyze financial options data using AI. Here's what you can do:</p>
    <ul style='font-size:20px; margin-left:25px; line-height:1.6'>
        <li>Get <b>live, real-time </b> market data from E*TRADE (quotes and options chains) after authenticating</li>
        <li>Upload your own options data in CSV format</li>
        <li>Chat with an AI assistant about the data</li>
        <li>Get AI-powered analysis and recommendations</li>
    </ul>
    <p style='font-size:20px'>
        The assistant uses a <a href="https://ollama.com/" target="_blank">local LLM (Ollama) for privacy and speed</a>↗️. Connect your E*TRADE account 
        to access live market data, or upload your own data to get started.
    </p>
</div>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Create three columns for the main layout
col1, col2, col3 = st.columns([1, 1, 1])

# --- E*TRADE Integration ---
with col1:
    st.subheader("E*TRADE Data")
    # Attempt to load saved session (tokens.json)
    session, base_url = etrade_client.load_saved_session("sandbox")

    if session is None:
        st.warning("E*TRADE not authenticated. Please authorize to enable market calls.")

        if "etrade_oauth" not in st.session_state:
            st.session_state.etrade_oauth = {}

        if st.button("Start E*TRADE Authorization"):
            authorize_url, req_token, req_secret, base = etrade_client.start_auth("sandbox")
            # store request token/secret for completion step
            st.session_state.etrade_oauth["request_token"] = req_token
            st.session_state.etrade_oauth["request_token_secret"] = req_secret
            st.session_state.etrade_oauth["authorize_url"] = authorize_url
            st.session_state.etrade_oauth["base_url"] = base
            # try to open in browser for convenience
            try:
                webbrowser.open(authorize_url)
            except Exception:
                pass

        if st.session_state.etrade_oauth.get("authorize_url"):
            st.markdown("**Authorize URL:**")
            st.markdown(f"[{st.session_state.etrade_oauth['authorize_url']}]({st.session_state.etrade_oauth['authorize_url']})")
            pin = st.text_input("Enter the PIN/verifier from E*TRADE:")
            if st.button("Complete E*TRADE Authorization"):
                if not pin:
                    st.error("Please paste the PIN/verifier provided by E*TRADE after authorizing.")
                else:
                    try:
                        session, base_url = etrade_client.complete_auth(
                            st.session_state.etrade_oauth.get("request_token"),
                            st.session_state.etrade_oauth.get("request_token_secret"),
                            pin,
                            "sandbox"
                        )
                        st.success("E*TRADE authorization complete — tokens saved.")
                        # clear temporary oauth info
                        st.session_state.etrade_oauth = {}
                        # reload saved session
                        session, base_url = etrade_client.load_saved_session("sandbox")
                    except Exception as e:
                        st.error(f"Failed to complete authorization: {e}")

        st.markdown("---")
        st.info("If you have already authorized and saved tokens, reload the app or use the 'Revoke / Re-auth' button below.")
        if st.button("Revoke / Re-auth (delete saved tokens)"):
            try:
                # Try to remove tokens file
                if hasattr(etrade_client, 'TOKENS_FILE'):
                    tf = etrade_client.TOKENS_FILE
                else:
                    # fallback path inside etrade package
                    tf = os.path.join(os.path.dirname(__file__), "etrade", "tokens.json")
                if os.path.exists(tf):
                    os.remove(tf)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to remove tokens file: {e}")

        # Don't proceed to market calls if no session
        session = None

    else:
        # Show auth success in a dismissible banner above the data section
        st.toast("E*TRADE: Successfully authenticated", icon="✅")

    # User selects ticker
    ticker = st.text_input("Enter ticker symbol:", "AAPL")

    if st.button("Get Quote"):
        if session is None:
            st.error("No authenticated E*TRADE session. Please authorize first.")
        else:
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
