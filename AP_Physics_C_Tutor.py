def generate_question(topic: str) -> str | None:
    prompt = f'''
You are an AP Physics C: Mechanics expert preparing students for their exam.

Instructions:
- Use LaTeX formatting for all physics formulas, enclosed in $...$ or $$...$$.
- Format your question clearly and concisely.
- Provide answer choices labeled A) through D).
- Do NOT include explanations or extra commentary.
- Use correct physics terminology and symbols.

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
'''
    messages = [
        {"role": "system", "content": "You generate AP Physics C style questions with clear LaTeX formatting."},
        {"role": "user", "content": prompt}
    ]

    # rest of function ...

def generate_svg(question_text: str) -> str | None:
    tutorial = '''
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
'''
    prompt = f'''
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
'''
    messages = [
        {"role": "system", "content": "You generate clean, error-free Python SVG drawing functions."},
        {"role": "user", "content": prompt}
    ]

    # rest of function ...

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

Include references to diagram elements (e.g., arrows, forces).

Use LaTeX formatting for formulas.

Question:
\"\"\"{question_text}\"\"\"
'''
    messages = [
        {"role": "system", "content": "You provide clear, detailed AP Physics explanations with LaTeX."},
        {"role": "user", "content": prompt}
    ]

    # rest of function ...
