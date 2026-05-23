# 📝 NotesVault

NotesVault is a lightweight, secure, and intuitive web application designed to streamline your note-taking experience. Built entirely in Python using the **Flask** web framework, NotesVault features a powerful **Optical Character Recognition (OCR)** engine that allows users to seamlessly extract text from images and convert them into editable, searchable digital notes.

---

## ✨ Features

- **Rich Note-Taking:** Create, edit, and organize your text notes with a clean, distraction-free user interface.
- **Image-to-Text (OCR):** Upload images (receipts, book pages, whiteboard screenshots) and instantly extract readable text using Python's OCR capabilities.
- **Search & Filter:** Find notes instantly with a fast global search that indexes both manual entries and text extracted from images.
- **Secure Storage:** Safely store and manage your personal database of knowledge.
- **Clean UI/UX:** Responsive and modern design tailored for both desktop and mobile viewports.

---

## 🛠️ Tech Stack

- **Backend Framework:** [Flask](https://flask.palletsprojects.com/) (Python)
- **OCR Engine:** [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) / `pytesseract`
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML5, CSS3, JavaScript (Bootstrap / Tailwind CSS)

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Ensure you have Python 3.8+ installed on your system. You will also need to install **Tesseract OCR** on your operating system for the image-to-text functionality to work.

#### Installing Tesseract OCR:
- **Windows:** Download and run the installer from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Note down your installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
- **macOS:** Install via Homebrew:
  ```bash
  brew install tesseract
  
