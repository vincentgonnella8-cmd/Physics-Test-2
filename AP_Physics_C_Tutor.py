import streamlit as st
import os
from openai import OpenAI

# Get API key from Streamlit secrets or environment variable fallback
API_KEY = st.secrets.get("OPENAI_API_KEY")

if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets or environment variables.")
    st.stop()

BASE_URL = "https://models.github.ai/inference"
MODEL_NAME = "gpt-4.1"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

st.title('AP Physics C Tutor')

# Initialize message history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Sidebar sliders
st.sidebar.title('Model Parameters')
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens = st.sidebar.slider('Max Tokens', 1, 4096, 256)

# Display chat history
for msg in st.session_state['messages']:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'], unsafe_allow_html=True)  # Allow LaTeX rendering

# Chat input
if prompt := st.chat_input("What can I help you with?"):
    st.session_state['messages'].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Add system message to instruct AI on behavior
        system_message = {
            "role": "system",
            "content": (
                "You are an expert AP Physics C tutor. Your goal is to provide thorough and "
                "detailed explanations for every question. ALWAYS try to use similar problem "
                " solving as college board's AP classroom, and if a student asks to generate a "
                " question, refer to the college board document to help you create one Always "
                " prioritize clarity, depth, and "
                "comprehensive coverage of all relevant concepts, including math derivations, "
                "physical intuition, and problem-solving strategies. Use LaTeX (enclosed in dollar signs, "
                "e.g., $E=mc^2$ or $$\\int F \\, dx$$) whenever appropriate to clearly display equations."
            )
        }

        # Include the system message at the start of the conversation
        messages = [system_message] + st.session_state['messages']

        # Stream the response from the model
        response_stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        full_response = st.write_stream(response_stream)

        # Render LaTeX in the assistant's message
        st.markdown(full_response, unsafe_allow_html=True)

        st.session_state['messages'].append({"role": "assistant", "content": full_response})
