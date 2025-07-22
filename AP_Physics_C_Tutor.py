import streamlit as st
import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Try to find and load the .env file automatically
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
else:
    # .env not found, assume environment variables are set elsewhere (like deployment secrets)
    pass

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    st.error("API key not found! Please set OPENAI_API_KEY in your environment or .env file.")
    st.stop()

BASE_URL = "https://models.github.ai/inference"
MODEL_NAME = "gpt-4.1"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

st.title('AP Physics C Tutor')

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.sidebar.title('Model Parameters')
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens = st.sidebar.slider('Max Tokens', 1, 4096, 256)

for msg in st.session_state['messages']:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

if prompt := st.chat_input("What can I help you with?"):
    st.session_state['messages'].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state['messages'],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        full_response = st.write_stream(response_stream)
        st.session_state['messages'].append({"role": "assistant", "content": full_response})