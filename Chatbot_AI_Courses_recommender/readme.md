# 🤖 Intelligent Course Recommendation Chatbot

This repository contains an advanced AI-powered chatbot designed to recommend professional training courses based on user inputs. The system leverages state-of-the-art technologies, including **natural language processing with Google Gemini**, **vector search with embeddings**, **cloud-based databases**, and a **modern conversational interface built with Streamlit**.

---

## 🎯 Overview

The chatbot is built as a full-stack AI application that:

- Understands user intents via LLM-based keyword extraction and classification.  
- Recommends courses through semantic search powered by embeddings and vector databases.  
- Stores and manages user sessions, conversation history, and course enrollments using cloud services.  
- Offers a seamless conversational experience with real-time chat, authentication, and personalized course suggestions.

---

## 🧠 Learning Objectives

By exploring or building upon this project, you’ll gain hands-on experience in:

- Integrating generative AI (Google Gemini) into real-world applications  
- Implementing semantic search and recommendations using vector embeddings (VertexAI + Qdrant)  
- Building REST APIs with FastAPI that interact with multiple external services  
- Creating intuitive conversational UIs with Streamlit  
- Managing user authentication and session data across cloud databases (Supabase & Firebase)  
- Designing a robust microservices architecture for AI applications  

---

## 🛠️ Tech Stack

### Core Technologies

- **Backend**: FastAPI (Python)  
- **Frontend**: Streamlit  
- **Generative AI**: Google Gemini 2.0 Flash  
- **Embeddings**: VertexAI Text Embedding Model  
- **Vector Search**: Qdrant Cloud  
- **Authentication**: Supabase  
- **Conversation History**: Firebase Firestore  
- **Containerization**: Docker  

### Python Libraries

```bash
fastapi==0.115.7  
streamlit  
google-generativeai==0.8.3  
vertexai==1.70.0  
qdrant-client  
supabase==2.3.4  
firebase-admin  
python-dotenv==1.0.1  
passlib[bcrypt]==1.7.4  
