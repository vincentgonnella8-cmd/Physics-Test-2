import streamlit as st
import re
from openai import OpenAI

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
max_tokens_question = st.sidebar.slider("Question Max Tokens", 200, 1000, 600, 10)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 100, 1024, 512)
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.8, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 500, 2048, 1400, 10)

st.title("AP Physics C Tutor — Question, Diagram & Explanation Generator")

topic = st.text_input("Enter the Physics Topic (e.g. Rotational Motion, Energy Conservation):", "Rotational Motion")

def clean_code_block(code: str) -> str:
    """Remove markdown fences if any."""
    code = code.strip()
    if code.startswith("```"):
        code = "\n".join(code.splitlines()[1:])
    if code.endswith("```"):
        code = "\n".join(code.splitlines()[:-1])
    return code.strip()

def render_markdown_with_latex(text: str):
    # Convert newlines to Markdown line breaks for better formatting
    text = text.replace('\n', '  \n')
    st.markdown(text, unsafe_allow_html=True)

def generate_question_and_diagram_desc(topic: str) -> tuple[str | None, str | None]:
    prompt = f'''
You are an AP Physics C expert.

Generate ONE original multiple-choice question on "{topic}", with clear LaTeX formatting.

Then provide a detailed textual description of the diagram illustrating the problem setup.
This description will be used to generate an SVG diagram.

Format your response as:

Question:
[question text]

Answer Choices:
A) ...
B) ...
C) ...
D) ...

Correct Answer: [Letter]

Diagram description:
[Describe the key elements, shapes, arrows, labels, and spatial relations of the diagram.]
'''
    messages = [
        {"role": "system", "content": "Generate rigorous AP Physics questions with LaTeX, and detailed diagram descriptions."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_question,
            max_tokens=max_tokens_question + 300  # extra tokens for diagram desc
        )
        full_text = response.choices[0].message.content.strip()
        
        # Parse question and diagram description
        parts = re.split(r"\s*Diagram description:\s*", full_text, flags=re.IGNORECASE)
        question_text = parts[0].strip()
        diagram_desc = parts[1].strip() if len(parts) > 1 else ""
        return question_text, diagram_desc
    except Exception as e:
        st.error(f"OpenAI API call failed (generate_question_and_diagram_desc): {e}")
        return None, None

def generate_svg(diagram_desc: str) -> str | None:
    tutorial = '''
You are a Python SVG expert using the svgwrite library.

Here is a detailed guide on how to generate SVG diagrams:

1. Setup Canvas:
   - Create the drawing with size 400x300 pixels:
     dw = svgwrite.Drawing(size=("400px", "300px"))
   - Add a white background rectangle covering the entire canvas:
     dw.add(dw.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))

2. Markers (Arrowheads):
   - Define reusable markers for arrows using dw.marker:
     arrow = dw.marker(insert=(10, 5), size=(10, 10), orient="auto", id="arrow")
     arrow.add(dw.path(d="M0,0 L10,5 L0,10 L2,5 Z", fill="red"))
     dw.defs.add(arrow)
   - Use marker_end="url(#arrow)" string on lines, do NOT assign marker objects directly.

3. Basic Shapes:
   - Lines: dw.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=2)
   - Circles: dw.circle(center=(x, y), r=radius, stroke="black", fill="none")
   - Rectangles: dw.rect(insert=(x, y), size=(width, height), fill="none", stroke="black")

4. Text:
   - Use dw.text("Label", insert=(x, y), fill="black", font_size="12px")

5. Return the SVG string:
   - Use return dw.tostring()

Please strictly output ONLY the Python function draw_diagram(), no markdown or explanations.
'''
    prompt = f'''
You are a physics diagram expert.

{tutorial}

Based on the following diagram description, generate a Python function named draw_diagram() using the svgwrite library that creates a 2D SVG diagram illustrating the problem setup.

Requirements:
- Output ONLY the Python function draw_diagram() (no markdown).
- Canvas size: 400x300 px.
- White background rectangle.
- Strictly 2D elements only.
- Return the SVG XML string via dw.tostring().

Diagram description:
\"\"\"{diagram_desc}\"\"\"
'''
    messages = [
        {"role": "system", "content": "You generate clean, error-free Python SVG drawing functions."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_svg,
            max_tokens=max_tokens_svg
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API call failed (generate_svg): {e}")
        return None

def generate_explanation(question_text: str) -> str | None:
    prompt = f'''
You are an excellent AP Physics C tutor.

Instructions:
- Write a detailed, step-by-step explanation suitable for AP Physics C students.
- Use LaTeX formatting for all mathematical formulas and expressions.
- Refer explicitly to diagram elements like arrows and forces.
- Use clear physics terminology and explain concepts thoroughly.
- Format your explanation in readable paragraphs.

Given the question below, write a very detailed and thorough explanation suitable for a top AP Classroom solution.

Question:
\"\"\"{question_text}\"\"\"
'''
    messages = [
        {"role": "system", "content": "You provide clear, detailed AP Physics explanations with LaTeX."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_explanation,
            max_tokens=max_tokens_explanation
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API call failed (generate_explanation): {e}")
        return None

def execute_svg_code(code: str) -> str | None:
    import svgwrite

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

    st.markdown("### Generated Question")
    render_markdown_with_latex(raw_question)

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
        st.components.v1.html(f"""<div style="border:1px solid #ccc; max-width:420px;">{svg_str}</div>""", height=320)
    else:
        st.warning("SVG diagram could not be rendered due to errors.")
        st.stop()

    # Generate explanation
    with st.spinner("Generating detailed explanation..."):
        explanation = generate_explanation(raw_question)

    if explanation:
        st.markdown("### Detailed Explanation")
        render_markdown_with_latex(explanation)
    else:
        st.warning("Failed to generate explanation.")
