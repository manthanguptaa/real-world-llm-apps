# AI Health Advisor Agent

A Streamlit application that analyzes blood marker reports and provides personalized health recommendations.

https://github.com/user-attachments/assets/e7c81a72-49c6-428e-9163-969831b58f64


## Features

- PDF upload for blood marker reports
- AI-powered analysis of blood markers
- Personalized recommendations for diet and exercise
- Download the personalized recommendations as .txt file

## Setup

1. Clone this repository

2. Set up a virtual environment:
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run ai_health_advisor_agent/app.py
   ```
2. Upload your blood marker report in PDF format
3. Wait for the analysis to complete
4. Review the personalized recommendations

## Important Note

This application is for informational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for proper medical guidance.
