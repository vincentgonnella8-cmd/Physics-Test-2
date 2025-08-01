import streamlit as st
import os
from openai import OpenAI
import svgwrite
from io import StringIO

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
max_tokens = st.sidebar.slider('Max Tokens', 1, 4096, 1024)

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
        # System message for AI behavior
        system_message = {
            "role": "system",
            "content": (
                "You are an expert AP Physics C tutor. When asked to generate a problem, follow this format:\n\n"
                "Question: <question>\nAnswer: <short answer>\nExplanation: <step-by-step explanation>\n"
                "SVG_Code:\n```python\n<svgwrite-based draw_diagram() function>\n```"
                "\nDo NOT explain the code. Just include it."
            )
        }

        messages = [system_message] + st.session_state['messages']

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        full_response = response.choices[0].message.content

        if "SVG_Code:" in full_response and "```python" in full_response:
            try:
                # Extract sections
                question = full_response.split("Question:")[1].split("Answer:")[0].strip()
                answer = full_response.split("Answer:")[1].split("Explanation:")[0].strip()
                explanation = full_response.split("Explanation:")[1].split("SVG_Code:")[0].strip()
                code_block = full_response.split("```python")[1].split("```")[0].strip()

                # Run the code block securely
                local_vars = {}
                exec(code_block, {"svgwrite": svgwrite}, local_vars)

                if 'draw_diagram' in local_vars:
                    svg_str = local_vars['draw_diagram']()

                    st.markdown(f"**Question:** {question}")
                    st.image(svg_str)
                    st.markdown(f"**Answer:** {answer}")
                    st.markdown(f"**Explanation:** {explanation}")

                    # Save response to session history
                    st.session_state['messages'].append({"role": "assistant", "content": f"**Question:** {question}\n\n**Answer:** {answer}\n\n**Explanation:** {explanation}"})
                else:
                    st.error("AI did not return a draw_diagram() function.")
            except Exception as e:
                st.error(f"Diagram rendering error: {e}")
        else:
            # Fallback: plain assistant reply
            st.markdown(full_response, unsafe_allow_html=True)
            st.session_state['messages'].append({"role": "assistant", "content": full_response})
