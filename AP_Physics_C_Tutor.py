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

# Tabs for Chat and Question Generator
tab1, tab2 = st.tabs(["📚 Tutor Chat", "🧪 Question Generator"])

# ========== TAB 1: TUTOR CHAT ==========
with tab1:
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

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
                    "solving as college board's AP classroom, and if a student asks to generate a "
                    "question, refer to the college board document to help you create one. Always "
                    "prioritize clarity, depth, and comprehensive coverage of all relevant concepts, "
                    "including math derivations, physical intuition, and problem-solving strategies. "
                    "Use LaTeX (enclosed in dollar signs, e.g., $E=mc^2$ or $$\\int F \\, dx$$) whenever appropriate."
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
            st.markdown(full_response, unsafe_allow_html=True)

            st.session_state['messages'].append({"role": "assistant", "content": full_response})

# ========== TAB 2: QUESTION GENERATOR ==========
with tab2:
    st.subheader("Generate a Custom AP Physics C Question")

    q_type = st.radio("Question Type", ["Open-Ended", "Multiple Choice"])
    topic = st.text_input("Topic (e.g., Newton's Second Law)")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

    if "question_part" not in st.session_state:
        st.session_state.question_part = None
    if "answer_part" not in st.session_state:
        st.session_state.answer_part = None
    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False

    if st.button("Generate Question"):
        st.session_state.show_answer = False  # Reset on new question

        # System message for focused question generation
        system_msg = {
            "role": "system",
            "content": (
                "You are an expert AP Physics C question generator. "
                "Always match College Board's AP style. Use clear physics language, proper math notation "
                "with LaTeX ($...$ or $$...$$), and pedagogically sound structure."
            )
        }

        # User prompt based on question type
        if q_type == "Open-Ended":
            user_prompt = (
                f"Generate an open-ended AP Physics C question on the topic of '{topic}' "
                f"with {difficulty.lower()} difficulty. Format it like an FRQ from the AP exam. "
                f"After the question, provide a complete, step-by-step solution with explanations "
                f"using LaTeX formatting where appropriate. Separate the question and solution clearly."
            )
        else:  # Multiple Choice
            user_prompt = (
                f"Generate a multiple choice AP Physics C question on the topic of '{topic}' "
                f"with {difficulty.lower()} difficulty. Include exactly 4 choices labeled (A)–(D), "
                f"with only one correct answer. After the question, clearly indicate the correct answer "
                f"(e.g., **Correct Answer: (C)**), then provide a full explanation. Separate the question "
                f"and answer using a divider like '---' or similar."
            )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                system_msg,
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        full_response = response.choices[0].message.content

        # Try splitting the response at a divider like "---" or "Answer:"
        if "---" in full_response:
            parts = full_response.split("---", 1)
        elif "Answer:" in full_response:
            parts = full_response.split("Answer:", 1)
        else:
            parts = [full_response, ""]

        st.session_state.question_part = parts[0].strip()
        st.session_state.answer_part = parts[1].strip() if len(parts) > 1 else ""
    
    # Show the generated question
    if st.session_state.question_part:
        st.markdown("### Question")
        st.markdown(st.session_state.question_part, unsafe_allow_html=True)

        # Reveal answer button
        if not st.session_state.show_answer and st.session_state.answer_part:
            if st.button("Reveal Answer"):
                st.session_state.show_answer = True

        # Show answer after button is clicked
        if st.session_state.show_answer and st.session_state.answer_part:
            st.markdown("### Answer / Explanation")
            st.markdown(st.session_state.answer_part, unsafe_allow_html=True)
