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

# Sidebar sliders
st.sidebar.title('Model Parameters')
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens = st.sidebar.slider('Max Tokens', 1, 4096, 256)

# Tabs: Chat and Question Generator
tab1, tab2 = st.tabs(["📚 Tutor Chat", "🧪 Question Generator"])

# ========== TAB 1: TUTOR CHAT ==========
with tab1:
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    # Display chat history
    for msg in st.session_state['messages']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'], unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("What can I help you with?"):
        st.session_state['messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system_message = {
                "role": "system",
                "content": (
                    "You are an expert AP Physics C tutor. Your goal is to provide thorough and "
                    "detailed explanations for every question. ALWAYS try to use similar problem "
                    " solving as college board's AP classroom, and if a student asks to generate a "
                    " question, refer to the college board document to help you create one. Always "
                    " prioritize clarity, depth, and comprehensive coverage of all relevant concepts, "
                    " including math derivations, physical intuition, and problem-solving strategies. "
                    " Use LaTeX (enclosed in dollar signs, e.g., $E=mc^2$ or $$\\int F \\, dx$$) whenever appropriate."
                )
            }

            messages = [system_message] + st.session_state['messages']

            response_stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            full_response = st.write_stream(response_stream)
            st.markdown(full_response, unsafe_allow_html=True)

            st.session_state['messages'].append({"role": "assistant", "content": full_response})

# ========== TAB 2: QUESTION GENERATOR ==========
with tab2:
    st.subheader("Generate a Custom AP Physics C Question")

    q_type = st.radio("Question Type", ["Open-Ended", "Multiple Choice"])
    topic = st.text_input("Topic (e.g., Newton's Second Law)")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    num_choices = 4 if q_type == "Multiple Choice" else None

    if st.button("Generate Question"):
        system_prompt = (
            "Generate an AP Physics C question based on College Board's style. "
            f"Make it a {q_type.lower()} question on the topic of {topic}, with {difficulty.lower()} difficulty. "
        )
        if q_type == "Multiple Choice":
            system_prompt += "Include exactly 4 answer choices labeled (A)–(D), with only one correct answer."

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        generated = response.choices[0].message.content
        st.markdown(generated, unsafe_allow_html=True)
