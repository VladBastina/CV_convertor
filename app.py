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

# Initialize session state for uploaded file if not already present
if "uploaded_file_content" not in st.session_state:
    st.session_state["uploaded_file_content"] = None
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key=f"pdf_uploader_{st.session_state['file_uploader_key']}")

# If a new file is uploaded, update session state
if uploaded_file is not None and st.session_state["uploaded_file_content"] != uploaded_file.getvalue():
    st.session_state["uploaded_file_content"] = uploaded_file.getvalue()
    st.session_state["file_processed"] = False # Reset processing status for new file
    st.rerun() # Rerun to process the new file

# Process the file if it's in session state and not yet processed
if st.session_state["uploaded_file_content"] is not None and not st.session_state.get("file_processed", False):
    # Save the uploaded PDF to a temporary file
    temp_pdf_path = "temp_cv.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(st.session_state["uploaded_file_content"])

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
                create_cv_docx(json_data)
                
                # Read the generated DOCX into a BytesIO object for download
                with open("Denisa_CV_from_json.docx", "rb") as f:
                    docx_bytes = BytesIO(f.read())

            st.success("DOCX created successfully!")
            st.session_state["file_processed"] = True # Mark as processed
            st.download_button(
                label="Download Converted CV (DOCX)",
                data=docx_bytes.getvalue(),
                file_name="converted_cv.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_button"
            )
            # Clean up temporary PDF file immediately after processing
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

        else:
            st.error("Failed to get JSON data from Gemini. Please check the API key and prompt.")
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
    else:
        st.error("Failed to extract text from the PDF.")
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

# After download, clear the uploaded file from session state and reset the uploader
if st.session_state.get("download_button"):
    st.session_state["uploaded_file_content"] = None
    st.session_state["file_processed"] = False
    st.session_state["download_button"] = False # Reset button state
    st.session_state["file_uploader_key"] += 1 # Increment key to reset file uploader
    st.rerun() # Rerun to clear the UI
