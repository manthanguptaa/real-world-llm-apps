import streamlit as st
import pandas as pd
import os
import tempfile
import json
import warnings
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import PyPDF2
import docx2txt
from pathlib import Path
import toml
from dotenv import load_dotenv
from agents import ResumeEvaluationAgent

# Filter out SyntaxWarnings about invalid escape sequences
warnings.filterwarnings("ignore", category=SyntaxWarning, message="invalid escape sequence")

# Load environment variables
load_dotenv()

# Set custom theme and styling
st.set_page_config(
    page_title="AI Recruiter",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/manthangupta26/real-world-llm-apps',
        'Report a bug': 'https://github.com/manthangupta26/real-world-llm-apps/issues',
        'About': 'AI Recruiter - Powered by Gemini AI'
    }
)

# Custom CSS
def local_css():
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            padding-top: 2rem;
            color: #ffffff;
        }
        
        /* Custom title styling */
        .title-container {
            background-color: rgba(30, 58, 138, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .app-title {
            color: #ffffff;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0;
        }
        
        .app-subtitle {
            color: #e2e8f0;
            font-size: 1.2rem;
            font-weight: 400;
        }
        
        /* Section styling */
        .section-container {
            background-color: rgba(30, 58, 138, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .section-title {
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Card styling for results */
        .card {
            background-color: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            color: #ffffff;
        }
        
        .card h4 {
            color: #ffffff;
            margin-top: 0;
        }
        
        .card p {
            color: #e2e8f0;
        }
        
        .card-pass {
            border-left: 5px solid #4CAF50;
        }
        
        .card-fail {
            border-left: 5px solid #F44336;
        }
        
        .card-error {
            border-left: 5px solid #FF9800;
        }
        
        .score-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-weight: 600;
            font-size: 0.9rem;
            color: white;
        }
        
        .badge-pass {
            background-color: #4CAF50;
        }
        
        .badge-fail {
            background-color: #F44336;
        }
        
        .badge-error {
            background-color: #FF9800;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        /* Radio buttons and sliders */
        .stRadio > div {
            padding: 10px;
            border-radius: 5px;
            background-color: rgba(30, 41, 59, 0.7);
            color: #ffffff;
        }
        
        /* Text inputs and areas */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: rgba(30, 41, 59, 0.7);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* File uploader */
        .stFileUploader > div > div {
            padding: 10px;
            border-radius: 5px;
            background-color: rgba(30, 41, 59, 0.7);
            color: #ffffff;
        }
        
        .uploadedFile {
            background-color: rgba(30, 41, 59, 0.7) !important;
            color: #ffffff !important;
        }
        
        /* Processing info */
        .processing-info {
            padding: 1rem;
            border-radius: 5px;
            background-color: rgba(13, 110, 253, 0.2);
            margin-bottom: 1rem;
            border-left: 5px solid #0d6efd;
            color: #ffffff;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            padding: 1rem;
            color: #e2e8f0;
            font-size: 0.9rem;
            margin-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #e2e8f0 !important;
        }
        
        [data-testid="stMetricDelta"] {
            color: #e2e8f0 !important;
        }
        
        /* Info boxes */
        .stAlert {
            background-color: rgba(30, 41, 59, 0.7) !important;
            color: #ffffff !important;
        }
        
        /* Remove Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Make sure all text is visible */
        p, h1, h2, h3, h4, h5, h6, span, label, .stMarkdown, .stText {
            color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
# Initialize styling
local_css()

# Initialize the resume evaluation agent
@st.cache_resource
def get_resume_agent():
    agent = ResumeEvaluationAgent()
    if not agent.is_configured():
        st.error("Gemini API key not found. Please set the GEMINI_API_KEY in your .env file.")
        st.stop()
    return agent

# Function to authenticate with Google Drive
@st.cache_resource
def get_drive_service():
    # First try to get credentials from Streamlit secrets
    try:
        uploaded_json = st.secrets.get("google_credentials", None)
        
        if uploaded_json:
            credentials = Credentials.from_service_account_info(uploaded_json)
            drive_service = build('drive', 'v3', credentials=credentials)
            return drive_service
    except FileNotFoundError:
        # If streamlit can't find secrets.toml in the default locations, try loading it manually
        local_secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
        if os.path.exists(local_secrets_path):
            try:
                secrets_data = toml.load(local_secrets_path)
                if 'google_credentials' in secrets_data:
                    credentials = Credentials.from_service_account_info(secrets_data['google_credentials'])
                    drive_service = build('drive', 'v3', credentials=credentials)
                    return drive_service
            except Exception as e:
                st.error(f"Error loading secrets from {local_secrets_path}: {str(e)}")
    
    # If not found in secrets, try from environment variables
    env_creds = {}
    
    # Check for Google Drive environment variables
    required_keys = [
        "GOOGLE_DRIVE_TYPE", "GOOGLE_DRIVE_PROJECT_ID", "GOOGLE_DRIVE_PRIVATE_KEY_ID",
        "GOOGLE_DRIVE_PRIVATE_KEY", "GOOGLE_DRIVE_CLIENT_EMAIL", "GOOGLE_DRIVE_CLIENT_ID",
        "GOOGLE_DRIVE_AUTH_URI", "GOOGLE_DRIVE_TOKEN_URI", 
        "GOOGLE_DRIVE_AUTH_PROVIDER_CERT_URL", "GOOGLE_DRIVE_CLIENT_CERT_URL"
    ]
    
    # Check if all required environment variables are present
    all_keys_present = all(os.getenv(key) for key in required_keys)
    
    if all_keys_present:
        # Create credentials from environment variables
        env_creds = {
            "type": os.getenv("GOOGLE_DRIVE_TYPE"),
            "project_id": os.getenv("GOOGLE_DRIVE_PROJECT_ID"),
            "private_key_id": os.getenv("GOOGLE_DRIVE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GOOGLE_DRIVE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("GOOGLE_DRIVE_CLIENT_EMAIL"),
            "client_id": os.getenv("GOOGLE_DRIVE_CLIENT_ID"),
            "auth_uri": os.getenv("GOOGLE_DRIVE_AUTH_URI"),
            "token_uri": os.getenv("GOOGLE_DRIVE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_DRIVE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("GOOGLE_DRIVE_CLIENT_CERT_URL")
        }
        
        try:
            credentials = Credentials.from_service_account_info(env_creds)
            drive_service = build('drive', 'v3', credentials=credentials)
            return drive_service
        except Exception as e:
            st.error(f"Error loading Google Drive credentials from environment variables: {str(e)}")
    
    st.error("""
    Google Drive credentials not found. Please either:
    
    1. Set up credentials in Streamlit secrets (.streamlit/secrets.toml)
    2. Or provide credentials in your .env file
    
    See the README.md for detailed instructions.
    """)
    return None

# Function to extract text from a PDF file
def extract_text_from_pdf(file_obj):
    pdf_reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Function to extract text from a DOCX file
def extract_text_from_docx(file_obj):
    return docx2txt.process(file_obj)

# Function to extract text from uploaded files
def extract_text_from_file(file_obj, file_extension=None):
    # If file_extension is not provided, try to get it from the file object
    if file_extension is None:
        try:
            file_extension = Path(file_obj.name).suffix.lower()
        except AttributeError:
            # If file_obj doesn't have a name attribute (like BytesIO), the extension must be provided
            st.error("Could not determine file type. Please provide file extension.")
            return None
    else:
        # Ensure the extension starts with a dot
        if not file_extension.startswith('.'):
            file_extension = '.' + file_extension
        file_extension = file_extension.lower()
    
    if file_extension == ".pdf":
        return extract_text_from_pdf(file_obj)
    elif file_extension == ".docx":
        return extract_text_from_docx(file_obj)
    elif file_extension == ".txt":
        return file_obj.read().decode('utf-8')
    else:
        return None

# Function to download file from Google Drive
def download_file_from_drive(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_content.seek(0)
    return file_content

# Function to list files in a Google Drive folder
def list_files_in_folder(drive_service, folder_id):
    results = []
    page_token = None
    
    while True:
        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        
        for file in response.get('files', []):
            results.append(file)
        
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
            
    return results

# Function to extract file ID from Google Drive link
def extract_file_id(drive_link):
    if "drive.google.com" in drive_link:
        if "/file/d/" in drive_link:
            # Format: https://drive.google.com/file/d/FILE_ID/view
            file_id = drive_link.split("/file/d/")[1].split("/")[0]
        elif "id=" in drive_link:
            # Format: https://drive.google.com/open?id=FILE_ID
            file_id = drive_link.split("id=")[1].split("&")[0]
        elif "/folders/" in drive_link:
            # Format: https://drive.google.com/drive/folders/FOLDER_ID
            file_id = drive_link.split("/folders/")[1].split("?")[0].split("/")[0]
        else:
            return None
        return file_id
    return None

# Main app
def main():
    # Custom title
    st.markdown(
        """
        <div class="title-container">
            <h1 class="app-title">AI Recruiter 📝</h1>
            <p class="app-subtitle">Smart resume filtering powered by AI</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Initialize the resume evaluation agent
    resume_agent = get_resume_agent()
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Job Description Section
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Job Description</h2>', unsafe_allow_html=True)
        job_description = st.text_area(
            "Enter the job description here:",
            height=300,
            placeholder="Paste the job description here. The more detailed the description, the better the evaluation."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Evaluation Settings Section
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Evaluation Settings</h2>', unsafe_allow_html=True)
        score_threshold = st.slider(
            "Minimum score to pass (out of 10):",
            min_value=1.0,
            max_value=10.0,
            value=7.5,
            step=0.1,
            help="Resumes with scores above this threshold will be marked as 'Passed'"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        # Resume Input Section
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Resume Input</h2>', unsafe_allow_html=True)
        
        input_method = st.radio(
            "Choose how to upload resumes:",
            ("Upload files directly", "Google Drive link"),
            horizontal=True
        )
        
        if input_method == "Upload files directly":
            uploaded_files = st.file_uploader(
                "Upload resume files (PDF, DOCX, TXT)",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help="You can select multiple files at once"
            )
            
            if uploaded_files:
                st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")
        
        else:  # Google Drive link
            drive_link = st.text_input(
                "Enter Google Drive link (file or folder):",
                placeholder="https://drive.google.com/file/d/... or https://drive.google.com/drive/folders/..."
            )
            
            if drive_link:
                file_id = extract_file_id(drive_link)
                if file_id:
                    st.success("Valid Google Drive link!")
                else:
                    st.warning("Invalid Google Drive link format. Please check and try again.")
        
        # Evaluate button
        evaluate_button = st.button("Evaluate Resumes", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Process resumes when button is clicked
    if evaluate_button and job_description:
        with st.spinner("Initializing evaluation process..."):
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h2 class="section-title">Evaluation Process</h2>', unsafe_allow_html=True)
            
            if input_method == "Upload files directly":
                if not uploaded_files:
                    st.warning("Please upload at least one resume file.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
                
                results = []
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                for i, file in enumerate(uploaded_files):
                    progress_text.markdown(f'<div class="processing-info">Processing: {file.name} ({i+1}/{len(uploaded_files)})</div>', unsafe_allow_html=True)
                    resume_text = extract_text_from_file(file)
                    
                    if resume_text:
                        with st.spinner(f"AI is evaluating {file.name}..."):
                            score, feedback = resume_agent.evaluate_resume(resume_text, job_description)
                            
                            results.append({
                                "Resume": file.name,
                                "Score": score,
                                "Feedback": feedback,
                                "Status": "Pass" if score >= score_threshold else "Fail"
                            })
                    else:
                        results.append({
                            "Resume": file.name,
                            "Score": 0,
                            "Feedback": "Could not extract text from file.",
                            "Status": "Error"
                        })
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                progress_text.empty()
                display_results(results)
            
            else:  # Google Drive link
                if not drive_link:
                    st.warning("Please provide a Google Drive link.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
                
                drive_service = get_drive_service()
                
                if not drive_service:
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
                
                file_id = extract_file_id(drive_link)
                
                if not file_id:
                    st.error("Invalid Google Drive link. Please provide a valid link.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
                
                # Check if it's a folder or a file
                try:
                    file_metadata = drive_service.files().get(fileId=file_id, fields='mimeType').execute()
                    
                    if file_metadata['mimeType'] == 'application/vnd.google-apps.folder':
                        # Process folder
                        st.info("Processing folder from Google Drive...")
                        files = list_files_in_folder(drive_service, file_id)
                        
                        if not files:
                            st.warning("No files found in the specified folder.")
                            st.markdown('</div>', unsafe_allow_html=True)
                            return
                        
                        results = []
                        progress_text = st.empty()
                        progress_bar = st.progress(0)
                        
                        supported_mime_types = [
                            'application/pdf', 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                            'text/plain'
                        ]
                        
                        # Filter to only supported file types
                        valid_files = [f for f in files if f['mimeType'] in supported_mime_types]
                        
                        if not valid_files:
                            st.warning("No supported files found in the folder. Please ensure your folder contains PDF, DOCX, or TXT files.")
                            st.markdown('</div>', unsafe_allow_html=True)
                            return
                            
                        for i, file in enumerate(valid_files):
                            progress_text.markdown(f'<div class="processing-info">Processing: {file["name"]} ({i+1}/{len(valid_files)})</div>', unsafe_allow_html=True)
                            
                            file_content = download_file_from_drive(drive_service, file['id'])
                            
                            with tempfile.NamedTemporaryFile(suffix=Path(file['name']).suffix, delete=False) as temp_file:
                                temp_file.write(file_content.getvalue())
                                temp_path = temp_file.name
                            
                            with open(temp_path, 'rb') as f:
                                file_ext = Path(file['name']).suffix
                                resume_text = extract_text_from_file(io.BytesIO(f.read()), file_ext)
                            
                            os.unlink(temp_path)
                            
                            if resume_text:
                                with st.spinner(f"AI is evaluating {file['name']}..."):
                                    score, feedback = resume_agent.evaluate_resume(resume_text, job_description)
                                    
                                    results.append({
                                        "Resume": file['name'],
                                        "Score": score,
                                        "Feedback": feedback,
                                        "Status": "Pass" if score >= score_threshold else "Fail"
                                    })
                            else:
                                results.append({
                                    "Resume": file['name'],
                                    "Score": 0,
                                    "Feedback": "Could not extract text from file.",
                                    "Status": "Error"
                                })
                            
                            progress_bar.progress((i + 1) / len(valid_files))
                        
                        progress_text.empty()
                        display_results(results)
                    else:
                        # Process single file
                        st.info("Processing single file from Google Drive...")
                        file_metadata = drive_service.files().get(fileId=file_id, fields='name').execute()
                        file_name = file_metadata['name']
                        
                        file_content = download_file_from_drive(drive_service, file_id)
                        
                        with tempfile.NamedTemporaryFile(suffix=Path(file_name).suffix, delete=False) as temp_file:
                            temp_file.write(file_content.getvalue())
                            temp_path = temp_file.name
                        
                        with open(temp_path, 'rb') as f:
                            file_ext = Path(file_name).suffix
                            resume_text = extract_text_from_file(io.BytesIO(f.read()), file_ext)
                        
                        os.unlink(temp_path)
                        
                        if resume_text:
                            with st.spinner(f"AI is evaluating {file_name}..."):
                                score, feedback = resume_agent.evaluate_resume(resume_text, job_description)
                                
                                results = [{
                                    "Resume": file_name,
                                    "Score": score,
                                    "Feedback": feedback,
                                    "Status": "Pass" if score >= score_threshold else "Fail"
                                }]
                                
                                display_results(results)
                        else:
                            st.error(f"Could not extract text from {file_name}.")
                
                except Exception as e:
                    st.error(f"Error processing Google Drive: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(
        """
        <div class="footer">
            <p>AI Recruiter | Powered by Gemini AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Function to display results
def display_results(results):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">Evaluation Results</h2>', unsafe_allow_html=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Calculate statistics
    total = len(df)
    passed = len(df[df["Status"] == "Pass"])
    failed = len(df[df["Status"] == "Fail"])
    error = len(df[df["Status"] == "Error"])
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Resumes", total)
    with col2:
        st.metric("Passed", passed, f"{passed/total*100:.1f}%" if total > 0 else "0%")
    with col3:
        st.metric("Failed", failed, f"{failed/total*100:.1f}%" if total > 0 else "0%")
    with col4:
        st.metric("Errors", error, f"{error/total*100:.1f}%" if total > 0 else "0%")
    
    # Display passed resumes
    st.markdown('<h3 style="color: #4CAF50; margin-top: 20px;">Passed Resumes</h3>', unsafe_allow_html=True)
    passed_df = df[df["Status"] == "Pass"].sort_values(by="Score", ascending=False).reset_index(drop=True)
    
    if not passed_df.empty:
        for _, row in passed_df.iterrows():
            st.markdown(
                f"""
                <div class="card card-pass">
                    <h4>{row['Resume']}</h4>
                    <p><span class="score-badge badge-pass">Score: {row['Score']:.1f}/10</span></p>
                    <p><strong>Feedback:</strong> {row['Feedback']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("No resumes passed the evaluation.")
    
    # Display failed resumes
    st.markdown('<h3 style="color: #F44336; margin-top: 20px;">Failed Resumes</h3>', unsafe_allow_html=True)
    failed_df = df[df["Status"] == "Fail"].sort_values(by="Score", ascending=False).reset_index(drop=True)
    
    if not failed_df.empty:
        for _, row in failed_df.iterrows():
            st.markdown(
                f"""
                <div class="card card-fail">
                    <h4>{row['Resume']}</h4>
                    <p><span class="score-badge badge-fail">Score: {row['Score']:.1f}/10</span></p>
                    <p><strong>Feedback:</strong> {row['Feedback']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("No resumes failed the evaluation.")
    
    # Display error resumes
    error_df = df[df["Status"] == "Error"].reset_index(drop=True)
    if not error_df.empty:
        st.markdown('<h3 style="color: #FF9800; margin-top: 20px;">Resumes with Errors</h3>', unsafe_allow_html=True)
        for _, row in error_df.iterrows():
            st.markdown(
                f"""
                <div class="card card-error">
                    <h4>{row['Resume']}</h4>
                    <p><span class="score-badge badge-error">Error</span></p>
                    <p><strong>Message:</strong> {row['Feedback']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Download results as CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name="resume_evaluation_results.csv",
        mime="text/csv"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 