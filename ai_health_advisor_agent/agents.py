import openai
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class HealthAdvisor:
    """Agent for analyzing blood marker reports and providing health recommendations."""
    
    def __init__(self):
        self.system_prompt = """You are a knowledgeable and empathetic health advisor who specializes in 
        interpreting blood test results and providing health recommendations in extremely simple language 
        that anyone without medical knowledge can understand."""
    
    def analyze(self, file):
        """
        Analyze blood markers and provide recommendations.
        
        Args:
            file: The uploaded PDF file object
            
        Returns:
            str: Analysis and recommendations
        """
        prompt = """As a compassionate and knowledgeable health advisor, please analyze the blood marker report 
        and provide insights in extremely simple, everyday language. Imagine you're explaining to someone with 
        no medical background. Avoid technical jargon, and when you must use a medical term, explain it immediately.
        
        Focus on:
        1. Identifying any concerning or out-of-range markers
        2. Explaining what these markers mean using simple analogies and everyday examples
        3. Suggesting specific lifestyle changes, including:
           - Recommended physical activities that are easy to understand and implement
           - Common, everyday foods to include or avoid (use familiar food names, not nutrients)
        
        Please structure your response in a friendly, conversational manner as if talking to a friend."""

        try:
            # Read the file data and encode it as base64
            file_data = file.getvalue()
            base64_string = base64.b64encode(file_data).decode("utf-8")
            
            # Use the Chat Completions API with the base64-encoded file
            response = client.responses.create(
                model="gpt-4o",
                input=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "input_file",
                                "filename": file.name,
                                "file_data": f"data:application/pdf;base64,{base64_string}",
                            },
                            {
                                "type": "input_text",
                                "text": prompt,
                            }
                        ]
                    }
                ],
            )
            
            return response.output_text
            
        except Exception as e:
            return f"Error analyzing blood markers: {str(e)}"
