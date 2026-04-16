# Intelligent Insurance Policy Analyzer

Production-ready AI-powered Insurance Policy Analyzer built with Python, Streamlit, Flask, and OpenAI.

## Features

- **Policy Summary**: Simple plain-English explanation
- **Key Benefits & Exclusions**: Extracted from document
- **Hidden Clauses**: AI-identified risky conditions
- **Policy Type Detection**: Term / Endowment / ULIP
- **Financial Analysis**: Premium, Tenure, Total Investment, Maturity, Net Profit
- **CAGR & ROI**: Annualized returns, inflation-adjusted
- **Guaranteed vs Non-Guaranteed** classification
- **Risk Score (1–10)**: Based on tenure, lock-in, clauses, returns
- **Recommendation**: Who should buy the policy
- **Comparison**: vs 7% FD and 12% MF SIP

## Architecture

```
BimaBuddy AI/
├── frontend/
│   └── app.py                    # Streamlit UI
├── backend/
│   ├── api.py                    # Flask REST API
│   ├── core/
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── logger.py             # Structured logging
│   └── services/
│       ├── pdf_service.py        # PDF text extraction
│       ├── ai_service.py         # Gemini AI analysis
│       ├── financial_engine.py   # ROI, CAGR calculations
│       ├── policy_classifier.py  # Policy type detection
│       ├── risk_analyzer.py      # Risk scoring
│       └── regex_extractor.py    # Regex financial extraction
├── config.py                     # Configuration with validation
├── requirements.txt
└── README.md
```

### Production Practices

- **Error handling**: Custom exception hierarchy (`PDFProcessingError`, `AIAnalysisError`, etc.)
- **Logging**: Structured logging with `bimabuddy` logger
- **Financial calculations**: Validated formulas, edge-case handling
- **AI prompts**: Optimized structured extraction with schema hints

## Setup

### 1. Clone / Navigate to Project

```bash
cd "c:\Users\hp\Desktop\BimaBuddy AI"
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Install Tesseract OCR for Scanned PDFs

For **scanned or image-based PDFs**, install Tesseract OCR:

- **Windows:** Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH
- **Mac:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

Without Tesseract, scanned PDFs will fail with "Could not extract text". Text-selectable PDFs work without it.

### 5. Set Environment Variables

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "your-gemini-api-key"

# Windows (CMD)
set GEMINI_API_KEY=your-gemini-api-key

# Linux/Mac
export GEMINI_API_KEY=your-gemini-api-key
```

Optional:
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)
- `FLASK_HOST` (default: `127.0.0.1`)
- `FLASK_PORT` (default: `5000`)

## Run Locally

### Terminal 1 – Start Flask Backend

```bash
python -m backend.api
# or: python backend/api.py
```

Backend runs at `http://127.0.0.1:5000`.

### Terminal 2 – Start Streamlit Frontend

```bash
streamlit run frontend/app.py
```

Frontend opens at `http://localhost:8501`.

## API Endpoints

| Method | Endpoint  | Description        |
|--------|-----------|--------------------|
| GET    | /health   | Health check       |
| POST   | /analyze  | Analyze PDF (multipart form, key: `file`) |

### Example API Request

```bash
curl -X POST -F "file=@policy.pdf" http://127.0.0.1:5000/analyze
```

## Example Test Case

1. Create a simple PDF with text like:

   ```
   LIC Jeevan Anand - Endowment Plan
   Annual Premium: Rs 50,000
   Policy Term: 25 years
   Sum Assured: Rs 10,00,000
   Maturity Benefit: Rs 15,00,000 (Guaranteed)
   Benefits: Death benefit, Maturity benefit, Bonus
   Exclusions: Suicide within 1 year
   ```

2. Upload it via the Streamlit UI and click **Analyze Policy**.

## Sample API Response JSON

```json
{
  "success": true,
  "policy_summary": {
    "simple_summary": "Endowment plan with 25-year term...",
    "policy_type": "endowment",
    "guaranteed_return": true
  },
  "key_benefits": ["Death benefit", "Maturity benefit"],
  "exclusions": ["Suicide within 1 year"],
  "hidden_clauses": [],
  "policy_type_detected": "endowment",
  "premium_details": { "amount": 50000, "frequency": "yearly" },
  "tenure_years": 25,
  "total_investment": 1250000,
  "maturity_value": 1500000,
  "net_profit": 250000,
  "cagr_percent": 0.93,
  "guaranteed_vs_non_guaranteed": "Guaranteed",
  "risk_score": 3,
  "risk_level": "Low-Medium",
  "recommendation": "Suitable for conservative investors..."
}
```

## Error Handling

- Invalid PDF → 422
- Missing API key → 503
- File too large (>16MB) → 413
- AI parse failure → 422
- Timeout → Handled with user message

## License

MIT
