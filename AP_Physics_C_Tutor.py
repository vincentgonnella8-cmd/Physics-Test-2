import streamlit as st
import os
from openai import OpenAI
import svgwrite

# --- Config ---
API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets or environment variables.")
    st.stop()

BASE_URL = "https://models.github.ai/inference"
MODEL_NAME = "gpt-4.1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# --- Sidebar ---
st.sidebar.title("Model Parameters")
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 1000, 2048, 1500)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 100, 1024, 512)

st.title("AP Physics C Tutor — Question, Explanation & Diagram Generator")

topic = st.text_input(
    "Enter the Physics Topic (e.g. Rotational Motion, Energy Conservation):",
    "Rotational Motion"
)

def clean_code(code):
    lines = code.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)

def generate_question_and_explanation(topic):
    prompt = f"""
You are an AP Physics C: Mechanics expert teacher preparing students for the 2025 exam.

Using the style and tone of the 2012 official AP Physics C: Mechanics practice exam, generate original, up-to-date questions that could appear on a modern AP exam.

Task:

1. Generate a **new multiple-choice question** (MCQ) on {topic}, with 4 answer choices, indicate the correct answer, and provide a brief explanation.

2. Generate a **new free-response question** (FRQ) on {topic}, multi-part (a, b, c), with step-by-step solutions and labeled answers following AP scoring guidelines.

Label each question with:
- **Topic**  
- **Question Type**  
- **Difficulty Level**  
- **Answer Format**

Use rigorous LaTeX formatting naturally in your explanations.  
For example, write kinetic energy as $K = \\frac{{1}}{{2}}mv^2$, and display integrals as  
$$ W = \\int \\vec{{F}} \\cdot d\\vec{{s}} $$
"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Generate AP Physics C questions on topic: {topic}"}
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_explanation,
        max_tokens=max_tokens_explanation
    )
    return response.choices[0].message.content

def generate_svg_code(question_text):
    prompt = f'''
You are a physics diagram expert who writes clean Python code using the svgwrite library.

Based on the following AP Physics C free-response question, generate a Python function named draw_diagram() that creates an SVG diagram illustrating the problem setup or key concepts.

Requirements:
- Output ONLY the function definition for draw_diagram().
- DO NOT include any markdown (no ```python or backticks).
- The function must:
  - Create an SVG canvas 400x300 pixels
  - Add a white background rectangle
  - Define and use a red arrow marker with id 'arrow'
  - Use that marker on at least one line
  - Return the SVG XML string via dw.tostring()
  - Include clear comments

Here is the question to base the diagram on:
"""{question_text}"""
'''
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Return only the clean draw_diagram() function code."}
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_svg,
        max_tokens=max_tokens_svg
    )
    return response.choices[0].message.content

def execute_svg_code(code_block):
    code_block = clean_code(code_block)

    # Ensure arrow markers are correctly formatted
    code_block_fixed = code_block.replace(
        'marker_end=arrow', 'marker_end="url(#arrow)"'
    )

    # --- Diagnostic preview ---
    st.subheader("Generated SVG Code (Python)")
    st.code(code_block_fixed, language="python")

    # Validate code first
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
        try:
            svg_str = local_vars['draw_diagram']()
            return svg_str
        except Exception as e:
            st.error(f"Error running draw_diagram(): {e}")
            return None
    else:
        st.error("No draw_diagram() function found in the SVG code.")
        return None

if st.button("Generate AP Physics C Question, Explanation & Diagram"):
    if not topic.strip():
        st.warning("Please enter a physics topic!")
    else:
        with st.spinner("Generating question and explanation..."):
            full_explanation = generate_question_and_explanation(topic)

        st.markdown("### Generated AP Physics C Question & Explanation")
        st.markdown(full_explanation, unsafe_allow_html=True)

        # Extract free-response question section for the diagram
        frq_start = full_explanation.lower().find("free-response question")
        frq_text = full_explanation[frq_start:] if frq_start != -1 else full_explanation

        with st.spinner("Generating SVG diagram..."):
            svg_code = generate_svg_code(frq_text)

        svg_str = execute_svg_code(svg_code)
        if svg_str:
            st.image(svg_str)
            st.success("SVG Diagram rendered successfully!")
        else:
            st.warning("SVG diagram could not be rendered due to errors.")
