import streamlit as st
import os
import json
from io import BytesIO
from pdf_to_json import extract_text_from_pdf, get_json_from_gemini
from convert import create_cv_docx

# Configure Streamlit page
st.set_page_config(page_title="CV Converter", layout="centered")

st.title("CV to DOCX Converter")
st.write("Upload a PDF CV, extract data, and convert it to a DOCX format.")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded PDF to a temporary file
    temp_pdf_path = "temp_cv.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("PDF uploaded successfully!")

    # Extract text from PDF
    with st.spinner("Extracting text from PDF..."):
        text_content = extract_text_from_pdf(temp_pdf_path)

    if text_content:
        # Get JSON from Gemini
        with st.spinner("Sending text to Gemini for JSON extraction..."):
            json_data = get_json_from_gemini(text_content)

        if json_data:
            # Convert JSON to DOCX
            with st.spinner("Converting JSON to DOCX..."):
                # create_cv_docx expects a dictionary, not a file path
                # It also saves the DOCX to a file, so we need to read it back
                create_cv_docx(json_data)
                
                # Read the generated DOCX into a BytesIO object for download
                with open("Denisa_CV_from_json.docx", "rb") as f:
                    docx_bytes = BytesIO(f.read())

            st.success("DOCX created successfully!")
            st.download_button(
                label="Download Converted CV (DOCX)",
                data=docx_bytes.getvalue(),
                file_name="converted_cv.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.error("Failed to get JSON data from Gemini. Please check the API key and prompt.")
    else:
        st.error("Failed to extract text from the PDF.")

    # Clean up temporary PDF file
    os.remove(temp_pdf_path)
