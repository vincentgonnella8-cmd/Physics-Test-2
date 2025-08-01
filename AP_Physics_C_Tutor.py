import streamlit as st
import os
from openai import OpenAI
import svgwrite

API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets or environment variables.")
    st.stop()

BASE_URL = "https://models.github.ai/inference"
MODEL_NAME = "gpt-4.1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

st.title("AP Physics C Tutor — Two-Step Q&A and Diagram Generator")

st.sidebar.title("Model Parameters")
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 100, 2048, 1024)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 100, 1024, 512)

if 'history' not in st.session_state:
    st.session_state['history'] = []

def generate_physics_explanation(user_prompt):
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert AP Physics C tutor. Given the user's prompt, generate a physics question, the final answer, "
            "and a detailed, step-by-step explanation with rigorous LaTeX formatting. "
            "Include a brief explanation at the start about how to use LaTeX formatting for math in the explanation, "
            "such as enclosing inline math in $...$ and display math in $$...$$. "
            "Do NOT include any SVG code or diagram instructions."
        )
    }
    user_msg = {"role": "user", "content": user_prompt}
    messages = [system_msg, user_msg]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_explanation,
        max_tokens=max_tokens_explanation
    )
    return response.choices[0].message.content

def generate_svg_code(diagram_desc):
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert at generating physics diagrams in Python using svgwrite. "
            "Generate ONLY the function draw_diagram() that returns an SVG string. "
            "Include a white background rectangle filling the canvas and define a red arrow marker with id 'arrow'. "
            "Use marker_end='url(#arrow)' to draw arrows. "
            "At the start of your code, briefly explain (in Python comments) how to use svgwrite to create the diagram, "
            "how to add the background and arrows, and how to use marker_end properly. "
            "Do NOT include any explanation or text outside the code block."
        )
    }
    user_msg = {"role": "user", "content": diagram_desc}
    messages = [system_msg, user_msg]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_svg,
        max_tokens=max_tokens_svg
    )
    return response.choices[0].message.content

def execute_svg_code(code_block):
    code_block_fixed = code_block.replace(
        'marker_end=arrow', 'marker_end="url(#arrow)"'
    ).replace(
        "marker_end=arrow", 'marker_end="url(#arrow)"'
    )
    local_vars = {}
    exec(code_block_fixed, {"svgwrite": svgwrite}, local_vars)
    if 'draw_diagram' in local_vars:
        return local_vars['draw_diagram']()
    else:
        raise RuntimeError("No draw_diagram() function found in SVG code.")

st.write("### Step 1: Enter your physics question or topic")

user_input = st.text_area("Physics question prompt", height=100)

if st.button("Generate Question & Explanation"):
    if not user_input.strip():
        st.warning("Please enter a prompt!")
    else:
        with st.spinner("Generating physics question, answer, and explanation..."):
            explanation_response = generate_physics_explanation(user_input)
            st.session_state['history'].append({"role": "assistant_explanation", "content": explanation_response})
            st.success("Explanation generated!")

if any(h['role'] == "assistant_explanation" for h in st.session_state['history']):
    latest_exp = [h for h in st.session_state['history'] if h['role'] == "assistant_explanation"][-1]['content']

    st.markdown("### Generated Question & Explanation")
    st.markdown(latest_exp, unsafe_allow_html=True)

    st.write("---")
    st.write("### Step 2: Enter a description of the diagram to generate")

    diagram_desc = st.text_area(
        "Diagram description (e.g. 'Draw a block of mass m on a frictionless surface with a force arrow pointing right')",
        height=100
    )

    if st.button("Generate Diagram SVG"):
        if not diagram_desc.strip():
            st.warning("Please enter a diagram description!")
        else:
            with st.spinner("Generating SVG code..."):
                svg_code_response = generate_svg_code(diagram_desc)

            if "def draw_diagram" in svg_code_response:
                try:
                    code_start = svg_code_response.index("def draw_diagram")
                    code_block = svg_code_response[code_start:].strip()

                    svg_str = execute_svg_code(code_block)
                    st.image(svg_str)
                    st.success("SVG Diagram rendered successfully!")
                except Exception as e:
                    st.error(f"Error rendering SVG diagram: {e}")
                    st.text(svg_code_response)
            else:
                st.error("SVG code not found in the AI response.")
                st.text(svg_code_response)
