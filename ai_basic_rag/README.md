# AI Basic RAG Demo

This is a Streamlit application that showcases a basic RAG (Retrieval-Augmented Generation) system using OpenAI's language models and Milvus Lite vector database.

## Features

- Interactive chat interface with the AI agent
- Knowledge base management with PDF upload
- Fixed-size chunking for large documents
- Beautiful and intuitive UI
- Local file-based vector storage with Milvus Lite

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

3. Create a `.env` file from the example:
```bash
cp .env.example .env
# Edit the .env file to add your OpenAI API key
```

4. Start the Streamlit application:
```bash
cd ai_basic_rag
streamlit run app.py
```

## Project Structure

- `app.py`: Streamlit application
- `agents.py`: Agent implementation
- `vector_store.py`: Milvus vector store integration
- `requirements.txt`: Project dependencies
- `.env`: Environment configuration (create from .env.example)
- `tmp/milvus.db`: File-based Milvus Lite storage

## Application Features

### Knowledge Base Management
- Upload PDFs to the knowledge base
- Automatic chunking for large documents
- Progress tracking for uploads
- Clear knowledge base functionality

### Chat Interface
- Interactive chat with the AI assistant
- Real-time responses using RAG
- Context-aware conversations
- Clear chat history functionality

## Vector Database

The application uses Milvus Lite, a file-based version of Milvus that:
- Doesn't require running a separate Milvus server
- Stores all vector data in a local file
- Is perfect for prototyping and small to medium-sized applications
- Can be easily upgraded to a full Milvus server for production

## What is Basic RAG?

Basic RAG (Retrieval-Augmented Generation) enhances Large Language Models by:
1. Retrieving relevant information from a knowledge base
2. Providing that information as context to the model
3. Generating responses based on both the user's query and the retrieved context

Unlike agentic RAG, this system doesn't have autonomous tool-calling capabilities.

## License

MIT License 