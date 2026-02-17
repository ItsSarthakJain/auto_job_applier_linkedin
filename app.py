from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ast
import csv
from datetime import datetime
import os
from pathlib import Path
import re

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = Path(os.getenv("AJA_EXCEL_DIR", BASE_DIR / "all excels"))
CSV_FILE = CSV_DIR / "all_applied_applications_history.csv"


def _clean_option_text(value: str) -> str:
    cleaned = (value or "").strip()
    # Normalize artifacts like:  "Yes"<Yes>  -> Yes
    cleaned = cleaned.strip('"').strip("'").strip()
    match = re.match(r"^(.*?)(?:<[^>]+>)?$", cleaned)
    if match:
        cleaned = match.group(1).strip()
    cleaned = cleaned.strip('"').strip("'").strip()
    return re.sub(r"\s+", " ", cleaned)


def _split_question_and_options(raw_question: str) -> tuple[str, list[str]]:
    text = (raw_question or "").strip()
    if "[" not in text or "]" not in text:
        return text, []

    try:
        q_text = text[:text.rfind("[")].strip()
        options_blob = text[text.rfind("[") + 1:text.rfind("]")].strip()
        if not options_blob:
            return q_text or text, []
        options = [_clean_option_text(part) for part in options_blob.split(",")]
        options = [opt for opt in options if opt]
        return q_text or text, options
    except Exception:
        return text, []
##> ------ Karthik Sarode : karthik.sarode23@gmail.com - UI for excel files ------
@app.route('/')
def home():
    """Displays the home page of the application."""
    return render_template('index.html')

@app.route('/applied-jobs', methods=['GET'])
def get_applied_jobs():
    '''
    Retrieves a list of applied jobs from the applications history CSV file.
    
    Returns a JSON response containing a list of jobs, each with details such as 
    Job ID, Title, Company, HR Name, HR Link, Job Link, External Job link, and Date Applied.
    
    If the CSV file is not found, returns a 404 error with a relevant message.
    If any other exception occurs, returns a 500 error with the exception message.
    '''

    def parse_questions(raw_questions: str) -> list[dict]:
        raw_questions = (raw_questions or "").strip()
        if not raw_questions:
            return []
        try:
            parsed = ast.literal_eval(raw_questions)
        except Exception:
            return [{"question": "Raw Questions", "answer": raw_questions, "type": "raw", "previous": ""}]

        # "Questions Found" is usually stored as a set of tuples.
        items = parsed if isinstance(parsed, (list, tuple, set)) else [parsed]
        results = []
        for item in items:
            if isinstance(item, (list, tuple)):
                raw_question = str(item[0]).strip() if len(item) > 0 else "Unknown"
                question, options = _split_question_and_options(raw_question)
                answer = _clean_option_text(str(item[1]).strip()) if len(item) > 1 else ""
                q_type = str(item[2]).strip() if len(item) > 2 else ""
                previous = _clean_option_text(str(item[3]).strip()) if len(item) > 3 else ""
                results.append(
                    {
                        "question": question,
                        "raw_question": raw_question,
                        "answer": answer,
                        "type": q_type,
                        "previous": previous,
                        "options": options,
                    }
                )
            else:
                q_text = str(item)
                question, options = _split_question_and_options(q_text)
                results.append(
                    {
                        "question": question,
                        "raw_question": q_text,
                        "answer": "",
                        "type": "",
                        "previous": "",
                        "options": options,
                    }
                )
        return results

    try:
        jobs = []
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                fields = [{"key": k, "value": row.get(k, "")} for k in (reader.fieldnames or [])]
                jobs.append(
                    {
                        "job_id": row.get("Job ID", ""),
                        "title": row.get("Title", ""),
                        "company": row.get("Company", ""),
                        "date_applied": row.get("Date Applied", "Pending"),
                        "external_job_link": row.get("External Job link", ""),
                        "job_link": row.get("Job Link", ""),
                        "hr_name": row.get("HR Name", ""),
                        "hr_link": row.get("HR Link", ""),
                        "questions": parse_questions(row.get("Questions Found", "")),
                        "fields": fields,
                    }
                )
        return jsonify(jobs)
    except FileNotFoundError:
        # Empty state is more UI-friendly than hard 404 for first-time users.
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applied-jobs/<job_id>', methods=['PUT'])
def update_applied_date(job_id):
    """
    Updates the 'Date Applied' field of a job in the applications history CSV file.

    Args:
        job_id (str): The Job ID of the job to be updated.

    Returns:
        A JSON response with a message indicating success or failure of the update
        operation. If the job is not found, returns a 404 error with a relevant
        message. If any other exception occurs, returns a 500 error with the
        exception message.
    """
    try:
        data = []
        if not CSV_FILE.exists():
            return jsonify({"error": f"CSV file not found at {CSV_FILE}"}), 404
            
        # Read current CSV content
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldNames = reader.fieldnames
            found = False
            for row in reader:
                if row['Job ID'] == job_id:
                    row['Date Applied'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    found = True
                data.append(row)
        
        if not found:
            return jsonify({"error": f"Job ID {job_id} not found"}), 404

        with open(CSV_FILE, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldNames)
            writer.writeheader()
            writer.writerows(data)
        
        return jsonify({"message": "Date Applied updated successfully"}), 200
    except Exception as e:
        print(f"Error updating applied date: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)

##<
