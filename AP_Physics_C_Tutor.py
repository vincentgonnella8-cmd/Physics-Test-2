import streamlit as st
import os
from openai import OpenAI
import svgwrite
import re

API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets or environment variables.")
    st.stop()

BASE_URL = "https://models.github.ai/inference"
MODEL_NAME = "gpt-4.1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

st.title("AP Physics C Tutor — Explanation & Diagram Generator")

st.sidebar.title("Model Parameters")
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 100, 2048, 1024)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 100, 1024, 512)

def generate_physics_explanation(user_prompt):
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert AP Physics C tutor. Given the user's prompt, generate a physics question, "
            "the final answer, and a detailed, step-by-step explanation with rigorous LaTeX formatting. "
            "Start your response with a brief explanation on how to use LaTeX math formatting in the text, "
            "specifically: inline math should be enclosed in $...$ and display math in $$...$$. "
            "ALWAYS use LaTeX for any math expressions or formulas. "
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
            "Generate ONLY a complete function named draw_diagram() that returns the SVG string. "
            "Include a white background rectangle that fills the entire SVG canvas. "
            "Define a red arrow marker with id 'arrow' in defs and use marker_end='url(#arrow)' properly. "
            "At the start of your function code, add a brief Python comment explaining how svgwrite is used, "
            "how the background rectangle is added, and how arrows with marker_end work. "
            "Ensure the Python code you output is syntactically correct, complete, and runnable. "
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
    # Fix common marker_end misuse
    code_block_fixed = code_block.replace(
        'marker_end=arrow', 'marker_end="url(#arrow)"'
    ).replace(
        "marker_end=arrow", 'marker_end="url(#arrow)"'
    )
    # Optional: fix other common issues here if you want

    # Compile check before exec
    try:
        compile(code_block_fixed, "<string>", "exec")
    except SyntaxError as e:
        st.error(f"Syntax error detected in SVG code: {e}")
        return None

    local_vars = {}
    try:
        exec(code_block_fixed, {"svgwrite": svgwrite}, local_vars)
    except Exception as e:
        st.error(f"Error executing SVG code: {e}")
        return None
    
    if 'draw_diagram' in local_vars:
        return local_vars['draw_diagram']()
    else:
        st.error("No draw_diagram() function found in SVG code.")
        return None

st.write("### Enter a physics topic or question prompt")

user_input = st.text_area("Physics question prompt", height=120)

if st.button("Generate Explanation and Diagram"):
    if not user_input.strip():
        st.warning("Please enter a prompt!")
    else:
        with st.spinner("Generating physics explanation..."):
            explanation_response = generate_physics_explanation(user_input)
        
        st.markdown("### Generated Question, Answer, and Explanation")
        st.markdown(explanation_response, unsafe_allow_html=True)
        
        # Try to extract a suitable diagram prompt from the explanation:
        question_match = re.search(r"Question:(.*)", explanation_response, re.IGNORECASE)
        diagram_prompt = question_match.group(1).strip() if question_match else user_input

        with st.spinner("Generating SVG diagram code..."):
            svg_code_response = generate_svg_code(diagram_prompt)

        if "def draw_diagram" in svg_code_response:
            try:
                code_start = svg_code_response.index("def draw_diagram")
                code_block = svg_code_response[code_start:].strip()

                svg_str = execute_svg_code(code_block)
                if svg_str:
                    st.image(svg_str)
                    st.success("SVG Diagram rendered successfully!")
                else:
                    st.warning("SVG diagram could not be rendered due to errors.")
            except Exception as e:
                st.error(f"Error rendering SVG diagram: {e}")
        else:
            st.error("SVG code not found in the AI response.")
