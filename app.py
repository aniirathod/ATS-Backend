from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import fitz  # PyMuPDF for PDF text extraction
import google.generativeai as genai

load_dotenv()
app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Extract text from PDF
def extract_text_from_pdf(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Gemini evaluation
def evaluate_resume(prompt, resume_text, job_description):
    model = genai.GenerativeModel('gemini-1.5-flash')
    input_parts = [prompt, f"\nResume:\n{resume_text}", f"\nJob Description:\n{job_description}"]
    response = model.generate_content(input_parts)
    return response.text

# Endpoint to handle resume scan
@app.route('/scan-resume', methods=['POST'])
def scan_resume():
    if 'resume' not in request.files or 'job_description' not in request.form or 'mode' not in request.form:
        return jsonify({"error": "Missing data"}), 400

    resume_file = request.files['resume']
    job_description = request.form['job_description']
    mode = request.form['mode']  # "summary" or "percentage"

    try:
        pdf_bytes = resume_file.read()
        resume_text = extract_text_from_pdf(pdf_bytes)

        if mode == "summary":
            prompt = """
You are an experienced Technical HR Manager. Review the following resume in context of the given job description. 
Evaluate strengths, weaknesses, and give a summary of how well the candidate fits.
"""
        elif mode == "percentage":
            prompt = """
You are an ATS scanner. Analyze the following resume against the job description. 
Output:
1. Match percentage
2. Missing keywords
3. Suggestions to improve the resume.
"""
        else:
            return jsonify({"error": "Invalid mode"}), 400

        result = evaluate_resume(prompt, resume_text, job_description)
        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
