"""Chat and LLM integration UI components.

This module provides Streamlit UI components for interacting with the LLM and displaying chat history.
"""
import streamlit as st
import webbrowser

def render_chat_area():
    """Render the chat UI section."""
    st.markdown("## 💬 Chat")
    
    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Status warning about Ollama server
    st.markdown(
        """
        > **Note**: This requires [Ollama](https://ollama.ai) running locally with the 
        [Mixtral model](https://ollama.ai/library/mixtral)
        installed. [Click here](https://ollama.ai) to download.
        """,
        unsafe_allow_html=True
    )

    # Input box
    if prompt := st.chat_input("Ask me about stock options strategy..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Echo the user's message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Add assistant's response
        with st.chat_message("assistant"):
            response = (
                "Sorry, the LLM integration is not enabled or functioning correctly. "
                "Please make sure Ollama is running with the Mixtral model installed."
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)