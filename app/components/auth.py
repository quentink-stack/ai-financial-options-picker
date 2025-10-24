"""Authentication UI components for E*TRADE integration.

This module provides Streamlit UI components for handling E*TRADE authentication flows.
"""
import streamlit as st
import os
import webbrowser
import etrade.client as etrade_client

def render_auth_sidebar():
    """Render the E*TRADE authentication sidebar expander."""
    with st.expander("🔑 E*TRADE Authentication"):
        # Check if we have a valid session for the sidebar controls
        sidebar_session, _ = etrade_client.load_saved_session("sandbox")
        if sidebar_session is not None:
            st.success("E*TRADE Status: Authenticated")
            if st.button("Force Re-auth", help="Start new authorization flow (useful if tokens are expired)"):
                try:
                    # remove saved tokens file
                    if hasattr(etrade_client, 'TOKENS_FILE'):
                        tf = etrade_client.TOKENS_FILE
                    else:
                        tf = os.path.join(os.path.dirname(__file__), "..", "etrade", "tokens.json")
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

def render_auth_flow():
    """Render the main E*TRADE authentication flow UI.
    
    Returns:
        tuple: (session, base_url) if authenticated, (None, None) if not
    """
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
                    tf = os.path.join(os.path.dirname(__file__), "..", "etrade", "tokens.json")
                if os.path.exists(tf):
                    os.remove(tf)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to remove tokens file: {e}")

        # Don't proceed to market calls if no session
        return None, None
    else:
        st.toast("E*TRADE: Successfully authenticated", icon="✅")
        return session, base_url