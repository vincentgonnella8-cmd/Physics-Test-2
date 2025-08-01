import streamlit as st
import os
from openai import OpenAI
import svgwrite

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
        # System message instructing AI how to respond
        system_message = {
            "role": "system",
            "content": (
                "You are an expert AP Physics C tutor. When asked to generate a problem, "
                "respond using the exact format below:\n\n"
                "Question: <the physics question>\n"
                "Answer: <final numeric or conceptual answer>\n"
                "Explanation: <step-by-step detailed explanation>\n"
                "SVG_Code:\n```python\n"
                "import svgwrite\n\n"
                "def draw_diagram():\n"
                "    dwg = svgwrite.Drawing(size=(\"300px\", \"200px\"))\n"
                "    # Define a red arrow marker for force arrows\n"
                "    arrow = dwg.marker(id=\"arrow\", insert=(10,5), size=(10,10), orient=\"auto\")\n"
                "    arrow.add(dwg.path(d=\"M 0 0 L 10 5 L 0 10 z\", fill=\"red\"))\n"
                "    dwg.defs.add(arrow)\n\n"
                "    # Draw shapes, lines, text, and use marker_end='url(#arrow)' for arrows\n"
                "    # Example:\n"
                "    # dwg.add(dwg.line(start=(80, 100), end=(100, 100), stroke=\"red\", stroke_width=2, marker_end=\"url(#arrow)\"))\n\n"
                "    # Return SVG string\n"
                "    return dwg.tostring()\n"
                "```\n"
                "Do NOT include any extra text outside this format."
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

        # Process the response
        if "SVG_Code:" in full_response and "```python" in full_response:
            try:
                question = full_response.split("Question:")[1].split("Answer:")[0].strip()
                answer = full_response.split("Answer:")[1].split("Explanation:")[0].strip()
                explanation = full_response.split("Explanation:")[1].split("SVG_Code:")[0].strip()
                code_block = full_response.split("```python")[1].split("```")[0].strip()

                # Run the svgwrite code safely
                local_vars = {}
                exec(code_block, {"svgwrite": svgwrite}, local_vars)

                if 'draw_diagram' in local_vars:
                    svg_str = local_vars['draw_diagram']()

                    st.markdown(f"**Question:** {question}")
                    st.image(svg_str)
                    st.markdown(f"**Answer:** {answer}")
                    st.markdown(f"**Explanation:** {explanation}")

                    # Save cleaned assistant response in history (no code shown)
                    clean_msg = f"**Question:** {question}\n\n**Answer:** {answer}\n\n**Explanation:** {explanation}"
                    st.session_state['messages'].append({"role": "assistant", "content": clean_msg})
                else:
                    st.error("AI response did not include draw_diagram() function.")
            except Exception as e:
                st.error(f"Diagram rendering error: {e}")
        else:
            # If format unexpected, just show raw response
            st.markdown(full_response, unsafe_allow_html=True)
            st.session_state['messages'].append({"role": "assistant", "content": full_response})
