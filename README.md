# Professor Matcher Agent
## Aditya Patil(23B0720) - IIT Bombay

## 1. Overview
The **Professor Matcher Agent** is an AI-powered system that evaluates a candidate's resume against the research interests of university professors and returns ranked match scores. The tool automates three major tasks:
1. Resume parsing (from PDF)
2. Faculty directory scraping
3. AI-based semantic similarity scoring using an LLM

This project is designed to help students and researchers identify relevant academic advisors based on alignment of research interests.
[Gemini Interaction Log](https://gemini.google.com/share/146ac38b45a0)

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────┐
│         ProfessorMatcherAgent           │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 1. Resume Parser (PDF)            │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 2. Faculty Directory Scraper      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 3. Match Scoring Engine (LLM)     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 2.2 Flow of Data
```
User Inputs → Resume (PDF) + Directory URL
         ↓
PDF Extractor → Full Text Resume
         ↓
Web Scraper → List of Professors (name, profile URL, research interests)
         ↓
LLM computes Match Score for each professor
         ↓
Ranked Output → Top N Matches Displayed to User
```

---

## 3. Data Design

### 3.1 Resume Data
Extracted into a **single raw text string** using `pdfplumber`. No structured parsing or NLP entity extraction is done yet.

### 3.2 Professor Data Model
```json
{
  "name": "<string>",
  "url": "<string>",
  "research_interests": "<string>"
}
```

### 3.3 Scoring Output Model
```json
{
  "name": "<professor name>",
  "research_interests": "<text scraped>",
  "score": <0-10 integer>
}
```

---

## 4. Component Breakdown

| Component | Library / Tech Used | Purpose |
|-----------|--------------------|---------|
| Resume Parser | `pdfplumber` | Extracts text from PDF resumes |
| Web Scraper | `selenium`, ChromeDriver, `webdriver-manager` | Extracts structured data from university faculty directories |
| LLM Matcher | `OpenAI` API | Computes semantic alignment between resume text and professor's research |
| Console UI | `input()` loop | Handles user interactions in CLI |

---

## 5. Chosen Technologies and Justification

| Technology | Reason |
|------------|--------|
| **Python** | Rapid prototyping, easy integration with NLP + scraping libraries |
| **pdfplumber** | Better text extraction quality than PyPDF2, supports layout reading |
| **Selenium** | Required for JS-rendered faculty pages; headless automation |
| **OpenAI Chat Completion API** | Reliable LLM reasoning, supports JSON mode response |
| **ChromeDriverManager** | Auto-installs correct ChromeDriver version, avoids OS config issues |
| **JSON-based scoring** | Enforces deterministic LLM outputs for downstream formatting |

---

## 6. Running the Agent
```bash
export OPENAI_API_KEY="your_key_here"
python main.py
```

You will be prompted for:
```
[Chat] Enter faculty directory URL:
[Chat] Enter resume PDF path:
```

---

## 7. Example Output
```
--- TOP 10 PROFESSOR MATCHES ---

#1: Prof. ABC
  - Research Area: Machine Learning, Vision
  - Match Score: 9/10

#2: Prof. XYZ
  - Research Area: Distributed Systems, Cloud Infra
  - Match Score: 8/10
```

---

## 8. Notes
- Each university website requires custom scraping logic.
- The match score is interpretive and depends on the LLM.
