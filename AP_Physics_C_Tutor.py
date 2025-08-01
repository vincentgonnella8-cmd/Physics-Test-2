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
max_tokens_question = st.sidebar.slider("Question Max Tokens", 200, 800, 450, 10)
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

def fix_marker_end(code: str) -> str:
    """
    Replace all instances of marker_end=variable
    with marker_end="url(#variable)" to fix svgwrite usage.
    """
    pattern = r'marker_end\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)'
    def repl(m):
        var_name = m.group(1)
        return f'marker_end="url(#{var_name})"'
    return re.sub(pattern, repl, code)

def generate_question(topic: str) -> str | None:
    prompt = f"""
You are an AP Physics C: Mechanics expert preparing students for their exam.

Generate ONE original, rigorous multiple-choice question on the topic of "{topic}".

Format your response exactly as:

Question:
[question text]

Answer Choices:
A) ...
B) ...
C) ...
D) ...

Correct Answer: [Letter]

Do NOT include an explanation here.
"""
    messages = [
        {"role": "system", "content": "You generate AP Physics C style questions."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_question,
            max_tokens=max_tokens_question
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API call failed (generate_question): {e}")
        return None

def generate_svg(question_text: str) -> str | None:
    # Full SVG tutorial prompt added here:
    tutorial = """
You are a Python SVG expert using the `svgwrite` library. Here's a detailed guide on how to generate SVG diagrams:

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
   - To use the marker on a line or path, set marker_end to "url(#arrow)" (a string):
     line = dw.line(start=(50, 100), end=(150, 100), stroke="black", stroke_width=2, marker_end="url(#arrow)")
   - Do NOT assign the marker object directly (e.g., marker_end=arrow), as SVG expects a URL string reference.

3. Basic Shapes:
   - Add lines:
     dw.add(dw.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=2))
   - Add circles:
     dw.add(dw.circle(center=(x, y), r=radius, stroke="black", fill="none"))
   - Add rectangles:
     dw.add(dw.rect(insert=(x, y), size=(width, height), fill="none", stroke="black"))

4. Text:
   - Add labels using dw.text:
     dw.add(dw.text("Label", insert=(x, y), fill="black", font_size="12px"))

5. Comments:
   - Add comments in the Python code to explain what each section does.

6. Return the SVG string:
   - Finish by returning the SVG XML string with:
     return dw.tostring()

7. Important:
   - Use only 2D elements.
   - Use clear and concise code.
   - Avoid markdown or extra text; output only the Python function draw_diagram().

Example function:

def draw_diagram():
    import svgwrite
    dw = svgwrite.Drawing(size=("400px", "300px"))
    dw.add(dw.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))

    # Define red arrow marker
    arrow = dw.marker(insert=(10, 5), size=(10, 10), orient="auto", id="arrow")
    arrow.add(dw.path(d="M0,0 L10,5 L0,10 L2,5 Z", fill="red"))
    dw.defs.add(arrow)

    # Draw a black line with arrowhead
    line = dw.line(start=(50, 100), end=(150, 100), stroke="black", stroke_width=2, marker_end="url(#arrow)")
    dw.add(line)

    # Add label near line
    dw.add(dw.text("Force", insert=(60, 90), fill="black", font_size="12px"))

    return dw.tostring()

Please strictly follow these instructions when generating the SVG Python code.
"""
    prompt = f"""
You are a physics diagram expert.

{tutorial}

Based on the following AP Physics C question, generate a Python function named draw_diagram() using the svgwrite library that creates a 2D SVG diagram illustrating the problem setup.

Requirements:
- Output ONLY the Python function draw_diagram() (no markdown).
- Canvas size: 400x300 px.
- White background rectangle.
- Red arrow marker with id 'arrow' used on at least one line.
- Clear comments.
- Strictly 2D elements only.
- Return the SVG XML string via dw.tostring().

Question:
\"\"\"{question_text}\"\"\"
"""
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
    prompt = f"""
You are an excellent AP Physics C tutor.

Given the question below, write a very detailed and thorough explanation suitable for a top AP Classroom solution.

Include references to diagram elements (e.g., arrows, forces).

Use LaTeX formatting for formulas.

Question:
\"\"\"{question_text}\"\"\"
"""
    messages = [
        {"role": "system", "content": "You provide clear, detailed AP Physics explanations."},
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
    code = fix_marker_end(code)  # <-- improved marker_end fix

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

def extract_question_text(raw_question: str) -> str:
    match = re.search(r"Question:(.*?)(?:Answer Choices:|Correct Answer:|$)", raw_question, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_question.strip()

if st.button("Generate Question, Diagram & Explanation"):

    if not topic.strip():
        st.warning("Please enter a physics topic!")
        st.stop()

    # Generate question
    with st.spinner("Generating AP Physics C question..."):
        raw_question = generate_question(topic)

    if not raw_question:
        st.stop()

    st.markdown("### Generated Question")
    st.markdown(raw_question)

    question_text = extract_question_text(raw_question)

    # Generate SVG
    with st.spinner("Generating SVG diagram..."):
        svg_code = generate_svg(question_text)

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
        st.markdown(explanation, unsafe_allow_html=True)
    else:
        st.warning("Failed to generate explanation.")
