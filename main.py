"""
main.py — Simple menu so anyone can use the Transwork Business Assistant
from the terminal. Run:  python main.py
"""

import json
import time

import assistant


def read_multiline(label: str) -> str:
    print(f"{label} (paste text, then type END on a new line and press Enter):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def option_writing():
    name = input("Customer name (or press Enter to skip): ").strip()
    situation = read_multiline("Customer's message / situation")
    notes = input("What will the company do? (staff notes): ").strip()
    tone = input("Tone (press Enter for 'Professional and empathetic'): ").strip()
    print("\nWorking... please wait.")
    start = time.time()
    reply = assistant.draft_customer_response(
        situation=situation,
        staff_notes=notes or "Not provided",
        customer_name=name or "Not provided",
        tone=tone or "Professional and empathetic",
    )
    print(f"\n----- DRAFT REPLY (review before sending) — {time.time() - start:.1f}s -----\n")
    print(reply)


def option_summary():
    document = read_multiline("Document to summarise")
    print("\nWorking... please wait.")
    start = time.time()
    summary = assistant.summarise_document(document)
    print(f"\n----- SUMMARY — {time.time() - start:.1f}s -----\n")
    print(summary)


def option_extract():
    enquiry = read_multiline("Customer enquiry")
    print("\nWorking... please wait.")
    start = time.time()
    result = assistant.extract_enquiry(enquiry)
    print(f"\n----- STRUCTURED OUTPUT (JSON) — {time.time() - start:.1f}s -----\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    print("=" * 50)
    print("  TRANSWORK BUSINESS ASSISTANT v1")
    print(f"  Model: {assistant.MODEL}")
    print("=" * 50)
    actions = {"1": option_writing, "2": option_summary, "3": option_extract}
    while True:
        print("\n1. Draft a customer response")
        print("2. Summarise a document")
        print("3. Extract information from an enquiry")
        print("4. Exit")
        choice = input("Choose 1-4: ").strip()
        if choice == "4":
            print("Goodbye.")
            break
        if choice not in actions:
            print("Please choose 1, 2, 3 or 4.")
            continue
        try:
            actions[choice]()
        except ValueError as err:          # e.g. empty input
            print(f"Input problem: {err}")
        except Exception as err:           # e.g. no internet, bad API key
            print(f"Something went wrong: {err}")


if __name__ == "__main__":
    main()
