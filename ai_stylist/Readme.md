# AI Stylist

AI Stylist is a Streamlit-based application that leverages the power of Gemini to create personalized style guides based on your preferences. Whether you want to dress like Ryan Gosling or adopt any other style inspiration, AI Stylist generates tailored recommendations to match your desired aesthetic.

## Features

- **Style Guide Generation**: Input your style inspiration (e.g., a celebrity or a specific look), and the app will create a personalized style guide for you.
- **Powered by Gemini**: Uses the Gemini model under the hood for advanced recommendations and insights.
- **Interactive UI**: Built with Streamlit for a seamless and user-friendly experience.

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
4. Create a `.env` file in the root directory and add your Gemini API key:
   ```
   Gemini_API_KEY=your_api_key_here
   ```
    ```

## Usage

1. Launch the app using the command above.
2. Input your style inspiration (e.g., "James Bond").
3. View the generated style guide tailored to your preferences.

## Requirements

- Python 3.8+
- Streamlit
- Gemini (ensure you have access to the Gemini model)
