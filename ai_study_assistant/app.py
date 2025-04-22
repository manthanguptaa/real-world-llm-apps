import io
import os
import time

import PyPDF2
import streamlit as st
from dotenv import load_dotenv

from agents import StudyAssistant

# Set basic page config
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Function to save API key to .env file
def save_api_key(api_key):
    with open(".env", "w") as f:
        f.write(f"OPENAI_API_KEY={api_key}\n")


# Initialize session state for API key popup
if "api_key_submitted" not in st.session_state:
    st.session_state.api_key_submitted = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Check for OpenAI API key in environment
if not st.session_state.api_key_submitted and "OPENAI_API_KEY" not in os.environ:
    with st.form("api_key_form", clear_on_submit=False):
        st.header("Welcome to AI Study Assistant")
        st.write("Please enter your OpenAI API key to continue")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="Enter your API key here",
            help="Get your API key from https://platform.openai.com/api-keys",
        )
        submitted = st.form_submit_button("Submit")

        if submitted and api_key:
            # Save the API key
            st.session_state.api_key = api_key
            st.session_state.api_key_submitted = True
            save_api_key(api_key)
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("API key saved successfully! Loading the application...")
            time.sleep(2)
            st.rerun()
        elif submitted and not api_key:
            st.error("Please enter a valid API key")

    st.write("### Why do I need an API key?")
    st.write(
        "The AI Study Assistant uses OpenAI's language models to provide intelligent study assistance. You need to provide your own API key to use these services."
    )
    st.write("### How to get an API key?")
    st.write("1. Go to [OpenAI's API Keys page](https://platform.openai.com/api-keys)")
    st.write("2. Sign up or log in to your OpenAI account")
    st.write("3. Create a new API key")
    st.write("4. Copy and paste the key here")
    st.write(
        "**Note:** Your API key is stored locally and used only for OpenAI services."
    )

    st.stop()  # Block interaction until API key is provided

# Load environment variables
load_dotenv()


# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n\n"
    return text


# Function to chunk text into smaller pieces
def chunk_text(text, chunk_size=1000, overlap=100):
    if not text:
        return []
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            for char in ["\n\n", ".", "?", "!"]:
                pos = text.rfind(char, start, end)
                if pos != -1:
                    end = pos + 1
                    break
        chunks.append(text[start:end])
        start = end - overlap if end - overlap > start else end
    return chunks


# Initialize session states
if "assistant" not in st.session_state:
    st.session_state.assistant = StudyAssistant()
if "materials_processed" not in st.session_state:
    st.session_state.materials_processed = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "chat"
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

assistant = st.session_state.assistant


# Function to clear chat history
def clear_chat():
    st.session_state.chat_history = []


# Function to clear study materials
def clear_materials():
    try:
        assistant.vector_store.drop()
        assistant.setup_vector_store()
        st.session_state.materials_processed = {}
        st.success("Study materials cleared successfully!")
    except Exception as e:
        st.error(f"Error clearing study materials: {str(e)}")


# Sidebar
with st.sidebar:
    st.image(
        "https://media.licdn.com/dms/image/v2/C5612AQFjOmJ_0UmzIQ/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1635826425447?e=2147483647&v=beta&t=JtdnhvzjN_5dVKkR6toDC1VEng56AVwtwAGQCu3pRYI",
        width=50,
    )
    st.header("AI Study Assistant")
    st.write("Your personal AI tutor")

    col1, col2 = st.columns(2)
    with col1:
        st.write("💬 **Model:**")
        st.write("🔍 **Vector DB:**")
    with col2:
        st.write("GPT-4o")
        st.write("Milvus Lite")

    st.divider()

    st.subheader("📚 Study Materials")
    kb_col1, kb_col2 = st.columns(2)
    with kb_col2:
        if st.button("🗑️ Clear Materials", key="clear_materials"):
            clear_materials()

    uploaded_files = st.file_uploader(
        "Upload study materials (PDF)", type=["pdf"], accept_multiple_files=True
    )

    if uploaded_files:
        for pdf_file in uploaded_files:
            file_id = f"{pdf_file.name}_{pdf_file.size}"
            if file_id not in st.session_state.materials_processed:
                with st.spinner("Processing study material..."):
                    try:
                        text = extract_text_from_pdf(pdf_file)
                        chunks = chunk_text(text)
                        chunk_progress = st.progress(0)
                        for i, chunk in enumerate(chunks):
                            metadata = {
                                "source": pdf_file.name,
                                "chunk": i,
                                "total_chunks": len(chunks),
                            }
                            assistant.store_material(chunk, metadata)
                            chunk_progress.progress((i + 1) / len(chunks))
                        st.session_state.materials_processed[file_id] = {
                            "name": pdf_file.name,
                            "chunks": len(chunks),
                        }
                        st.success(
                            f"Processed {pdf_file.name} into {len(chunks)} chunks!"
                        )
                    except Exception as e:
                        st.error(f"Error processing {pdf_file.name}: {str(e)}")
            else:
                processed = st.session_state.materials_processed[file_id]
                st.info(
                    f"Already processed {processed['name']} ({processed['chunks']} chunks)"
                )

    st.divider()
    st.subheader("🧭 Navigation")
    if st.button("💬 Chat", key="nav_chat"):
        st.session_state.current_tab = "chat"
        st.rerun()
    if st.button("🔍 Concept Explorer", key="nav_concepts"):
        st.session_state.current_tab = "concepts"
        st.rerun()
    if st.button("🎴 Flashcards", key="nav_flashcards"):
        st.session_state.current_tab = "flashcards"
        st.rerun()
    if st.button("📝 Quiz Generator", key="nav_quiz"):
        st.session_state.current_tab = "quiz"
        st.rerun()
    if st.button("📊 Summarizer", key="nav_summarizer"):
        st.session_state.current_tab = "summarizer"
        st.rerun()

# Main content
if st.session_state.current_tab == "chat":
    st.header("💬 Chat with Your Study Assistant")
    st.write("Ask questions about your study materials")

    if st.session_state.chat_history:
        for exchange in st.session_state.chat_history:
            st.write(f"**You:** {exchange['user']}")
            st.write(f"**AI:** {exchange['assistant']}")

    user_input = st.text_area(
        "Your question:", height=80, placeholder="Ask about your study materials..."
    )
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Send", key="chat_submit"):
            if user_input:
                st.write(f"**You:** {user_input}")
                with st.spinner("Thinking..."):
                    try:
                        response = assistant.generate_response(user_input)
                        st.write(f"**AI:** {response}")
                        st.session_state.chat_history.append(
                            {"user": user_input, "assistant": response}
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating response: {str(e)}")
            else:
                st.warning("Please enter a question.")
    with col2:
        if st.button("Clear Chat", key="clear_chat"):
            clear_chat()
            st.rerun()

elif st.session_state.current_tab == "concepts":
    st.header("🔍 Concept Explorer")
    st.write("Get detailed explanations of concepts")
    concept = st.text_input("Enter a concept:", placeholder="e.g., Photosynthesis...")
    if st.button("Explain Concept", key="explain_concept"):
        if concept:
            with st.spinner(f"Generating explanation for {concept}..."):
                try:
                    explanation = assistant.explain_concept(concept)
                    st.write(f"### {concept}")
                    st.write(explanation)
                except Exception as e:
                    st.error(f"Error explaining concept: {str(e)}")
        else:
            st.warning("Please enter a concept.")

elif st.session_state.current_tab == "flashcards":
    st.header("🎴 Flashcards")
    st.write("Generate flashcards to test your knowledge")
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Enter a topic:", placeholder="e.g., Cell Biology...")
    with col2:
        num_cards = st.number_input(
            "Number of cards:", min_value=1, max_value=20, value=5
        )
    if st.button("Generate Flashcards", key="gen_flashcards"):
        if topic:
            with st.spinner(f"Generating {num_cards} flashcards..."):
                try:
                    flashcards = assistant.generate_flashcards(topic, num_cards)
                    st.session_state.flashcards = flashcards
                except Exception as e:
                    st.error(f"Error generating flashcards: {str(e)}")
        else:
            st.warning("Please enter a topic.")
    if st.session_state.flashcards:
        st.subheader(f"Flashcards on {topic}")
        for i, card in enumerate(st.session_state.flashcards):
            with st.expander(f"Card {i+1}: {card['question']}", expanded=False):
                st.write(f"**Answer:** {card['answer']}")

elif st.session_state.current_tab == "quiz":
    st.header("📝 Quiz Generator")
    st.write("Test your knowledge with quizzes")
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Enter a topic:", placeholder="e.g., Ancient Rome...")
    with col2:
        num_questions = st.number_input(
            "Number of questions:", min_value=1, max_value=10, value=5
        )
    if st.button("Generate Quiz", key="gen_quiz"):
        if topic:
            with st.spinner(f"Generating {num_questions} questions..."):
                try:
                    quiz = assistant.generate_quiz(topic, num_questions)
                    st.session_state.quiz = quiz
                    st.session_state.quiz_answers = {}
                except Exception as e:
                    st.error(f"Error generating quiz: {str(e)}")
        else:
            st.warning("Please enter a topic.")
    if st.session_state.quiz:
        st.subheader(f"Quiz on {topic}")
        for i, question in enumerate(st.session_state.quiz):
            st.write(f"**Question {i+1}:** {question['question']}")
            selected_option = st.radio(
                f"Select your answer for question {i+1}:",
                question["options"],
                key=f"q{i}",
            )
            selected_index = question["options"].index(selected_option)
            st.session_state.quiz_answers[i] = selected_index
            if st.button(f"Check Answer {i+1}", key=f"check_{i}"):
                if selected_index == question["correct_index"]:
                    st.success("Correct! ✅")
                else:
                    st.error(
                        f"Incorrect. The correct answer is: {question['options'][question['correct_index']]}"
                    )
                st.info(f"**Explanation:** {question['explanation']}")
            st.divider()
        if st.button("Check All Answers", key="check_all"):
            score = 0
            for i, question in enumerate(st.session_state.quiz):
                if (
                    i in st.session_state.quiz_answers
                    and st.session_state.quiz_answers[i] == question["correct_index"]
                ):
                    score += 1
            st.success(f"Your score: {score}/{len(st.session_state.quiz)}")

elif st.session_state.current_tab == "summarizer":
    st.header("📊 Summarizer")
    st.write("Generate concise summaries")
    text_to_summarize = st.text_area(
        "Enter text to summarize:",
        height=300,
        placeholder="Paste your study material...",
    )
    col1, col2 = st.columns([3, 1])
    with col2:
        max_length = st.number_input(
            "Max summary length (characters):", min_value=100, max_value=2000, value=500
        )
    if st.button("Generate Summary", key="gen_summary"):
        if text_to_summarize:
            with st.spinner("Generating summary..."):
                try:
                    summary = assistant.summarize_material(
                        text_to_summarize, max_length
                    )
                    st.subheader("Summary")
                    st.write(summary)
                    st.info(f"Summary length: {len(summary)} characters")
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")
        else:
            st.warning("Please enter text to summarize.")

# Footer
st.write("---")
st.write("AI Study Assistant | Created by Manish Sharma")
st.write("[Follow @lucifer_x007 on Twitter](https://twitter.com/lucifer_x007)")
st.write("Powered by OpenAI")
