import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from docx import Document
import json

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = pdf.PdfReader(file)
    text = ""
    for page in range(len(reader.pages)):
        text += reader.pages[page].extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

# GenAI request function
def get_gemini_response(input_prompt, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_prompt)
    return json.loads(response.text)  # Assuming the response is a JSON string

# Input prompt template for GenAI
input_prompt_template = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System).
Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide 
best assistance for improving the resumes. Assign the percentage Matching based 
on JD and
the missing keywords with high accuracy.
resume: {text}
description: {jd}
weights: {weights}

I want the response in one single string having the structure
{{"CandidateName": "", "OverallScore":"%", "ExperienceScore":"%", "AdditionalExperienceNeeded": "", "SkillsScore":"%", "AdditionalSkillsNeeded": "", "EducationMatch":"%", "AdditionalEducationNeeded": "", "CertificationMatch":"%", "AdditionalCertificationsNeeded": "", "QuantifiableResultsMatch":"%", "AreasNeedingImprovement": ""}}
"""

# Streamlit app
st.title("Resume and Job Description Matcher")

st.markdown("""
This tool helps recruiters and hiring managers quickly evaluate how well a candidate's CV matches a job description. Here's how to use it:

1. **Upload the Candidate's CVs**: You can upload multiple PDFs or Word documents of the candidate's CVs.
2. **Enter the Job Description**: Copy and paste the job description into the text area.
3. **Adjust Weights**: Use the sliders to set how important each factor is for the job.

4. **Get Results**: The tool will analyze the CVs against the job description and provide match scores and detailed feedback for each CV.

Give it a try to see how well candidates fit your job requirements!
""")

# Fetch the API key from Streamlit's secrets
api_key = st.secrets["GENAI_API_KEY"]


if not api_key:
    st.warning("Please enter your API key to proceed.")

# Job description input
jd = st.text_area("Paste the Job Description")

# Resume files uploader (allow multiple files)
uploaded_files = st.file_uploader("Upload Your Resumes", type=["pdf", "docx"], accept_multiple_files=True, help="Please upload PDF or DOCX files")

# Weights for different criteria
st.sidebar.header("Assign Weights (0-100)")
st.sidebar.write("""
Adjust the weights for different criteria according to your preference. 
The weights determine how much each criterion contributes to the overall matching score.
""")

weights = {
    "title": st.sidebar.slider("Job Title Weight", 0, 100, 20),
    "experience": st.sidebar.slider("Experience Weight", 0, 100, 20),
    "skills": st.sidebar.slider("Skills Weight", 0, 100, 20),
    "education": st.sidebar.slider("Education Weight", 0, 100, 20),
    "certifications": st.sidebar.slider("Certifications Weight", 0, 100, 20),
}

# Submit button
if uploaded_files and api_key:
    submit = st.button("Submit")

    if submit:
        for uploaded_file in uploaded_files:
            # Extract text from the uploaded file
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = extract_text_from_docx(uploaded_file)

            # Create the input prompt
            input_prompt = input_prompt_template.format(
                text=text, 
                jd=jd, 
                weights=json.dumps(weights)
            )

            # Get response from GenAI
            response = get_gemini_response(input_prompt, api_key)

            # Display results for each file
            st.header(uploaded_file.name)
            st.write(f"**Candidate Name**: {response.get('CandidateName', 'N/A')}")
            st.write(f"**Overall Score**: {response.get('OverallScore', 'N/A')}")
            st.write(f"**Experience Score**: {response.get('ExperienceScore', 'N/A')}")
            if 'ExperienceScore' in response and float(response['ExperienceScore'].strip('%')) < 80:
                st.write(f"**Additional Experience Needed**: {response.get('AdditionalExperienceNeeded', 'N/A')}")
            st.write(f"**Skills Score**: {response.get('SkillsScore', 'N/A')}")
            if 'SkillsScore' in response and float(response['SkillsScore'].strip('%')) < 80:
                st.write(f"**Additional Skills Needed**: {response.get('AdditionalSkillsNeeded', 'N/A')}")
            st.write(f"**Education Match**: {response.get('EducationMatch', 'N/A')}")
            if 'EducationMatch' in response and float(response['EducationMatch'].strip('%')) < 80:
                st.write(f"**Additional Education Needed**: {response.get('AdditionalEducationNeeded', 'N/A')}")
            st.write(f"**Certification Match**: {response.get('CertificationMatch', 'N/A')}")
            if 'CertificationMatch' in response and float(response['CertificationMatch'].strip('%')) < 80:
                st.write(f"**Additional Certifications Needed**: {response.get('AdditionalCertificationsNeeded', 'N/A')}")
            st.write(f"**Quantifiable Results Match**: {response.get('QuantifiableResultsMatch', 'N/A')}")
            if 'QuantifiableResultsMatch' in response and float(response['QuantifiableResultsMatch'].strip('%')) < 80:
                st.write(f"**Areas Needing Improvement**: {response.get('AreasNeedingImprovement', 'N/A')}")
else:
    st.write("Please upload PDF or DOCX files.")
