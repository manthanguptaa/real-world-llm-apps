import json
import os
import time
import uuid
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from pymilvus.exceptions import ConnectionNotExistException

from vector_store import StudyMaterialsStore

load_dotenv()


class StudyAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        self.conversation_history = []
        self.vector_store = None
        self.setup_vector_store()

    def setup_vector_store(self):
        """Initialize or reinitialize the vector store."""
        try:
            # Create a shorter unique identifier
            unique_id = str(uuid.uuid4())[:8]
            timestamp = str(int(time.time()))[-6:]
            db_uri = f"tmp/sa_{unique_id}_{timestamp}.db"

            self.vector_store = StudyMaterialsStore(
                collection="study_materials", dimension=1536, uri=db_uri
            )
        except Exception as e:
            print(f"Error setting up vector store: {e}")
            # Try with a new unique URI
            unique_id = str(uuid.uuid4())[:8]
            timestamp = str(int(time.time()))[-6:]
            new_uri = f"tmp/sa_{unique_id}_{timestamp}.db"
            self.vector_store = StudyMaterialsStore(
                collection="study_materials", dimension=1536, uri=new_uri
            )

    def get_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return response.data[0].embedding

    def store_material(self, text: str, metadata: Dict = None) -> int:
        """Store study material in the vector store."""
        try:
            embedding = self.get_embedding(text)
            meta = metadata or {}
            return self.vector_store.store_vectors([text], [embedding], [meta])[0]
        except ConnectionNotExistException:
            # Reconnect and try again
            print("Reconnecting to vector store...")
            self.setup_vector_store()
            embedding = self.get_embedding(text)
            meta = metadata or {}
            return self.vector_store.store_vectors([text], [embedding], [meta])[0]
        except Exception as e:
            print(f"Error storing material: {e}")
            raise

    def search_materials(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant study materials."""
        try:
            query_embedding = self.get_embedding(query)
            return self.vector_store.search_vectors(query_embedding, top_k)
        except ConnectionNotExistException:
            # Reconnect and try again
            print("Reconnecting to vector store...")
            self.setup_vector_store()
            query_embedding = self.get_embedding(query)
            return self.vector_store.search_vectors(query_embedding, top_k)
        except Exception as e:
            print(f"Error searching materials: {e}")
            raise

    def generate_response(self, query: str) -> str:
        """Generate a response to a student's question."""
        try:
            # Search for relevant materials
            relevant_materials = self.search_materials(query)
            context = "\n".join([item["text"] for item in relevant_materials])

            # Prepare conversation history
            history = "\n".join(
                [
                    f"Student: {msg['user']}\nAssistant: {msg['assistant']}"
                    for msg in self.conversation_history[-5:]  # Keep last 5 exchanges
                ]
            )

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant. Use the provided context from study materials to answer questions accurately and in a way that helps students understand the concepts.",
                    },
                    {
                        "role": "system",
                        "content": f"Relevant study materials:\n{context}",
                    },
                    {"role": "system", "content": f"Previous conversation:\n{history}"},
                    {"role": "user", "content": query},
                ],
                temperature=0.7,
            )

            # Store the exchange in history
            self.conversation_history.append(
                {"user": query, "assistant": response.choices[0].message.content}
            )

            return response.choices[0].message.content
        except ConnectionNotExistException:
            # Reconnect and try again
            print("Reconnecting to vector store...")
            self.setup_vector_store()
            return self.generate_response(query)
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    def generate_flashcards(self, topic: str, count: int = 5) -> List[Dict[str, str]]:
        """Generate flashcards for a specific topic."""
        try:
            # Search for relevant materials
            relevant_materials = self.search_materials(topic)
            context = "\n".join([item["text"] for item in relevant_materials])

            prompt = f"""
            Based on the following study materials, create {count} flashcards about {topic}.
            Each flashcard should have a question on one side and the answer on the other.
            
            Study materials:
            {context}
            
            Format your response as a JSON array of objects, each with 'question' and 'answer' fields.
            Make the questions challenging but fair, and the answers concise but complete.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant that creates effective flashcards for students.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            # Parse the JSON response
            content = response.choices[0].message.content
            try:
                # Extract JSON if it's wrapped in markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                flashcards = json.loads(content)
                return flashcards
            except json.JSONDecodeError:
                # If JSON parsing fails, return a formatted error
                return [
                    {
                        "question": "Error",
                        "answer": "Could not generate flashcards. Please try again.",
                    }
                ]

        except Exception as e:
            print(f"Error generating flashcards: {e}")
            return [{"question": "Error", "answer": f"Error: {str(e)}"}]

    def generate_quiz(self, topic: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate a quiz with multiple-choice questions."""
        try:
            # Search for relevant materials
            relevant_materials = self.search_materials(topic)
            context = "\n".join([item["text"] for item in relevant_materials])

            prompt = f"""
            Based on the following study materials, create a quiz with {num_questions} multiple-choice questions about {topic}.
            Each question should have 4 options with only one correct answer.
            
            Study materials:
            {context}
            
            Format your response as a JSON array of objects, each with:
            - 'question': the question text
            - 'options': array of 4 possible answers
            - 'correct_index': the index (0-3) of the correct answer
            - 'explanation': brief explanation of why the answer is correct
            
            Make the questions challenging but fair, covering important concepts from the materials.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant that creates effective quizzes for students.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            # Parse the JSON response
            content = response.choices[0].message.content
            try:
                # Extract JSON if it's wrapped in markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                quiz = json.loads(content)
                return quiz
            except json.JSONDecodeError:
                # If JSON parsing fails, return a formatted error
                return [
                    {
                        "question": "Error",
                        "options": ["Error"],
                        "correct_index": 0,
                        "explanation": "Could not generate quiz. Please try again.",
                    }
                ]

        except Exception as e:
            print(f"Error generating quiz: {e}")
            return [
                {
                    "question": "Error",
                    "options": ["Error"],
                    "correct_index": 0,
                    "explanation": f"Error: {str(e)}",
                }
            ]

    def summarize_material(self, text: str, max_length: int = 500) -> str:
        """Generate a concise summary of study material."""
        try:
            prompt = f"""
            Summarize the following study material in a clear, concise way that highlights the key concepts.
            Keep the summary under {max_length} characters.
            
            Study material:
            {text}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant that creates concise, accurate summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"

    def explain_concept(self, concept: str) -> str:
        """Provide a detailed explanation of a concept."""
        try:
            # Search for relevant materials
            relevant_materials = self.search_materials(concept)
            context = "\n".join([item["text"] for item in relevant_materials])

            prompt = f"""
            Explain the concept of "{concept}" in detail, using the provided study materials as a reference.
            If the materials don't cover this concept well, use your general knowledge to provide a clear explanation.
            
            Study materials:
            {context}
            
            Your explanation should be:
            1. Clear and easy to understand
            2. Include examples where appropriate
            3. Break down complex ideas into simpler components
            4. Highlight key points that students should remember
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant that explains concepts clearly and accurately.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error explaining concept: {e}")
            return f"Error explaining concept: {str(e)}"

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history
