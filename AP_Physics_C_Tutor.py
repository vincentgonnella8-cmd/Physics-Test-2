import streamlit as st
import re
from openai import OpenAI
import svgwrite  # Moved import here since it's used below

# --- Load API key from Streamlit secrets ---
API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets.")
    st.stop()

# Set your GitHub-hosted inference URL here
BASE_URL = "https://models.github.ai/inference"

# Initialize OpenAI client with custom base_url
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

MODEL_NAME = "gpt-4o-mini"

# Sidebar controls for tuning generation
st.sidebar.title("Model Parameters")
temp_question = st.sidebar.slider("Question Temperature", 0.0, 1.0, 0.7, 0.1)
max_tokens_question = st.sidebar.slider("Question Max Tokens", 200, 1200, 700, 10)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 200, 1024, 600)
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.8, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 500, 2048, 1400, 10)

st.title("AP Physics C Tutor — Question, Diagram & Explanation Generator")

topic = st.text_input(
    "Enter the Physics Topic (e.g. Rotational Motion, Energy Conservation):",
    "Rotational Motion"
)


def clean_code_block(code: str) -> str:
    """Remove markdown fences if any."""
    code = code.strip()
    if code.startswith("```"):
        code = "\n".join(code.splitlines()[1:])
    if code.endswith("```"):
        code = "\n".join(code.splitlines()[:-1])
    return code.strip()


def generate_question_and_diagram_desc(topic: str) -> tuple[str | None, str | None]:
    prompt = f'''
You are an AP Physics C expert.

1. Generate ONE original multiple-choice physics question on the topic "{topic}".
   Use clear LaTeX formatting for all formulas.
   Provide the question and answer choices only.

2. Next, create a detailed, precise diagram description intended for generating an SVG image.
   The description must:
   - Use only exact pixel coordinates (x, y) for all diagram elements.
   - Specify shapes (lines, circles, arrows, labels) with size and orientation.
   - Use explicit instructions suitable for SVG rendering (e.g., "Draw a line from (x1,y1) to (x2,y2)").
   - Avoid using or referencing any language or phrases from the question text.
   - List each diagram element as a bullet point.
   - Example bullet points:
     * Draw a ramp line from (50, 250) to (350, 150).
     * Draw a solid circle centered at (150, 200) with radius 40 pixels.
     * Draw an arrow from (150, 200) down the ramp, length 50 pixels, labeled 'F_gravity'.
     * Place label 'θ' near (70, 260).

Format your response exactly as follows:

Question:
[question text]

Answer Choices:
A) ...
B) ...
C) ...
D) ...

Correct Answer: [Letter]

Diagram description:
- [list diagram elements as bullet points with pixel coordinates]

Do NOT include any SVG code or programming code.
Do NOT reuse any text from the question in the diagram description.
The diagram description should be clear and precise for an SVG renderer to follow.
'''
    messages = [
        {
            "role": "system",
            "content": "Generate rigorous AP Physics questions with LaTeX and precise SVG-style diagram descriptions with pixel coordinates.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_question,
            max_tokens=max_tokens_question + 400,  # extra tokens for diagram desc
        )
        full_text = response.choices[0].message.content.strip()

        # Parse question and diagram description
        parts = full_text.split("Diagram description:")
        question_text = parts[0].strip()
        diagram_desc = parts[1].strip() if len(parts) > 1 else ""
        return question_text, diagram_desc
    except Exception as e:
        st.error(f"OpenAI API call failed (generate_question_and_diagram_desc): {e}")
        return None, None


def generate_svg(diagram_desc: str) -> str | None:
    tutorial = '''
You are a Python SVG expert using the svgwrite library.

Generate SVG diagrams based exactly on the provided detailed diagram description with pixel coordinates.

Instructions:
1. Use a canvas size of 400x300 pixels.
2. Start with a white background rectangle covering the entire canvas.
3. For each bullet point in the diagram description:
   - Parse coordinates and shapes precisely.
   - Draw lines, circles, rectangles, and arrows exactly at specified pixel positions.
   - Use a red arrow marker with id 'arrow' for arrows.
   - Label text exactly at the given coordinates.
4. Do NOT add or change coordinates; follow the description exactly.
5. Use clear Python code with comments.
6. Return the SVG XML string with `return dw.tostring()`.
7. Output ONLY the Python function `draw_diagram()`. No markdown, no extra text.

Example snippet for an arrow line:
```python
arrow = dw.marker(insert=(10,5), size=(10,10), orient="auto", id="arrow")
arrow.add(dw.path(d="M0,0 L10,5 L0,10 L2,5 Z", fill="red"))
dw.defs.add(arrow)
line = dw.line(start=(150, 200), end=(200, 150), stroke="black", stroke_width=2, marker_end="url(#arrow)")
dw.add(line)
'''
    prompt = f'''
You are a physics diagram expert.

{tutorial}

Diagram description:
"""{diagram_desc}"""
'''
    messages = [
        {"role": "system", "content": "You generate clean, error-free Python SVG drawing functions."},
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
        st.error(f"OpenAI API call failed (generate_svg): {e}")
        return None


def generate_explanation(question_text: str) -> str | None:
    prompt = f'''
You are an excellent AP Physics C tutor.

Instructions:

Write a detailed, step-by-step explanation suitable for AP Physics C students.

Use LaTeX formatting for all mathematical formulas and expressions.

Refer explicitly to diagram elements like arrows and forces.

Use clear physics terminology and explain concepts thoroughly.

Format your explanation in readable paragraphs.

Given the question below, write a very detailed and thorough explanation suitable for a top AP Classroom solution.

Question:
"""{question_text}"""
'''
    messages = [
        {"role": "system", "content": "You provide clear, detailed AP Physics explanations with LaTeX."},
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
        st.error(f"OpenAI API call failed (generate_explanation): {e}")
        return None


def execute_svg_code(code: str) -> str | None:
    code = clean_code_block(code)
    # Fix marker_end syntax if assigned directly to marker object
    code = code.replace("marker_end=arrow", 'marker_end="url(#arrow)"')

    local_vars = {}
    try:
        exec(code, {"svgwrite": svgwrite}, local_vars)
    except Exception as e:
        st.error(f"Error executing SVG code: {e}")
        return None

    if "draw_diagram" not in local_vars:
        st.error("draw_diagram() function not found in SVG code.")
        return None

    try:
        svg_str = local_vars["draw_diagram"]()
        return svg_str
    except Exception as e:
        st.error(f"Error running draw_diagram(): {e}")
        return None


if st.button("Generate Question, Diagram & Explanation"):

    if not topic.strip():
        st.warning("Please enter a physics topic!")
        st.stop()

    # Generate question and diagram description
    with st.spinner("Generating AP Physics C question and diagram description..."):
        raw_question, diagram_description = generate_question_and_diagram_desc(topic)

    if not raw_question or not diagram_description:
        st.error("Failed to generate question or diagram description.")
        st.stop()

    # Show question + diagram description (for testing)
    st.markdown("### Generated Question")
    st.markdown(raw_question, unsafe_allow_html=True)  # LaTeX enabled

    st.markdown("### Diagram Description (for testing, can hide later)")
    st.text(diagram_description)

    # Generate SVG code from diagram description
    with st.spinner("Generating SVG diagram..."):
        svg_code = generate_svg(diagram_description)

    if not svg_code:
        st.warning("Failed to generate SVG code.")
        st.stop()

    st.subheader("Generated SVG Python Code")
    st.code(svg_code, language="python")

    svg_str = execute_svg_code(svg_code)
    if svg_str:
        st.subheader("Diagram")
        st.components.v1.html(
            f"""<div style="border:1px solid #ccc; max-width:420px;">{svg_str}</div>""",
            height=320,
        )
    else:
        st.warning("SVG diagram could not be rendered due to errors.")
        st.stop()

    # Generate explanation
    with st.spinner("Generating detailed explanation..."):
        explanation = generate_explanation(raw_question)

    if explanation:
        st.markdown("### Detailed Explanation")
        st.markdown(explanation, unsafe_allow_html=True)  # LaTeX enabled
    else:
        st.warning("Failed to generate explanation.")
