# 🤖 AI Resume Analyzer

An AI-powered Resume Analyzer built with **Python, Streamlit and Google Gemini**.

The application analyzes a PDF resume against a job description and provides an ATS-style evaluation, keyword analysis, improvement suggestions and a downloadable PDF report.

## ✨ Features

- 📄 PDF resume upload
- 💼 Job description analysis
- 🤖 Google Gemini-powered resume analysis
- 🎯 Overall ATS match score
- 🔑 ATS keyword analysis
- ✅ Matching skills
- ❌ Missing skills
- 💪 Strengths
- ⚠️ Weaknesses
- 🚀 Resume improvement recommendations
- 📝 Professional summary feedback
- 📥 Downloadable PDF analysis report
- 🎨 Modern purple, pink and orange UI
- 🔄 Gemini model fallback/retry handling
- 🔐 API key stored through environment variables

## 🛠️ Tech Stack

- **Python**
- **Streamlit**
- **Google Gemini API**
- **ReportLab**
- **pypdf**
- **python-dotenv**

## 📁 Project Structure

```text
AI-Resume-Analyzer/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
├── .env.example
│
├── utils/
│   └── pdf_reader.py
│
└── venv/
```

> `venv/` and `.env` should never be committed to GitHub.

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd AI-Resume-Analyzer
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Never publish your real API key on GitHub.

### 5. Start the application

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## ☁️ Streamlit Deployment

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app.
4. Select your GitHub repository.
5. Set the main file to:

```text
app.py
```

6. Add your Gemini API key in the deployment's **Secrets** section:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
```

7. Deploy the application.

Do not upload `.env` to GitHub.

## 🔒 Security

The Gemini API key is loaded from an environment variable:

```python
API_KEY = os.getenv("GEMINI_API_KEY")
```

The repository's `.gitignore` excludes `.env`.

If an API key is accidentally exposed, revoke/rotate it immediately.

## 🧪 Example Workflow

```text
Upload Resume
      ↓
Paste Job Description
      ↓
Analyze Resume
      ↓
ATS Match Score
      ↓
ATS Keyword Analysis
      ↓
Strengths & Weaknesses
      ↓
AI Improvement Suggestions
      ↓
Download PDF Report
```

## 🎯 Future Improvements

- Resume section-by-section scoring
- Resume rewriting assistant
- Multiple job-description comparison
- Resume version history
- Authentication
- Database-backed user accounts
- Advanced ATS visualizations
- Cover letter generation
- Online resume editor

## 👨‍💻 Portfolio Project

This project demonstrates practical experience with:

- Generative AI API integration
- Prompt engineering
- PDF processing
- Streamlit application development
- JSON-based AI responses
- Error handling and model fallback
- Report generation
- Environment-variable security
- AI-powered career tooling

---

Built with Python • Streamlit • Google Gemini
