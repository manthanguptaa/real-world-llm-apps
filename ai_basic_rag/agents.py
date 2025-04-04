from openai import OpenAI
from typing import List, Dict, Any
from vector_store import Milvus
import json
from dotenv import load_dotenv
import os
from pymilvus.exceptions import ConnectionNotExistException

load_dotenv()

class Agent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.setup_vector_store()
        self.model = "gpt-4o"
        self.conversation_history = []
        
    def setup_vector_store(self):
        """Initialize or reinitialize the vector store."""
        self.vector_store = Milvus(
            collection="knowledge",
            dimension=1536,
            uri="tmp/milvus.db"
        )

    def get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def store_knowledge(self, text: str) -> int:
        try:
            embedding = self.get_embedding(text)
            return self.vector_store.store_vectors([text], [embedding])[0]
        except ConnectionNotExistException:
            # Reconnect and try again
            print("Reconnecting to Milvus...")
            self.setup_vector_store()
            embedding = self.get_embedding(text)
            return self.vector_store.store_vectors([text], [embedding])[0]
        except Exception as e:
            print(f"Error storing knowledge: {e}")
            raise

    def search_knowledge(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.get_embedding(query)
            return self.vector_store.search_vectors(query_embedding, top_k)
        except ConnectionNotExistException:
            # Reconnect and try again
            print("Reconnecting to Milvus...")
            self.setup_vector_store()
            query_embedding = self.get_embedding(query)
            return self.vector_store.search_vectors(query_embedding, top_k)
        except Exception as e:
            print(f"Error searching knowledge: {e}")
            raise

    def generate_response(self, query: str) -> str:
        try:
            # Search for relevant knowledge
            relevant_knowledge = self.search_knowledge(query)
            context = "\n".join([item["text"] for item in relevant_knowledge])

            # Prepare conversation history
            history = "\n".join([
                f"User: {msg['user']}\nAssistant: {msg['assistant']}"
                for msg in self.conversation_history[-5:]  # Keep last 5 exchanges
            ])

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately."},
                    {"role": "system", "content": f"Relevant context:\n{context}"},
                    {"role": "system", "content": f"Previous conversation:\n{history}"},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )

            # Store the exchange in history
            self.conversation_history.append({
                "user": query,
                "assistant": response.choices[0].message.content
            })

            return response.choices[0].message.content
        except ConnectionNotExistException:
            # Reconnect and try again
            print("Reconnecting to Milvus...")
            self.setup_vector_store()
            return self.generate_response(query)
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    def get_conversation_history(self) -> List[Dict[str, str]]:
        return self.conversation_history 