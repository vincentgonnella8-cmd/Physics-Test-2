import streamlit as st
import os
from openai import OpenAI
import svgwrite

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
    code_block_fixed = code_block.replace(
        'marker_end=arrow', 'marker_end="url(#arrow)"'
    ).replace(
        "marker_end=arrow", 'marker_end="url(#arrow)"'
    )
    local_vars = {}
    exec(code_block_fixed, {"svgwrite": svgwrite}, local_vars)
    if 'draw_diagram' in local_vars:
        return local_vars['draw_diagram']()
    else:
        raise RuntimeError("No draw_diagram() function found in SVG code.")

st.write("### Step 1: Enter your physics question or topic")

user_input = st.text_area("Physics question prompt", height=100)

if st.button("Generate Question & Explanation"):
    if not user_input.strip():
        st.warning("Please enter a prompt!")
    else:
        with st.spinner("Generating physics question, answer, and explanation..."):
            explanation_response = generate_physics_explanation(user_input)
            st.session_state['history'].append({"role": "assistant_explanation", "content": explanation_response})
            st.success("Explanation generated!")

if any(h['role'] == "assistant_explanation" for h in st.session_state['history']):
    latest_exp = [h for h in st.session_state['history'] if h['role'] == "assistant_explanation"][-1]['content']

    st.markdown("### Generated Question & Explanation")
    st.markdown(latest_exp, unsafe_allow_html=True)

    st.write("---")
    st.write("### Step 2: Enter a description of the diagram to generate")

    diagram_desc = st.text_area(
        "Diagram description (e.g. 'Draw a block of mass m on a frictionless surface with a force arrow pointing right')",
        height=100
    )

    if st.button("Generate Diagram SVG"):
        if not diagram_desc.strip():
            st.warning("Please enter a diagram description!")
        else:
            with st.spinner("Generating SVG code..."):
                svg_code_response = generate_svg_code(diagram_desc)

            if "def draw_diagram" in svg_code_response:
                try:
                    code_start = svg_code_response.index("def draw_diagram")
                    code_block = svg_code_response[code_start:].strip()

                    svg_str = execute_svg_code(code_block)
                    st.image(svg_str)
                    st.success("SVG Diagram rendered successfully!")
                except Exception as e:
                    st.error(f"Error rendering SVG diagram: {e}")
                    st.text(svg_code_response)
            else:
                st.error("SVG code not found in the AI response.")
                st.text(svg_code_response)
