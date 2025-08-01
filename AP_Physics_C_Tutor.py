import streamlit as st
from openai import OpenAI
import re

# --- Config ---
API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please add OPENAI_API_KEY in Streamlit Secrets or environment variables.")
    st.stop()

client = OpenAI(api_key=API_KEY)
MODEL_NAME = "gpt-4.1"

# --- Sidebar for parameters ---
st.sidebar.title("Model Parameters")
temp_question = st.sidebar.slider("Question Temperature", 0.0, 1.0, 0.7, 0.1)
max_tokens_question = st.sidebar.slider("Question Max Tokens", 200, 800, 450, 10)
temp_svg = st.sidebar.slider("SVG Temperature", 0.0, 1.0, 0.3, 0.1)
max_tokens_svg = st.sidebar.slider("SVG Max Tokens", 100, 1024, 512)
temp_explanation = st.sidebar.slider("Explanation Temperature", 0.0, 2.0, 0.8, 0.1)
max_tokens_explanation = st.sidebar.slider("Explanation Max Tokens", 500, 2048, 1400, 10)

# --- Main UI ---
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

def generate_question(topic: str) -> str:
    """Generate a single AP Physics C question (MCQ) with answer choices and correct answer."""
    prompt = f"""
You are an AP Physics C: Mechanics expert preparing students for their exam.

Generate ONE original, rigorous multiple-choice question on the topic of "{topic}".

Format your response as follows (no extra text):

Question:
[Insert question text here]

Answer Choices:
A) ...
B) ...
C) ...
D) ...

Correct Answer: [Letter]

Provide no explanation here.
"""
    messages = [
        {"role": "system", "content": "You generate AP Physics C style questions."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_question,
        max_tokens=max_tokens_question
    )
    return response.choices[0].message.content.strip()

def generate_svg(question_text: str) -> str:
    """Generate SVG code as a Python function draw_diagram() using svgwrite based on question."""
    prompt = f"""
You are a physics diagram expert.

Based on the following AP Physics C question, generate a Python function named draw_diagram() that uses the svgwrite library to create a 2D SVG diagram illustrating the problem setup.

Requirements:
- Output ONLY the Python function draw_diagram() (no markdown).
- The function should create an SVG canvas of size 400x300 px.
- Include a white background rectangle.
- Define a red arrow marker with id 'arrow' and use it on at least one line.
- Use clear comments.
- Stick strictly to 2D SVG elements.
- Return the SVG XML string via dw.tostring().

Question:
\"\"\"{question_text}\"\"\"
"""
    messages = [
        {"role": "system", "content": "You generate clean, error-free Python SVG drawing functions."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_svg,
        max_tokens=max_tokens_svg
    )
    return response.choices[0].message.content.strip()

def generate_explanation(question_text: str) -> str:
    """Generate a detailed explanation referencing the question and diagram."""
    prompt = f"""
You are an excellent AP Physics C tutor.

Given the question below, write a very detailed and thorough explanation suitable for a top AP Classroom solution.

Include references to diagram elements (e.g., arrows, forces) as if the student can see the generated diagram.

Use LaTeX formatting for formulas.

Question:
\"\"\"{question_text}\"\"\"
"""
    messages = [
        {"role": "system", "content": "You provide clear, detailed AP Physics explanations."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temp_explanation,
        max_tokens=max_tokens_explanation
    )
    return response.choices[0].message.content.strip()

def execute_svg_code(code: str) -> str | None:
    """Run the draw_diagram function code to get SVG string."""
    import svgwrite
    import textwrap

    code = clean_code_block(code)

    # Fix common marker syntax if needed
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

def extract_question_text(raw_question: str) -> str:
    """Extract only the question text portion before Answer Choices."""
    match = re.search(r"Question:(.*?)(?:Answer Choices:|Correct Answer:|$)", raw_question, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_question.strip()

# --- Main button logic ---
if st.button("Generate Question, Diagram & Explanation"):

    if not topic.strip():
        st.warning("Please enter a physics topic!")
        st.stop()

    with st.spinner("Generating AP Physics C question..."):
        raw_question = generate_question(topic)

    st.markdown("### Generated Question")
    st.markdown(raw_question)

    question_text = extract_question_text(raw_question)

    with st.spinner("Generating SVG diagram..."):
        svg_code = generate_svg(question_text)

    st.subheader("Generated SVG Python Code")
    st.code(svg_code, language="python")

    svg_str = execute_svg_code(svg_code)
    if svg_str:
        # Display SVG inline using HTML component
        st.subheader("Diagram")
        svg_html = f"""<div style="border:1px solid #ccc; max-width:420px;">{svg_str}</div>"""
        st.components.v1.html(svg_html, height=320)
    else:
        st.warning("SVG diagram could not be rendered due to errors.")

    with st.spinner("Generating detailed explanation..."):
        explanation = generate_explanation(raw_question)

    st.markdown("### Detailed Explanation")
    st.markdown(explanation, unsafe_allow_html=True)
