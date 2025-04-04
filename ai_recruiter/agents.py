import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set up Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class ResumeEvaluationAgent:
    """Agent for evaluating resumes against job descriptions using Gemini."""
    
    def __init__(self):
        # Initialize Gemini model
        self.api_key = GEMINI_API_KEY
        if self.is_configured():
            self.model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')
        else:
            self.model = None
    
    def is_configured(self):
        """Check if the agent has a valid API key configured."""
        return self.api_key is not None and self.api_key.strip() != ""
    
    def evaluate_resume(self, resume_text, job_description):
        """
        Evaluate a resume against a job description.
        
        Args:
            resume_text (str): Text content of the resume
            job_description (str): Job description text
            
        Returns:
            tuple: (score, feedback) where score is a float from 1-10 and feedback is a string
        """
        if not self.is_configured():
            return 0, "Gemini API key not configured. Please set the GEMINI_API_KEY in your .env file."
            
        prompt = f"""
        You are an expert recruiter. You need to evaluate a resume against a job description.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        Rate this resume on a scale of 1 to 10 based on how well it matches the job description.
        Provide detailed feedback on why you gave this score, including strengths and improvement areas.
        
        Your response should be in this exact JSON format:
        {{
            "score": <score as a decimal between 1 and 10>,
            "feedback": "<detailed feedback explaining the score>"
        }}
        """
        
        try:
            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            result = response.text
            
            # Extract JSON part from the response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    rating_data = json.loads(json_str)
                    return rating_data.get("score", 0), rating_data.get("feedback", "No feedback provided")
                except json.JSONDecodeError:
                    return 0, "Error parsing AI response."
            else:
                return 0, "AI response format error."
                
        except Exception as e:
            return 0, f"Error: {str(e)}" 