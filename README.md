# Transwork Business Assistant v1

A simple AI-powered business assistant built in Python with the Google Gemini API.
Week 3 project — Generative AI Foundations, Transwork Company Limited.

---

## 1. Problem

Customer-service and admin staff spend a lot of time on repetitive text work:

- Writing replies to customers, often under pressure and with inconsistent tone.
- Reading long reports to find the few points management needs.
- Reading every customer message by hand to work out who it is from, what the problem is and how urgent it is.

Slow handling means late responses (our fictional Q3 report shows a 3.5-day average complaint response against a 1-day target) and unhappy customers.

## 2. Solution

A Python assistant with three functions:

| # | Function | Input | Output |
|---|---|---|---|
| 1 | **Business Writing** | Customer name, situation, staff notes, tone | Professional draft reply |
| 2 | **Summarisation** | Any business report or document | One-line summary, key points, key numbers, actions needed |
| 3 | **Information Extraction** | A customer enquiry (any quality of writing) | Structured JSON: name, issue, category, urgency, recommended action, missing info, confidence, human-review flag |

Example output from Function 3:

```json
{
  "customer_name": "John Mensah",
  "issue": "Delivery TW-20451 late, no communication",
  "category": "Complaint",
  "urgency": "High",
  "recommended_action": "Customer-service officer should call the customer today with a new delivery date.",
  "missing_information": [],
  "confidence": "High",
  "human_review_required": true,
  "review_reasons": ["High urgency case"]
}
```

## 3. Technology

- **Python 3.10+**
- **Google Gemini API** (`google-genai` SDK, Interactions API), default model `gemini-3.5-flash-lite` (tested about 100x faster than `gemini-3.8-flash` with similar quality)
- **Pydantic** to define and validate the structured output
- **python-dotenv** to keep the API key out of the code

## 4. How It Works

```
User input → Python (prompt + rules) → Gemini API → AI model → AI response
           → Python checks the response → Result shown / saved as JSON
```

1. `prompts.py` holds all prompts, each with clear instructions, rules and output format.
2. `assistant.py` sends the prompt to Gemini through `ask_model()`.
3. For extraction, Python sends a **JSON schema** (built from the `EnquiryExtraction` Pydantic class), so Gemini must reply with JSON in exactly that shape. Category, urgency and confidence are limited to fixed options.
4. Python **validates** the reply. If it does not match the structure, it is not passed on; it is marked for human review instead.
5. Plain Python **business rules** (not AI) decide when a person must review: high urgency, low confidence, no name, missing information, or not a real enquiry.

### Project files

```
assistant.py          Core logic: Gemini connection + the 3 functions
prompts.py            All prompts in one place
main.py               Terminal menu to use the assistant
run_tests.py          Runs all sample inputs, saves outputs and TESTING_RESULTS.md
sample_inputs/        Writing request, fictional business report, 6 test enquiries
sample_outputs/       Real outputs created by run_tests.py
TESTING_RESULTS.md    Test results table + findings
requirements.txt      Python packages
.env.example          Template for your API key
```

### Setup and run

```bash
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
# open .env and paste your key from https://aistudio.google.com/apikey

python main.py                # use the assistant interactively
python run_tests.py           # run all tests and create TESTING_RESULTS.md
```

## 5. Business Value

- **Faster responses:** a draft reply in seconds instead of 10–15 minutes.
- **Better prioritisation:** urgent cases (money lost, legal threats, service stopped) are flagged automatically.
- **Consistency:** every reply follows the same professional standard.
- **Ready for other systems:** the JSON output can go straight into a ticketing system, spreadsheet or CRM.
- **Management time saved:** reports reduced to the points that need decisions.

## 6. Limitations

- The AI can misjudge urgency or category, especially for short or unclear messages.
- It only knows what is in the input. It cannot check bookings, invoices or customer records.
- Poorly written or Pidgin/Twi-mixed messages are handled reasonably but less reliably.
- Very long inputs are cut at 20,000 characters.
- Needs an internet connection and a valid API key; free-tier rate limits apply.
- Output can change slightly each time for the same input.

## 7. Risks and Controls

| Risk | Control in this project |
|---|---|
| **Hallucination** — AI invents refunds, dates or facts | Prompts forbid inventing promises; `[PLACEHOLDER]` used for missing facts; staff review every draft before sending |
| **Wrong extraction** sent to another system | Schema-enforced JSON + Pydantic validation; invalid output is blocked and flagged |
| **Urgent case missed** | High urgency and low confidence always trigger human review |
| **Customer privacy** — personal data sent to an external AI | Only use test/fictional data in v1; a real deployment needs a data-protection review (Ghana Data Protection Act, 2012) |
| **API key leak** | Key kept in `.env`, which is excluded by `.gitignore` |
| **Over-reliance on AI** | The assistant drafts and sorts; a person makes the final decision |

**Human review is required** for every customer reply before it is sent, and for every case the system flags.
