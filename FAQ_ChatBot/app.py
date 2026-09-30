import re
import customtkinter as ctk
from tkinter import messagebox
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FAQS = [
    ("What is this chatbot?",
     "This is a simple FAQ chatbot that matches your question with the most similar question in its knowledge base."),
    ("What programming language is used?",
     "This project is developed in Python."),
    ("How can I install Python?",
     "Download Python from the official Python website and make sure Python is added to PATH during installation."),
    ("What is Python?",
     "Python is a high-level, general-purpose programming language known for its simple syntax and large library ecosystem."),
    ("What is machine learning?",
     "Machine learning is a branch of AI where computers learn patterns from data to make predictions or decisions."),
    ("What is NLP?",
     "Natural Language Processing, or NLP, is a field of AI that helps computers process and understand human language."),
    ("How does this chatbot match questions?",
     "It converts FAQ questions and the user's question into TF-IDF vectors and uses cosine similarity to find the closest match."),
    ("What is TF-IDF?",
     "TF-IDF is a text representation technique that gives importance to words based on how frequently and uniquely they occur."),
    ("What is cosine similarity?",
     "Cosine similarity measures how similar two text vectors are. A value closer to 1 means they are more similar."),
    ("Can I add more questions?",
     "Yes. Add another question and answer pair to the FAQS list in app.py."),
    ("Does the chatbot need an internet connection?",
     "No. This FAQ chatbot works locally and does not need an internet connection."),
    ("What is the minimum similarity?",
     "This demo uses 0.20 as a confidence threshold. If the similarity is lower, the chatbot asks the user to rephrase the question."),
]

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

questions = [clean_text(q) for q, _ in FAQS]
vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
faq_matrix = vectorizer.fit_transform(questions)

class FAQBot(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AskMate • FAQ Chatbot")
        self.geometry("900x680")
        self.minsize(760, 580)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="💬 AskMate",
                     font=ctk.CTkFont(size=32, weight="bold")).grid(
                     row=0, column=0, pady=(25, 2))
        ctk.CTkLabel(self, text="FAQ chatbot powered by TF-IDF + cosine similarity",
                     text_color="#9aa4b2").grid(row=1, column=0, pady=(0, 15))

        self.chat = ctk.CTkTextbox(self, corner_radius=18, font=ctk.CTkFont(size=15))
        self.chat.grid(row=2, column=0, padx=25, pady=10, sticky="nsew")
        self.chat.configure(state="disabled")

        bottom = ctk.CTkFrame(self, corner_radius=15)
        bottom.grid(row=3, column=0, padx=25, pady=(5, 15), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(bottom, height=45,
                                  placeholder_text="Type your question here...")
        self.entry.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="ew")
        self.entry.bind("<Return>", lambda event: self.ask())

        ctk.CTkButton(bottom, text="Ask ✨", width=110, height=45,
                      font=ctk.CTkFont(weight="bold"), command=self.ask).grid(
                      row=0, column=1, padx=(0, 8), pady=15)
        ctk.CTkButton(bottom, text="Clear", width=80, height=45,
                      fg_color="#444b55", hover_color="#555e69",
                      command=self.clear_chat).grid(
                      row=0, column=2, padx=(0, 15), pady=15)

        self.status = ctk.CTkLabel(self, text="Ready • 12 FAQs loaded",
                                   text_color="#7dd3fc")
        self.status.grid(row=4, column=0, pady=(0, 12))

        self.add_message("Bot", "Hi! 👋 Ask me anything about this project, Python, NLP or machine learning.")

    def add_message(self, speaker, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{speaker}\n{text}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def ask(self):
        user_text = self.entry.get().strip()
        if not user_text:
            return

        self.add_message("You", user_text)
        self.entry.delete(0, "end")

        cleaned = clean_text(user_text)
        user_vector = vectorizer.transform([cleaned])
        scores = cosine_similarity(user_vector, faq_matrix)[0]
        best_index = scores.argmax()
        confidence = float(scores[best_index])

        if confidence < 0.20:
            answer = "I'm not confident about that one yet. 🤔 Try asking the question in a simpler way."
        else:
            answer = FAQS[best_index][1]

        self.add_message("AskMate", answer)
        self.status.configure(
            text=f"Match confidence: {confidence:.0%}",
            text_color="#86efac" if confidence >= 0.20 else "#fbbf24"
        )

    def clear_chat(self):
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self.status.configure(text="Ready • 12 FAQs loaded", text_color="#7dd3fc")

if __name__ == "__main__":
    FAQBot().mainloop()
