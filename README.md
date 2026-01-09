# 🎓 Lecture Voice-to-Notes Generator using AI

An AI-powered application that converts lecture audio into structured notes, summaries, quizzes, and downloadable PDFs using Speech-to-Text and Natural Language Processing techniques.

---

## 📌 Problem Statement

Students often miss important points during lectures as it is difficult to listen, understand, and take notes simultaneously. Existing tools either provide raw transcripts or require manual effort.

This project aims to automate the entire process by converting lecture audio into:
- Clean transcripts
- Structured study notes
- Auto-generated quizzes
- Downloadable PDFs

---

## 🚀 Features

- 🎤 Converts lecture audio to text using Whisper
- 🧠 Generates structured notes using AI models
- ❓ Creates quizzes for self-assessment
- 📄 Exports notes as PDF
- 🌐 REST API using FastAPI
- 🖥️ Interactive UI using Streamlit
- 📂 Supports long lecture audio via chunking

---

## 🛠️ Tech Stack

### Backend
- Python 3.10
- FastAPI
- Whisper (Speech-to-Text)
- HuggingFace Transformers
- Pydub
- ReportLab

### Frontend
- Streamlit

### AI / ML
- OpenAI Whisper
- FLAN-T5 (Text-to-Text Generation)

---