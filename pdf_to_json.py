import google.generativeai as genai
import pypdf
import json
import os
from docx import Document # Import python-docx
import streamlit as st


# Configure the Gemini API key
# Replace 'YOUR_API_KEY' with your actual Gemini API key
# It's recommended to load this from an environment variable for security
# genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY) # Placeholder for API key

def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a PDF file.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(docx_path):
    """
    Extracts text content from a DOCX file.
    """
    text = ""
    try:
        document = Document(docx_path)
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def get_json_from_gemini(text_content):
    """
    Sends text content to the Gemini model and requests JSON output.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = """
    You are an expert CV (Curriculum Vitae) parser. Your task is to read a raw CV provided as text and extract its key information into a structured JSON format. Your output must be a single, valid JSON object and nothing else. Do not include any conversational text, explanations, or markdown outside of the JSON object itself.

    ### **JSON Schema and Rules**

    You must follow this exact JSON structure:

    **1. Top-Level Object:**
    The root object must contain the following keys:
    -   "name": (string) The full name of the candidate, anonymized to "Firstname L.". For example, "Denisa Zega" becomes "Denisa Z.".
    -   "role": (string) The primary job title or role of the candidate.
    -   "about": (string) The professional summary or "About Me" section.
    -   "sections": (array) An array of objects, where each object represents a section of the CV (e.g., Skills, Experience, Education).

    **2. Section Object Structure:**
    Each object inside the "sections" array must have:
    -   "title": (string) The uppercase heading of the section (e.g., "TECHNICAL SKILLS", "WORK EXPERIENCE").
    -   "type": (string) A specific type identifier that determines the structure of the section's content. The valid types are: "bullets", "experience", "text", and "list".

    **3. Content Structure by Section `type`:**

    #### `type: "experience"`
    Used for "Work Experience" or "Employment History".
    -   It must contain a "positions" key, which is an array of job objects.
    -   Each job object has:
        -   "role": (string) The job title.
        -   "dates": (string) The employment period (e.g., "01/2025 - Present").
        -   "details": (array of strings) A list of responsibilities and achievements, corresponding to the bullet points for that role.
        -   "technologies": (optional string) A single, comma-separated string of technologies, tools, or frameworks mentioned **within the `details` for that specific job**.

    #### `type: "bullets"`
    Used for categorized skills like "Technical Skills".
    -   It must contain an "items" key, which is an array of skill category objects.
    -   Each object has:
        -   "label": (string) The category name (e.g., "Backend", "Frontend").
        -   "value": (string) A comma-separated list of skills for that category.

    #### `type: "text"`
    Used for sections like "Education" or "Languages" where there is a main title and an optional subtitle.
    -   It must contain an "items" key, which is an array of entry objects.
    -   Each object has:
        -   "value": (string) The main line of text (e.g., "Business Computer Science - FSEGA...").
        -   "sub": (optional string) A secondary line for details (e.g., "Bachelor's Degree | 2016 - 2019").

    #### `type: "list"`
    Used for simple, non-categorized lists like "Certifications" or "Projects".
    -   It must contain an "items" key, which is an array of strings. Each string is one bullet point from the list.

    ### **Processing Instructions**

    -   **Section Mapping:** Map common CV headings to the correct `type`. For example, "Skills" -> "bullets"; "Experience" -> "experience"; "Education" -> "text"; "Certifications" -> "list".
    -   **Technology Extraction:** For each work experience entry, identify any technologies, programming languages, or specific tools mentioned within the description/bullet points. Extract these into the `technologies` field as a comma-separated string. **Crucially, do not remove the technology names from the original `details` text.**
    -   **Data Integrity:** Preserve all text from the CV. Do not summarize or omit details.
    -   **Inference:** If a section is not clearly labeled, infer its purpose from the content and structure it correctly.

    ---

    ### **Example**

    **Input CV:**
    ```text
    Denisa Zega
    Power Platform Developer

    About Me
    I’m an experienced Power Platform Developer specializing in building both canvas and model-driven Power Apps. My expertise lies in creating end-to-end solutions that streamline business processes and enhance operational efficiency. I am proficient in Power Automate for workflow automation and have a strong background in integrating various data sources, including Dataverse and SharePoint.

    Technical Skills
    -   Backend: Power Apps, Power Automate, Power Automate Desktop, UiPath
    -   Frontend: Javascript, HTML/CSS
    -   Storage: Dataverse, Sharepoint, SQL
    -   Methodologies: Agile, Scrum, Kanban

    Work Experience

    RPA Developer, Power Platform Developer
    01/2025 - Present
    - Designing, developing, and deploying end-to-end business applications for various clients.
    - Integrated AI Builder to automate document processing, reducing manual effort by 40%.
    - Managed client relationships and project coordination to ensure timely delivery of solutions.

    RPA Developer, Power Platform Developer
    01/2020 - 12/2024
    - Led numerous Power Apps and Power Automate solutions from conception to deployment.
    - Acted as a liaison between technical teams and stakeholders to gather requirements and provide updates.
    - Maintained a strong focus on quality and efficiency, performing rigorous testing and debugging.

    Education
    Business Computer Science - FSEGA, Babes - Bolyai University
    Bachelor's Degree | 2016 - 2019

    Certifications
    - UiPath Certified Professional
    - PL-900 Microsoft Certified: Power Platform Fundamentals
    - PL-100 Microsoft Certified: Power Platform App Maker

    Languages
    - Romanian — Native
    - English — Professional
    ```

    **Required JSON Output:**
    ```json
    {
    "name": "Denisa Z.",
    "role": "Power Platform Developer",
    "about": "I’m an experienced Power Platform Developer specializing in building both canvas and model-driven Power Apps. My expertise lies in creating end-to-end solutions that streamline business processes and enhance operational efficiency. I am proficient in Power Automate for workflow automation and have a strong background in integrating various data sources, including Dataverse and SharePoint.",
    "sections": [
        {
        "title": "TECHNICAL SKILLS",
        "type": "bullets",
        "items": [
            { "label": "Backend", "value": "Power Apps, Power Automate, Power Automate Desktop, UiPath" },
            { "label": "Frontend", "value": "Javascript, HTML/CSS" },
            { "label": "Storage", "value": "Dataverse, Sharepoint, SQL" },
            { "label": "Methodologies", "value": "Agile, Scrum, Kanban" }
        ]
        },
        {
        "title": "WORK EXPERIENCE",
        "type": "experience",
        "positions": [
            {
            "role": "RPA Developer, Power Platform Developer",
            "dates": "01/2025 - Present",
            "details": [
                "Designing, developing, and deploying end-to-end business applications for various clients.",
                "Integrated AI Builder to automate document processing, reducing manual effort by 40%.",
                "Managed client relationships and project coordination to ensure timely delivery of solutions."
            ],
            "technologies": "AI Builder"
            },
            {
            "role": "RPA Developer, Power Platform Developer",
            "dates": "01/2020 - 12/2024",
            "details": [
                "Led numerous Power Apps and Power Automate solutions from conception to deployment.",
                "Acted as a liaison between technical teams and stakeholders to gather requirements and provide updates.",
                "Maintained a strong focus on quality and efficiency, performing rigorous testing and debugging."
            ],
            "technologies": "Power Apps, Power Automate"
            }
        ]
        },
        {
        "title": "EDUCATION",
        "type": "text",
        "items": [
            {
            "value": "Business Computer Science - FSEGA, Babes - Bolyai University",
            "sub": "Bachelor's Degree | 2016 - 2019"
            }
        ]
        },
        {
        "title": "CERTIFICATIONS",
        "type": "list",
        "items": [
            "UiPath Certified Professional",
            "PL-900 Microsoft Certified: Power Platform Fundamentals",
            "PL-100 Microsoft Certified: Power Platform App Maker"
        ]
        },
        {
        "title": "LANGUAGES",
        "type": "text",
        "items": [
            { "value": "Romanian — Native" },
            { "value": "English — Professional" }
        ]
        }
    ]
    }
    ```

    ---

    Now, process the following CV and generate the JSON output.

    Text:
    """
    prompt += text_content

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0)
        )

        # Extract JSON string from markdown code block
        import re
        json_match = re.search(r"```json\n(.*)\n```", response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
            return json.loads(json_string)
        else:
            print("No JSON markdown block found in Gemini response.")
            return None
    except Exception as e:
        print(f"Error calling Gemini API or parsing response: {e}")
        return None
