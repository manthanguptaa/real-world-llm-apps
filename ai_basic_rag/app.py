import streamlit as st
from agents import Agent
import os
import io
import PyPDF2
from dotenv import load_dotenv

# Set custom page theme
st.set_page_config(
    page_title="AI Basic RAG Demo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton.secondary button {
        background-color: #f44336;
    }
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    .css-18e3th9 {
        padding: 1rem 5rem 10rem;
    }
    h1, h2, h3 {
        color: #1E88E5;
    }
    .stAlert {
        border-radius: 8px;
    }
    .chat-message-user {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #1976D2;
    }
    .chat-message-ai {
        background-color: #F1F8E9;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #43A047;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Function to chunk text into fixed-size segments
def chunk_text(text, chunk_size=1000, overlap=100):
    """Split text into chunks with overlap."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    end = chunk_size
    
    while start < len(text):
        # If we're not at the beginning, add overlap to start
        if start > 0:
            start = start - overlap
            
        # Find the last period or newline in the chunk
        if end < len(text):
            last_period = text.rfind('.', end - 100, end)
            last_newline = text.rfind('\n', end - 100, end)
            
            # Take the latest of period or newline if found
            if last_period != -1 or last_newline != -1:
                end = max(last_period, last_newline) + 1
        
        # Add the chunk
        chunks.append(text[start:end])
        
        # Set next chunk's points
        start = end
        end = start + chunk_size
        
    return chunks

# Initialize session states
if "agent" not in st.session_state:
    st.session_state.agent = Agent()

if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

agent = st.session_state.agent

# Function to clear chat history
def clear_chat():
    st.session_state.chat_history = []
    
# Function to clear knowledge base
def clear_knowledge():
    try:
        # Drop the Milvus collection
        agent.vector_store.drop()
        # Reinitialize the vector store
        agent.setup_vector_store()
        # Clear PDF processing history
        st.session_state.pdf_processed = {}
        st.success("Knowledge base cleared successfully!")
    except Exception as e:
        st.error(f"Error clearing knowledge base: {str(e)}")

# Sidebar for configuration and knowledge base uploads
with st.sidebar:
    st.sidebar.image("https://i.imgur.com/LKZF9P0.png", width=50)  # Replace with your logo if needed
    st.title("RAG Configuration")
    
    # Two columns for model info
    col1, col2 = st.columns(2)
    with col1:
        st.write("💬 **Model:**")
        st.write("🔍 **Vector DB:**")
    with col2:
        st.write("GPT-4o")
        st.write("Milvus Lite")
    
    st.divider()
    
    # Knowledge Base Management
    st.header("📚 Knowledge Base")
    
    # Controls for knowledge base
    kb_col1, kb_col2 = st.columns(2)
    with kb_col2:
        if st.button("🗑️ Clear Knowledge", key="clear_kb"):
            clear_knowledge()
    
    # Chunking settings
    with st.expander("⚙️ Chunking Settings"):
        chunk_size = st.slider("Chunk Size", 500, 5000, 1000, 
                              help="Set the size of text chunks in characters")
        chunk_overlap = st.slider("Chunk Overlap", 0, 200, 100,
                                 help="Set the overlap between chunks to maintain context")
    
    # Upload PDF file
    st.subheader("Upload PDF")
    pdf_file = st.file_uploader("Choose a PDF file", type=['pdf'], key="pdf_uploader")
    
    # Only process the PDF if it's not already processed
    if pdf_file is not None:
        # Create a unique identifier for this file
        file_id = f"{pdf_file.name}_{pdf_file.size}"
        
        # Check if this file has already been processed
        if file_id not in st.session_state.pdf_processed:
            with st.spinner("Processing PDF..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
                    text = ""
                    
                    # Show progress while extracting text
                    st.write("📄 Extracting text...")
                    pdf_progress = st.progress(0)
                    for i, page in enumerate(pdf_reader.pages):
                        text += pdf_reader.pages[i].extract_text() + "\n\n"
                        pdf_progress.progress((i + 1) / len(pdf_reader.pages))
                    
                    if text:
                        # Check if text is large enough to need chunking
                        if len(text) > chunk_size:
                            st.info(f"📊 PDF text is {len(text)} characters. Splitting into chunks...")
                            
                            # Split text into chunks
                            chunks = chunk_text(text, chunk_size, chunk_overlap)
                            st.info(f"Created {len(chunks)} chunks")
                            
                            # Store each chunk with progress tracking
                            st.write("💾 Storing chunks...")
                            chunk_progress = st.progress(0)
                            stored_ids = []
                            
                            for i, chunk in enumerate(chunks):
                                try:
                                    chunk_id = agent.store_knowledge(chunk)
                                    stored_ids.append(chunk_id)
                                    chunk_progress.progress((i + 1) / len(chunks))
                                except Exception as e:
                                    st.error(f"Error storing chunk {i+1}: {e}")
                                    # Try to reconnect
                                    try:
                                        agent.setup_vector_store()
                                        # Retry this chunk
                                        chunk_id = agent.store_knowledge(chunk)
                                        stored_ids.append(chunk_id)
                                        chunk_progress.progress((i + 1) / len(chunks))
                                    except:
                                        st.error("Failed to reconnect. Some chunks may not be stored.")
                                        break
                            
                            st.success(f"✅ PDF processed and stored in {len(stored_ids)} chunks")
                        else:
                            # Store as a single chunk
                            id = agent.store_knowledge(text)
                            st.success(f"✅ PDF processed and stored with ID: {id}")
                        
                        # Mark this file as processed
                        st.session_state.pdf_processed[file_id] = True
                    else:
                        st.error("Could not extract text from PDF")
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
        else:
            st.success(f"✅ PDF '{pdf_file.name}' already processed")

# Main content area
st.title("🧠 AI Basic RAG Demo")
st.write("Ask questions about your documents using our Retrieval-Augmented Generation system.")

# Chat interface
st.header("💬 Chat with the Agent")

# Display chat history
if st.session_state.chat_history:
    for exchange in st.session_state.chat_history:
        st.markdown(f'<div class="chat-message-user"><strong>You:</strong><br>{exchange["user"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-message-ai"><strong>AI:</strong><br>{exchange["assistant"]}</div>', unsafe_allow_html=True)

# Chat controls
user_input = st.text_area("Your question:", height=80, placeholder="Ask about your uploaded documents...")

# Two columns for the chat buttons
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("Send", key="chat_submit"):
        if user_input:
            # Display user message
            st.markdown(f'<div class="chat-message-user"><strong>You:</strong><br>{user_input}</div>', unsafe_allow_html=True)
            
            with st.spinner("Thinking..."):
                try:
                    response = agent.generate_response(user_input)
                    
                    # Display AI response
                    st.markdown(f'<div class="chat-message-ai"><strong>AI:</strong><br>{response}</div>', unsafe_allow_html=True)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "user": user_input,
                        "assistant": response
                    })
                    
                    # Clear the input box (requires a rerun)
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    # Try to reconnect
                    try:
                        agent.setup_vector_store()
                        st.warning("Reconnected to database. Please try submitting your question again.")
                    except:
                        st.error("Failed to reconnect. Please restart the application.")
        else:
            st.warning("Please enter a question.")

with col2:
    if st.button("Clear Chat", key="clear_chat"):
        clear_chat()
        st.experimental_rerun() 