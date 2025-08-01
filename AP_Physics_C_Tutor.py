import streamlit as st
import re
from openai import OpenAI
import svgwrite
import streamlit.components.v1 as components

# --- Load API key from Streamlit secrets ---
API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets.")
    st.stop()

# Set your GitHub-hosted inference URL here
BASE_URL = "https://models.github.ai/inference"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
MODEL_NAME = "gpt-4o-mini"

# Sidebar controls
st.sidebar.title("Model Parameters")
temp_question = st.sidebar.slider("Question Temperature", 0.0, 1.0, 0.7, 0.1)
max_tokens_question = st.sidebar.slider("Question Max Tokens", 200, 1200, 700, 10)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 200, 1024, 600, 10)
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.8, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 500, 2048, 1400, 10)

st.title("AP Physics C Tutor — Question, Diagram & Explanation Generator")

topic = st.text_input("Enter the Physics Topic (e.g. Rotational Motion, Energy Conservation):", "Rotational Motion")

def generate_question_and_diagram_desc(topic: str) -> tuple[str | None, str | None]:
    prompt = f'''
You are an AP Physics C expert.
Always express math using LaTeX syntax: inline math with \\( ... \\),
block math with $$ ... $$ for standalone equations. 
Avoid plaintext math (e.g., never 'F = ma', always use \\( F = ma \\)). 
Describe diagrams in strict SVG structure, no physics in diagram descriptions.

1. Generate ONE original multiple-choice physics question on the topic "{topic}".
   Use clear LaTeX formatting for all formulas.
   Provide the question and answer choices only.

2. Next, create a detailed, precise diagram description intended for generating an SVG image.

   The SVG canvas size is fixed at 800 pixels wide by 600 pixels high.
   All coordinates must fit within this 800x600 pixel canvas.

   Use the following SVG drawing conventions when writing the diagram description:
   - Circles are drawn by specifying the center coordinate (x, y) and the radius.
   - Lines are drawn between two points specified by their start and end coordinates.
   - Arrows are lines with a direction indicated by start and end points.
   - Labels are placed at exact (x, y) coordinates.
   - All shapes should be outlines only.
   - Assume a white background canvas of 800x600 pixels is already provided.
   - Avoid using language from the question text.
   - List each diagram element as a bullet point with coordinates and sizes.

Format:
Question:
[question]

Answer Choices:
A) ...
B) ...
C) ...
D) ...

Correct Answer: [Letter]

Diagram description:
- Draw ...
- Draw ...
'''
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AP Physics C tutor. LaTeX formatting is used to write mathematical expressions clearly. "
                "Describe diagrams in strict SVG structure, no physics in diagram descriptions."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_question,
            max_tokens=max_tokens_question + 400,
        )
        full_text = response.choices[0].message.content.strip()
        parts = full_text.split("Diagram description:")
        question_text = parts[0].strip()
        diagram_desc = parts[1].strip() if len(parts) > 1 else ""
        return question_text, diagram_desc
    except Exception as e:
        st.error(f"OpenAI API call failed: {e}")
        return None, None

def generate_svg_code(diagram_desc: str) -> str | None:
    tutorial = '''
You are a Python SVG expert using the svgwrite library.
Always express math using LaTeX syntax.
Generate SVG diagrams based exactly on the provided detailed diagram description with pixel coordinates.

Instructions:
1. Use a canvas size of 800x600 pixels.
2. Start with a white background rectangle covering the entire canvas.
3. For each bullet point in the diagram description:
   - Parse coordinates and shapes precisely.
   - Draw lines, circles, rectangles, and arrows.
   - Use a red arrow marker with id 'arrow' for arrows.
   - Label text exactly at the given coordinates.
4. Do NOT change coordinates.
5. Use clear Python code with comments.
6. Return the SVG XML string with `return dw.tostring()`.
7. Output ONLY the Python function `draw_diagram()`.
'''
    prompt = f"{tutorial}\nDiagram description:\n\"\"\"{diagram_desc}\"\"\""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert at writing SVG drawing code in Python using svgwrite."
            )
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_svg,
            max_tokens=max_tokens_svg,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API call failed: {e}")
        return None

def generate_explanation(question_text: str) -> str | None:
    prompt = f'''
You are an excellent AP Physics C tutor.
Always express math using LaTeX syntax.
Given this question, write a detailed explanation using LaTeX formatting.

Question:
"""{question_text}"""
'''
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AP Physics C tutor. Use LaTeX formatting."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_explanation,
            max_tokens=max_tokens_explanation,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API call failed: {e}")
        return None

def execute_svg_code(code: str) -> str | None:
    # Clean code block markers if present
    code = re.sub(r"^```(python)?|```$", "", code.strip(), flags=re.MULTILINE)
    # Fix marker_end argument to proper svgwrite syntax if needed
    code = code.replace("marker_end=arrow", 'marker_end="url(#arrow)"')
    local_vars = {}
    try:
        exec(code, {"svgwrite": svgwrite}, local_vars)
        if "draw_diagram" not in local_vars:
            raise ValueError("draw_diagram() function not found in SVG code.")
        svg_str = local_vars["draw_diagram"]()
        return svg_str
    except Exception as e:
        st.error(f"SVG execution error: {e}")
        return None

def render_latex_markdown(text: str):
    # Streamlit markdown with LaTeX support (works best for block math)
    # Replace $$ ... $$ with st.latex for block equations if desired (optional)
    # For now, just display with markdown allowing HTML and mathjax rendering
    st.markdown(text, unsafe_allow_html=True)

# Main UI button and flow
if st.button("Generate Question, Diagram & Explanation"):
    if not topic.strip():
        st.warning("Please enter a physics topic!")
        st.stop()

    with st.spinner("Generating question and diagram description..."):
        raw_question, diagram_description = generate_question_and_diagram_desc(topic)

    if not raw_question or not diagram_description:
        st.error("Failed to generate question or diagram description.")
        st.stop()

    st.markdown("### Generated Question")
    render_latex_markdown(raw_question)

    st.markdown("### Diagram Description (raw)")
    st.text(diagram_description)

    with st.spinner("Generating SVG drawing code..."):
        svg_code = generate_svg_code(diagram_description)

    if not svg_code:
        st.warning("SVG generation failed.")
        st.stop()

    st.subheader("Generated SVG Python Code")
    st.code(svg_code, language="python")

    svg_str = execute_svg_code(svg_code)

    if svg_str:
        st.subheader("Rendered Diagram")
        scale_factor = 0.8
        scaled_width = int(800 * scale_factor)
        scaled_height = int(600 * scale_factor)

        components.html(
            f"""
            <div style="
                width: {scaled_width}px;
                height: {scaled_height}px;
                overflow: hidden;
                border: 1px solid #ccc;
                transform: scale({scale_factor});
