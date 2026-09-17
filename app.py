import streamlit as st
import re
import subprocess
import os

# --- CORE LOGIC (Same as your terminal script) ---
def calculate_water_deficit(current_moisture, target_moisture, farm_area_sq_meters):
    if current_moisture >= target_moisture: return 0.0
    return round((target_moisture - current_moisture) * farm_area_sq_meters * 10, 2)

def check_borewell_supply(daily_yield_limit, water_already_pumped):
    return max(daily_yield_limit - water_already_pumped, 0.0)

def validate_decision(planner_output, max_available_water):
    match = re.search(r'DECISION:\s*([\d\.]+)', planner_output)
    if not match: return False, "Error: Could not find DECISION line."
    planned_water = float(match.group(1))
    if planned_water > max_available_water:
        return False, f"Logic Error: Scheduled {planned_water}L, but only {max_available_water}L available."
    return True, "Passed."

def sanitize_latex(text: str) -> str:
    text = text.replace('\\', r'\textbackslash{}')
    for char in ['&', '%', '$', '#', '_', '{', '}']:
        text = text.replace(char, '\\' + char)
    text = text.replace('\n\n', '\\par\n').replace('\n', '\\newline\n')
    return text

def generate_pdf_report(plan_text, decision_liters, next_steps_text):
    safe_plan = sanitize_latex(plan_text)
    safe_steps = sanitize_latex(next_steps_text)
    
    tex_template = f"""\\documentclass[12pt]{{article}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=1in}}
\\usepackage{{helvet}}
\\renewcommand{{\\familydefault}}{{\\sfdefault}}

\\title{{Autonomous Irrigation Schedule}}
\\author{{Agentic AI System}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section*{{Agent Reasoning}}
{safe_plan}

\\section*{{Final Execution}}
Total Water Allocated: \\textbf{{{decision_liters} Liters}}

\\section*{{Next Steps \\& Guidelines}}
{safe_steps}
\\end{{document}}"""

    tex_filename = "daily_irrigation_report.tex"
    with open(tex_filename, "w") as file:
        file.write(tex_template)
        
    subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], capture_output=True)

# --- WEB DASHBOARD UI ---
st.set_page_config(page_title="Smart Farm AI", layout="centered")

st.title("🌱 Autonomous Irrigation Planner")
st.write("Enter the live farm data below to generate an AI-optimized watering schedule.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    current_moisture = st.number_input("Current Soil Moisture (%)", value=40.0)
    target_moisture = st.number_input("Target Soil Moisture (%)", value=60.0)
    farm_area = st.number_input("Farm Area (sq meters)", value=500.0)
with col2:
    daily_yield = st.number_input("Daily Borewell Capacity (Liters)", value=4000.0)
    pumped_today = st.number_input("Water Pumped Today (Liters)", value=1500.0)

if st.button("Generate Smart Schedule", type="primary"):
    with st.spinner("AI Agent is reasoning and checking constraints..."):
        deficit = calculate_water_deficit(current_moisture, target_moisture, farm_area)
        supply = check_borewell_supply(daily_yield, pumped_today)
        
        # Simulated Initial Output
        initial_output = f"""PLAN: Target deficit is {deficit} Liters.
DECISION: {deficit}
NEXT STEPS: Monitor soil absorption."""
        
        is_valid, feedback = validate_decision(initial_output, supply)
        
        if not is_valid:
            st.warning("Critic Agent Intercepted: Water limit exceeded. Reflecting and correcting...")
            final_output = f"""PLAN: Deficit is {deficit}L, but supply is limited to {supply}L. Capping schedule to maximum available safe limit.
DECISION: {supply}
NEXT STEPS: Pump remaining capacity. Schedule remainder for tomorrow."""
        else:
            st.success("Critic Agent Approved: Operation is within safe limits.")
            final_output = initial_output

        # Extract for PDF
        match_decision = re.search(r'DECISION:\s*([\d\.]+)', final_output)
        decision_liters = float(match_decision.group(1)) if match_decision else 0.0
        generate_pdf_report(final_output, decision_liters, "Ensure drip lines are clear.")
        
        st.subheader("Final Operational Plan")
        st.info(final_output)

        # Provide Download Button
        if os.path.exists("daily_irrigation_report.pdf"):
            with open("daily_irrigation_report.pdf", "rb") as pdf_file:
                st.download_button(
                    label="📄 Download Official PDF Report",
                    data=pdf_file,
                    file_name="daily_irrigation_report.pdf",
                    mime="application/pdf"
                )