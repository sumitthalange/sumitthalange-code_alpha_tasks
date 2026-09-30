import requests
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

LANGUAGES = {
    "English": "en", "Hindi": "hi", "Marathi": "mr", "French": "fr",
    "German": "de", "Spanish": "es", "Italian": "it", "Portuguese": "pt",
    "Arabic": "ar", "Japanese": "ja", "Korean": "ko", "Chinese": "zh-CN",
    "Russian": "ru", "Turkish": "tr"
}

class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LinguaFlow • Language Translator")
        self.geometry("950x650")
        self.minsize(800, 560)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="🌐 LinguaFlow",
            font=ctk.CTkFont(size=32, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(25, 3))

        ctk.CTkLabel(
            self, text="Simple AI-powered language translation tool",
            text_color="#9aa4b2", font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, columnspan=2, pady=(0, 18))

        self.left = ctk.CTkFrame(self, corner_radius=18)
        self.right = ctk.CTkFrame(self, corner_radius=18)
        self.left.grid(row=2, column=0, padx=(25, 10), pady=10, sticky="nsew")
        self.right.grid(row=2, column=1, padx=(10, 25), pady=10, sticky="nsew")

        for frame in (self.left, self.right):
            frame.grid_rowconfigure(2, weight=1)
            frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.left, text="Source Language",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
                     row=0, column=0, padx=20, pady=(20, 8), sticky="w")

        self.source = ctk.CTkComboBox(self.left, values=list(LANGUAGES.keys()))
        self.source.set("English")
        self.source.grid(row=1, column=0, padx=20, sticky="ew")

        self.input_box = ctk.CTkTextbox(self.left, corner_radius=12, font=ctk.CTkFont(size=16))
        self.input_box.grid(row=2, column=0, padx=20, pady=18, sticky="nsew")
        self.input_box.insert("1.0", "Welcome to my language translation project!")

        ctk.CTkLabel(self.right, text="Target Language",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
                     row=0, column=0, padx=20, pady=(20, 8), sticky="w")

        self.target = ctk.CTkComboBox(self.right, values=list(LANGUAGES.keys()))
        self.target.set("Hindi")
        self.target.grid(row=1, column=0, padx=20, sticky="ew")

        self.output_box = ctk.CTkTextbox(self.right, corner_radius=12, font=ctk.CTkFont(size=16))
        self.output_box.grid(row=2, column=0, padx=20, pady=18, sticky="nsew")

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, columnspan=2, pady=(5, 20))

        ctk.CTkButton(bottom, text="↔ Swap", width=110, command=self.swap).pack(side="left", padx=6)
        ctk.CTkButton(bottom, text="✨ Translate", width=150, height=40,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.translate).pack(side="left", padx=6)
        ctk.CTkButton(bottom, text="📋 Copy Result", width=140, command=self.copy_result).pack(side="left", padx=6)
        ctk.CTkButton(bottom, text="Clear", width=90, fg_color="#444b55",
                      hover_color="#555e69", command=self.clear).pack(side="left", padx=6)

        self.status = ctk.CTkLabel(self, text="Ready • Translation API: MyMemory",
                                   text_color="#7dd3fc")
        self.status.grid(row=4, column=0, columnspan=2, pady=(0, 12))

    def translate(self):
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty text", "Please enter some text to translate.")
            return

        source = LANGUAGES[self.source.get()]
        target = LANGUAGES[self.target.get()]

        if source == target:
            self.output_box.delete("1.0", "end")
            self.output_box.insert("1.0", text)
            return

        self.status.configure(text="⏳ Translating...", text_color="#fbbf24")
        self.update_idletasks()

        try:
            url = "https://api.mymemory.translated.net/get"
            params = {"q": text, "langpair": f"{source}|{target}"}
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            translated = data.get("responseData", {}).get("translatedText", "")

            if not translated:
                raise ValueError("No translated text was returned.")

            self.output_box.delete("1.0", "end")
            self.output_box.insert("1.0", translated)
            self.status.configure(text="✓ Translation completed", text_color="#86efac")
        except Exception as exc:
            self.status.configure(text="Translation failed", text_color="#fca5a5")
            messagebox.showerror(
                "Translation Error",
                f"Could not reach the translation service.\n\n{exc}\n\n"
                "Please check your internet connection and try again."
            )

    def swap(self):
        s, t = self.source.get(), self.target.get()
        self.source.set(t)
        self.target.set(s)

        old_input = self.input_box.get("1.0", "end").strip()
        old_output = self.output_box.get("1.0", "end").strip()
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", old_output)
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", old_input)

    def copy_result(self):
        text = self.output_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.configure(text="✓ Result copied to clipboard", text_color="#86efac")

    def clear(self):
        self.input_box.delete("1.0", "end")
        self.output_box.delete("1.0", "end")
        self.status.configure(text="Ready • Translation API: MyMemory", text_color="#7dd3fc")

if __name__ == "__main__":
    TranslatorApp().mainloop()
