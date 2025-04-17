# AI Study Assistant 📚

A powerful AI-powered study assistant that helps students learn more effectively by leveraging their study materials.

## Features

- **Interactive Chat**: Ask questions about your study materials and get accurate, contextual answers
- **Concept Explorer**: Get detailed explanations of complex concepts from your materials
- **Flashcard Generator**: Create study flashcards automatically from your materials
- **Quiz Generator**: Test your knowledge with AI-generated quizzes
- **Summarizer**: Generate concise summaries of lengthy study materials
- **Knowledge Base Management**: Upload and manage your study materials (PDFs)

## Technical Features

- Built with Streamlit for a beautiful, responsive UI
- Uses OpenAI's GPT-4o for natural language understanding and generation
- Implements RAG (Retrieval-Augmented Generation) with Milvus Lite vector database
- Processes and chunks PDF documents for efficient storage and retrieval
- Local file-based vector storage for privacy and performance

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the Streamlit application:

```bash
cd ai_study_assistant
streamlit run app.py
```

4. Enter your OpenAI API key when prompted:
   - The application will ask for your OpenAI API key on first run
   - The key will be saved to a `.env` file for future use
   - You can get an API key from https://platform.openai.com/api-keys

## Project Structure

- `app.py`: Streamlit application with the user interface
- `agents.py`: Study assistant agent implementation
- `vector_store.py`: Vector database for storing study materials
- `requirements.txt`: Project dependencies
- `.env`: Environment configuration (created automatically when you enter your API key)

## How to Use

1. **Enter Your OpenAI API Key**: When you first run the application, you'll be prompted to enter your OpenAI API key
2. **Upload Study Materials**: Use the sidebar to upload PDF documents containing your study materials
3. **Chat with the Assistant**: Ask questions about your materials and get AI-powered answers
4. **Explore Concepts**: Get detailed explanations of specific concepts from your materials
5. **Generate Flashcards**: Create study flashcards on any topic covered in your materials
6. **Take Quizzes**: Test your knowledge with automatically generated quizzes
7. **Summarize Text**: Generate concise summaries of lengthy study materials

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for API access

## Troubleshooting

- **Vector Database Connection Issues**: If you encounter errors related to the vector database, try refreshing the page or restarting the application
- **API Key Issues**: Make sure your OpenAI API key is valid and has sufficient credits
- **PDF Processing Errors**: Some PDFs may not be processed correctly if they contain complex formatting or are scanned documents

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for providing the GPT-4o API
- Milvus for the vector database technology
- Streamlit for the web application framework
