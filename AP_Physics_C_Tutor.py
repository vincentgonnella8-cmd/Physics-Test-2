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
Always express math using LaTeX syntax: inline math with $ ... $,
block math with $$ ... $$ for standalone equations. 
Avoid plaintext math (e.g., never 'F = ma', always use $ F = ma $. 
Describe diagrams in strict SVG structure, no physics in diagram descriptions.

1. Generate ONE original multiple-choice physics question on the topic "{topic}".
   Use clear LaTeX formatting for all formulas.
   Provide the question and answer choices only.

2. Next, create a detailed, precise diagram description intended for generating an SVG image.

   The SVG canvas size is fixed at 800 pixels wide by 600 pixels high.
   All coordinates must fit within this 800x600 pixel canvas.
   Try to keep ALL parts of the diagram cleanly in view

   Use the following SVG drawing conventions when writing the diagram description:
   - Coordinates start at the top left of (0,0)
   - Use <polygon> for ramps, always making a RIGHT triangle for inclines
   - Circles are drawn by specifying the center coordinate (x, y) and the radius.
   - If a circle is on a ramp, align the BOTTOM EDGE of the circle to the ramp; If the center of the circle is on the ramp, move it down by one radius of the circle
   - ALL ramps and inclines will go UP and RIGHT; normal force is (very often) PERPENDICULAR to the ground
   - Lines are drawn between two points specified by their start and end coordinates.
   - Arrows are lines with a direction indicated by start and end points.
   - Labels are placed at exact (x, y) coordinates.
   - All shapes should be outlines only.
   - Assume a white background canvas of 800x600 pixels is already provided.
   - Avoid using language from the question text.
   - List each diagram element as a bullet point with coordinates and sizes.

    THE FOLLOWING IS AN EXAMPLE OF FORMATTING THE DIAGRAM DESCRIPTION, REFER TO THIS IF THE FORMATTING IS OFF [
        1. Use a <polygon> to draw a right triangle:
            * Base point: (50, 350)
            * Top point of the incline: (150, 150)
            * Right base: (550, 350)
        2. Use a <circle> centered at (250, 200) with a radius of 40.
        3. Use <line> elements with arrowheads:
                * Gravity (F<sub>g</sub>)
                    - From (250, 200) to (250, 280) (straight down)
                * Push Component (F<sub>p</sub>)
                    - From (250, 200) to (310, 260) (diagonal down-right)
                * Pull Component (F - pull)
                    - From (250, 200) to (190, 240) (diagonal up-left)
                * Reaction Force (F<sub>r</sub>)
                    - From (250, 200) to (220, 110) (diagonal upward, perpendicular to incline)
                * Friction Force (F<sub>f</sub>)
                    - From (250, 200) to (330, 160) (up the slope)
         4. Use <text> elements near the endpoints of each line.
                * E.g., place F_g - gravity at (260, 270)
                * Use font-style="italic" and matching colors for clarity
         5. Use a <path> element to draw a circular arc at the base of the slope:
                    - Start at (60, 350), end at (80, 330)
                * Fill it light pink and label it with α using <text>
         6. Use a <defs> block and a <marker> with a triangle shape to define arrows:
                     <marker id="arrow" ...>
                         <path d="M0,0 L0,6 L9,3 z" fill="inherit"/>
                     </marker>
                * Add marker-end="url(#arrow)" to each <line>
    ]

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
Always express math using LaTeX syntax: inline math with $ ... $,
block math with $$ ... $$ for standalone equations. 
Avoid plaintext math (e.g., never 'F = ma', always use $ F = ma $. 
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
8. Do NOT use any extra text or comments; ONLY put raw SVG code
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
        scale_factor = 1
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
                transform-origin: top left;
            ">
                {svg_str}
            </div>
            """,
            height=scaled_height,
            width=scaled_width,
        )
    else:
        st.warning("SVG rendering failed.")
        st.stop()

