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
    prompt = f"""
You are a physics diagram expert.

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
