from pdfminer.high_level import extract_text
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os

genai.configure(api_key="AIzaSyBYmelcY4b7uCVR8cgvLXOAJb9RjAYqY18")
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

def extract_data_from_report(pdf_path):
    return extract_text(pdf_path)

def process_medical_report(file_path):
    data = extract_data_from_report(file_path)

    prompt = f"""You are a health assistant AI designed to analyze medical reports and provide patients with simple, 
    personalized, and actionable advice based on their diagnosis, test results, medications, and doctor's notes. 
    Use the given report to provide detailed insights and recommendations in the following categories:
    Dietary Advice:
    Suggest foods the patient should eat and avoid based on their diagnosis and lab results (e.g., low glycemic index foods for diabetes, foods to reduce cholesterol, and foods that support kidney health).
    Provide meal planning tips for managing blood sugar levels effectively.
    Exercise Recommendations:
    Recommend appropriate exercises and their duration based on the patient's condition (e.g., low-impact exercises for beginners, strength training, or aerobic activities for diabetes management).
    Highlight precautions they need to take during physical activity.
    Lifestyle Adjustments:
    Suggest changes to improve overall health, such as better sleep habits, stress management techniques, and hydration.
    Identify harmful habits (e.g., alcohol or smoking) and recommend ways to reduce or eliminate them.
    Medication Adherence:
    Explain the importance of taking prescribed medications consistently and any common side effects they should watch for.
    Follow-Up Appointments and Tests:
    Highlight necessary follow-up appointments and tests mentioned in the report, such as HbA1c rechecks, cholesterol monitoring, eye exams, and kidney function tests.
    Complication Awareness:
    Warn the patient about potential complications they should be aware of (e.g., diabetic neuropathy, heart disease) and how to recognize early signs.
    General Motivation:
    Encourage the patient with positive language to stay motivated and committed to improving their health.
    When responding, address the patient in clear, friendly, and simple language. Tailor your advice based on the specific details in the report, such as blood sugar levels, cholesterol profile, kidney function, and lifestyle observations.
    Here's the report for analysis: {data}
    Provide actionable steps the patient can follow in each category and organize your response in clear sections."""

    try:
        response = model.generate_content(prompt)
        insights = response.text
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation error: {e}")
    
def markdown_to_formatted_paragraphs(markdown_text, styles):
    elements = []
                
    lines = markdown_text.split('\n')
                
    for line in lines:
        if line.startswith('# '):
            elements.append(Paragraph(line.replace('# ', ''), styles['Title']))
        elif line.startswith('## '):
            elements.append(Paragraph(line.replace('## ', ''), styles['Heading2']))
        elif line.startswith('### '):
            elements.append(Paragraph(line.replace('### ', ''), styles['Heading3']))
        elif '**' in line:
            formatted_line = line.replace('**', '<b>', 1).replace('**', '</b>', 1)
            elements.append(Paragraph(formatted_line, styles['Normal']))
        elif '*' in line and line.count('*') == 2:
            formatted_line = line.replace('*', '<i>', 1).replace('*', '</i>', 1)
            elements.append(Paragraph(formatted_line, styles['Normal']))  
        elif line.startswith('- '):
            formatted_line = line.replace('- ', '• ', 1)
            elements.append(Paragraph(formatted_line, styles['Normal']))
        elif line.strip():
            elements.append(Paragraph(line, styles['Normal']))
                
    return elements

def create_pdf(output_text, file_name="Patient_Advice.pdf"):
    pdf = SimpleDocTemplate(file_name, pagesize=letter)

    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CustomTitle",
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#4B9CD3"),
    ))
    styles.add(ParagraphStyle(
        name="CustomHeading2",
        fontSize=14,
        leading=18,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="CustomHeading3",
        fontSize=12,
        leading=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="CustomNormal",
        fontSize=12,
        leading=14,
        spaceAfter=6,
    ))

    elements = [Paragraph("Personalized Diabetes Care Report", styles['CustomTitle']), Spacer(1, 12)]

    formatted_elements = markdown_to_formatted_paragraphs(output_text, styles)
    elements.extend(formatted_elements)

    pdf.build(elements)
    return file_name

@app.post("/generate-report/")
async def generate_report(file: UploadFile = File(...)):
    try:
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file.file.read())

        insights = process_medical_report(temp_file_path)

        pdf_path = create_pdf(insights)

        os.remove(temp_file_path)

        return FileResponse(pdf_path, media_type="application/pdf", filename="Patient_Advice.pdf")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {e}")
