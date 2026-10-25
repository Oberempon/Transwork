# Testing Results — Transwork Business Assistant v1

Two full test runs were done on 25 October 2026 with the same 8 inputs:

| Run | Model | Total time for 8 tests | Time per enquiry |
|---|---|---|---|
| Run 1 (13:24) | `gemini-3.8-flash` | about 44 minutes | 198–319 seconds |
| **Run 2 (21:09) — final** | **`gemini-3.5-flash-lite`** | **about 25 seconds** | **2.3–2.8 seconds** |

The final outputs in `sample_outputs/` come from Run 2.

## 1. Speed comparison

| Test | Run 1: gemini-3.8-flash | Run 2: gemini-3.5-flash-lite |
|---|---|---|
| Business writing | 804.0 s | 6.8 s |
| Summarisation | 310.3 s | 3.4 s |
| 01 Normal enquiry | 197.6 s | 2.5 s |
| 02 Very long enquiry | 262.7 s | 2.6 s |
| 03 Ambiguous enquiry | 249.6 s | 2.6 s |
| 04 Missing information | 253.4 s | 2.4 s |
| 05 Poorly written enquiry | 264.5 s | 2.8 s |
| 06 Unexpected input | 318.9 s | 2.3 s |

A speed test (`speed_test.py`) showed that even a one-word reply took 96–136 seconds on `gemini-3.8-flash`. The slowness came from that model on the free tier, not from the prompts or the code. The lite model was about 100 times faster, and the quality of its answers was almost the same (see below).

## 2. Information extraction tests (Run 2)

| Test type | Input file | Name | Category | Urgency | Confidence | Human review? | Time (s) | Observation |
|---|---|---|---|---|---|---|---|---|
| Normal enquiry | `01_normal.txt` | John Mensah | Complaint | Medium | High | No | 2.5 | All facts correct and the booking reference TW-20451 was used in the action. Urgency "Medium" is softer than a human would choose: the customer was promised a date and nobody called him. Both models chose Medium, and because of that this case skipped human review. |
| Very long enquiry | `02_very_long.txt` | Adwoa Boateng | Complaint | High | High | Yes: High urgency case | 2.6 | Found the three main problems (missing October truck, overcharged invoices, damaged goods) and rated it High. It did not mention the threat of legal action or the GHS 60,000 order at risk, which a manager would want to see. |
| Ambiguous enquiry | `03_ambiguous.txt` | Esi | Complaint | Medium | Medium | Yes: Information is missing | 2.6 | Did not invent details. It sensibly suggested checking Esi's previous tickets and asked for the ticket number. "Complaint" is a guess, since the message does not say what the problem is. |
| Missing information | `04_missing_info.txt` | — (null) | Billing | High | High | Yes: High urgency case, No customer name found, Information is missing | 2.4 | Did not make up a name, which is correct. Billing was the right category. It listed what staff must ask (account number, transaction date). The action says "initiate a refund", so a person must confirm the double charge first. |
| Poorly written enquiry | `05_poorly_written.txt` | kwame | Complaint | High | High | Yes: High urgency case, Information is missing | 2.8 | Understood the Pidgin message well: truck not arrived since Monday, goods spoiling. The name was kept in lower case as written. It did not record that the customer had already called 3 times with no answer, which shows how angry he is. |
| Unexpected input | `06_unexpected.txt` | — (null) | Other | Low | High | Yes: No customer name found, Not a clear customer enquiry | 2.3 | Correctly recognised it is not a business enquiry and suggested closing it. The review rules still sent it to a person, which wastes staff time on obvious spam. (The slower model rated its confidence Low; the lite model rated it High.) |

Full JSON for each test is in `sample_outputs/`.

## 3. Business writing test (Run 2)

Output: `sample_outputs/writing_output.txt` (6.8 s)

| Check | Result |
|---|---|
| Used only the promises in the staff notes? | Yes. New delivery Friday before 2 pm and the waived delivery fee, nothing extra. |
| Correct name and reference? | Yes. "Dear John Mensah" and TW-20451. |
| Under 200 words? | Yes, 128 words. |
| Tone | Apologetic and professional, as requested. Apologised for the lack of communication as well as the delay. |
| Comparison | The slower model wrote "tomorrow, Friday", which would be wrong if sent on another day. The lite model wrote just "Friday", which is safer. |

## 4. Summarisation test (Run 2)

Output: `sample_outputs/summary_output.txt` (3.4 s)

| Check | Result |
|---|---|
| Numbers copied exactly? | Yes, all figures match the report. |
| Added anything not in the report? | No new facts. |
| Format followed? | Yes, all four sections. |
| Good | The "Actions / decisions needed" section correctly lists only recommendations (a) and (b), the two that need a board decision. The slower model got this wrong. |
| Problems | The numbers list still has no labels ("4,820", "22%"), so a manager cannot tell what they mean. One line mixes two different things: "Two (broken-down trucks / new corporate clients)". The fuel surcharge complaints from three corporate clients are not in the key points. |

## 5. Findings

**What works well:**
- **Speed (with the lite model):** 2–7 seconds per task, fast enough for real use.
- **Structured output:** valid JSON in all 12 extraction tests across both runs, and the format never broke. Another system could use it directly.
- **No invented facts:** when the name or details were missing, the AI returned null or listed what to ask for.
- **Hard inputs handled:** it understood a long, detailed letter and a poorly written Pidgin message.
- **Non-business messages recognised:** the jollof/football message was correctly marked "Other".
- **Customer replies follow the rules:** the reply promised only what the staff notes said.
- **Summary numbers are accurate:** every figure was copied correctly.
- **Safety net works:** the Python review rules sent 5 of 6 enquiries to a person, including every High urgency case.

**What does not work:**
- **The bigger model was far too slow:** `gemini-3.8-flash` took 3–13 minutes per task (about 44 minutes for 8 tests). Choosing the right model matters as much as writing good prompts.
- **Summary numbers have no labels,** so the list is hard to use.
- **Review rules over-flag:** obvious spam (test 06) still goes to a person.

**Where the AI can make mistakes:**
- **Urgency is a judgement call:** test 01 (late delivery, no phone call) was rated Medium by both models, though a manager might say High. Because of this, it was not sent for review.
- **Guessing on unclear messages:** test 03 was labelled "Complaint" without enough information to know.
- **Acting too early on money:** test 04 recommended a refund before the double charge was checked.
- **Leaving out important details:** the legal threat and the GHS 60,000 order in test 02, and "called 3 times" in test 05, were not captured.
- **Inconsistent confidence:** the two models gave different confidence for the same spam message (Low vs High), so confidence should not be trusted on its own.
- **Mixing up facts in summaries:** one summary line combined two unrelated numbers.

**Where a human must review the output:**
- Every customer reply, before it is sent, especially dates, refunds and fees.
- Every High urgency case (money lost, spoiling goods, legal or contract threats).
- Any action involving money, after checking the real billing records.
- Messages with missing details or an unclear request, so staff can contact the customer.
- Management summaries, to confirm no key decision or risk was left out.

## 6. Improvements for v2

1. Keep `gemini-3.5-flash-lite` as the default model for speed.
2. Change the summary prompt so every number has a label (e.g. "Deliveries in Q3: 4,820").
3. Make urgency rules stricter: a broken promise plus no communication counts as High.
4. Add a `legal_threat` (true/false) field so legal risks are always visible.
5. Send "Other" + "Low" messages to a spam folder instead of human review.
6. Change the recommended action for money cases to "verify first, then refund if confirmed".

## 7. Development log — problems found and how they were fixed

| # | Problem | Cause | Fix | Lesson |
|---|---|---|---|---|
| 1 | App said "GEMINI_API_KEY is not set" even though `.env` contained the key | The app was already running before `.env` was saved; it reads the key only once, at start-up | Exited and restarted the app. Code changed to always load `.env` from the project folder | Configuration is read at start-up, so restart after changing settings |
| 2 | API key was visible in a screenshot | Sharing the screen while `.env` was open | Advised to delete the key and create a new one in Google AI Studio | Never share API keys; `.gitignore` keeps `.env` off GitHub |
| 3 | Responses took about 50 seconds or more | Unknown at first | Added "Working... please wait" and response timing to the app, and asked the model to think less (`thinking_level: low`) | Measure first before guessing |
| 4 | Still slow after the change | Built `speed_test.py`: a one-word reply took 96–136 s, so the problem was not the prompts. The low-thinking setting saved only about 20 s | Tested the faster models available to the key | Isolate the problem with a small test |
| 5 | Full test run took about 44 minutes | `gemini-3.8-flash` was very slow on the free tier | Switched to `gemini-3.5-flash-lite` in `.env`: the same 8 tests took about 25 seconds with similar quality | Model choice is a business decision: speed vs quality vs cost |

### Manual tests done live in the app (gemini-3.5-flash-lite)

| Input | Result | Time |
|---|---|---|
| John Mensah late delivery (TW-20451) | Name, issue, category and action correct. Urgency Medium (a human might say High). No human review triggered | not recorded |
| "I was charged twice... I need my money back." | Name null (not invented), Billing, High, asked for account number and transaction date. Sent to human review for 3 reasons | 3.8 s |

Note: the raw output files from Run 1 were replaced when Run 2 was run; Run 1 results are recorded in the tables above.
