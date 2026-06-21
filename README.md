# Recall — Adaptive Revision Platform

A multi-user Flask web app for OCR A Level Computer Science (H446) coursework.
Teachers set multiple-choice questions; students answer them; an adaptive
algorithm keeps serving each student the questions they are weakest at.

## Run it locally

1. Install Python 3.

2. From this folder, install the libraries:

   ```
   pip install -r requirements.txt
   ```

3. Start the app:

   ```
   python app.py
   ```

4. Open the address it prints (usually http://127.0.0.1:5000) in a browser.

The database is created automatically as `instance/recall.db` the first time
you run it, and is filled with demo content.

## Demo logins

- Teacher:  `teacher` / `teacher123`
- Student:  `student` / `student123`

## Run the tests

```
python -m unittest discover -s tests
```

## What each file does

- `app.py` — the Flask application and all the pages (routes).
- `models.py` — the five database tables.
- `adaptive.py` — the adaptive (Leitner + weighted selection) algorithm.
- `reporting.py` — works out percentage scores per topic.
- `seed_data.py` — adds demo accounts and questions to a new database.
- `templates/` — the HTML pages.
- `static/style.css` — the single stylesheet.
- `tests/test_adaptive.py` — automatic tests for the algorithm and scoring.

## Deploying / sharing online

This project is designed to be built and run in **GitHub Codespaces**. To let a
stakeholder test the running app, open the **PORTS** tab in your Codespace, set
port 5000 to **Public**, and share the forwarded URL. See Lesson 8 of the build
manual for the full step-by-step.
