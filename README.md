# ECHO 👻

**Extract, Convert, Hear & Organize**

ECHO is a minimalist web application built with Python and Streamlit for downloading YouTube media and processing audio with AI, featuring local transcription with Whisper and automatic summarization with Google Gemini.

---

## 🚀 Features

* **Media Downloading**

  * Video extraction in MP4 with multiple resolutions.
  * Audio extraction in MP3 with multiple bitrates.

* **AI Transcription**

  * Converts video audio to text using the OpenAI Whisper model.

* **Smart Summarization**

  * Generates structured summaries in a guide/lesson format using the Google Gemini API.

* **Minimalist Dark UI**

  * Clean, responsive, and customized interface without visual distractions.

* **Handy Tools**

  * Quick copy buttons.
  * Download transcriptions and summaries as `.txt` files.

---

## 🛠️ Tech Stack

* **Python 3.10+**
* **Streamlit** — Web UI
* **yt-dlp** — Media extraction and processing
* **OpenAI Whisper** — Audio processing and transcription
* **Google GenAI SDK** — AI summarization
* **FFmpeg** — Background media processing

---

## 📦 Installation & Setup

### 1. Prerequisites

Make sure you have the following installed:

* Python 3.10 or higher
* FFmpeg

### 2. Clone the Repository

```bash
git clone https://github.com/LeonardoIensen/echo.git
cd echo
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Rename `.env.example` to `.env` and add your Google Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

You can get a free API key from Google AI Studio.

### 5. Run the Application

```bash
streamlit run app.py
```

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
