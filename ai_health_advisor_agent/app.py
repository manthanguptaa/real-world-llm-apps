import streamlit as st
from agents import HealthAdvisor
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def main():
    # Set page configuration
    st.set_page_config(
        page_title="AI Health Advisor",
        page_icon="❤️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B4BFF;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #FF4B4B;
    }
    .result-box {
        background-color: #e6f7ff;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        border-left: 5px solid #4B4BFF;
    }
    .disclaimer {
        font-size: 0.8rem;
        color: #666;
        text-align: center;
        margin-top: 2rem;
        padding: 10px;
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3rem;
        font-size: 1.1rem;
        background-color: #FF4B4B;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">❤️ AI Health Advisor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your personal health insights from blood marker reports</p>', unsafe_allow_html=True)
    
    # Sidebar with information
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/health-book.png", width=100)
        st.markdown("### About This App")
        st.markdown("""
        This application analyzes your blood marker reports and provides personalized health recommendations.
        
        **How it works:**
        1. Upload your blood test report (PDF format)
        2. Our AI analyzes the markers
        3. Receive easy-to-understand insights
        4. Get personalized recommendations
        """)
        
        st.markdown("### Tips for Best Results")
        st.markdown("""
        - Ensure your PDF is clear and readable
        - Reports should include reference ranges
        - For privacy, remove personal identifiers
        """)
        
        st.markdown("### Need Help?")
        st.markdown("""
        If you encounter any issues or have questions, please contact support.
        """)
    
    # Main content
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    ### Welcome to Your Personal Health Analysis!
    
    Upload your blood test report below, and I'll help you understand your results in simple, everyday language.
    You'll receive personalized recommendations for improving your health through diet and exercise.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Check if API key is configured
    if not os.getenv("OPENAI_API_KEY"):
        st.error("""
        ⚠️ **Configuration Error**: OpenAI API Key is not set.
        
        Please add your OpenAI API key to your .env file:
        ```
        OPENAI_API_KEY=your_api_key_here
        ```
        """)
        return
    
    # File upload with custom styling
    st.markdown("### 📄 Upload Your Blood Marker Report")
    uploaded_file = st.file_uploader(
        label="Blood Marker Report", 
        type=['pdf'], 
        help="Upload your blood test report in PDF format",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Show file details
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB",
            "File type": uploaded_file.type
        }
        st.write("### 📋 File Details")
        for key, value in file_details.items():
            st.write(f"**{key}:** {value}")
        
        # Analysis button
        if st.button("🔍 Analyze My Blood Report"):
            with st.spinner("Analyzing your blood marker report... This may take a minute."):
                # Initialize and use the HealthAdvisor
                advisor = HealthAdvisor()
                analysis = advisor.analyze(uploaded_file)
                
                # Display results with animation
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.markdown("### 📊 Analysis Results")
                
                # Animate the text appearance
                for line in analysis.split('\n'):
                    st.markdown(line)
                    time.sleep(0.1)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download button for the analysis
                st.download_button(
                    label="📥 Download Analysis",
                    data=analysis,
                    file_name="health_advisor_analysis.txt",
                    mime="text/plain"
                )
    
    # Footer with disclaimer
    st.markdown('<div class="disclaimer">', unsafe_allow_html=True)
    st.markdown("""
    ⚠️ **Important Note**: This analysis is for informational purposes only and should not replace 
    professional medical advice. Please consult with your healthcare provider for proper medical guidance.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
