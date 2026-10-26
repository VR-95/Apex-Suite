# Student Performance Analytics System

*An interactive academic performance analysis dashboard built with Python, NumPy, and Pandas.*

## 1. Overview
A local, browser-based Streamlit application that reads student data from a CSV file, validates it, and reports totals, averages, grades, pass/fail statistics, subject/department/attendance analysis and top performers. All calculations live in `functions.py`; `app.py` only displays them.

## 2. Problem statement
Teachers need a quick, reliable way to turn raw marks into meaningful insight without manual spreadsheet work.

## 3. Objectives
Practise variables, loops, functions, conditionals, NumPy and Pandas; compute the required metrics correctly; present them in an easy-to-use interface.

## 4. Technologies
Python 3.10+ (developed and tested on 3.12), NumPy, Pandas, Streamlit (interface), Plotly (charts), Pytest (tests).

## 5. Features
Dashboard metrics and charts · search/filter/sort · per-student profile · subject, department, attendance and grade analysis · CSV upload with full validation · CSV/Markdown report downloads · automated tests.

## 6. GUI pages
| Page | Purpose |
|---|---|
| Dashboard | 9 headline metrics, subject/grade/pass-fail/department charts, top 5 students |
| Student Records | Search by ID/name; filter by department, grade, result, attendance; sort; reset |
| Individual Student | Profile, subject chart vs class average, interpretation |
| Subject Analysis | Average/highest/lowest/median/passing/failing per subject; distribution chart |
| Department Analysis | Students, average, pass/fail, pass %, best department (ties handled) |
| Attendance Analysis | Statistics, students below 75 %, distribution, attendance-vs-marks scatter |
| Grade & Result Analysis | Grade and pass/fail counts, students per grade, highest/lowest performers |
| Dataset Management | Bundled data, CSV upload, validation messages, quality checks, return to default |
| Reports & Downloads | 4 CSV files and a Markdown summary report |

## 7. Dataset schema (`data/students.csv`, 26 fictional students)
`Student_ID` (unique text), `Name`, `Department`, five subject marks `Python, Statistics, NumPy, Pandas, Data_Analysis` (0–100), `Attendance` (0–100). The subject list is defined explicitly in `functions.py` (`SUBJECTS`); Attendance is never treated as a subject.

## 8. Rules (project-defined)
`Total = sum of 5 subjects`, `Average = Total / 5`.

| Average | Grade |
|---|---|
| 90–100 | A+ |
| 80 to <90 | A |
| 70 to <80 | B |
| 60 to <70 | C |
| 50 to <60 | D |
| <50 | F |

**Pass** = average ≥ 40 **and** every subject ≥ 35; otherwise Fail. Consequence: an average of 40–49.99 is graded F but still passes. Attendance (threshold 75 %) never changes the academic result. A subject is "passed" by a student with ≥ 35 in it.

## 9. Folder structure
```
app.py  main.py  functions.py  requirements.txt  pytest.ini  README.md  Project_Documentation.md
data/students.csv   tests/test_analytics.py   outputs/   screenshots/
```

## 10. Installation and running (Windows / VS Code, PowerShell)
Step:1

Using Command Prompt 
Open cmd in project folder  
cd C:\Users\XYZ\Desktop\APEX SUITE\apex-suite

and run 

pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

Step:2

open cmd in backend folder of the project
cd C:\Users\XYZ\Desktop\APEX SUITE\apex-suite\backend

and run

npm run build
npm install
start.bat

and then you will get a localhost link then follow it 

## 11. Testing
```powershell
python -m pytest -q
```
Covers calculations, grade/pass boundaries, ties, validation, filters, exports and GUI pages (Streamlit `AppTest`).

## 12. Downloading reports
Open **Reports & Downloads** and click a button. Files are generated in memory from the active dataset; the source CSV is never modified. The filtered CSV uses the filters set on *Student Records*.

## 13. Troubleshooting
- *`streamlit` not recognised*: run it as `python -m streamlit run app.py` inside the activated venv.
- *Port busy*: Streamlit picks the next port; use the URL it prints.
- *Upload rejected*: read the listed problems (CSV line numbers are given) and fix the file.

## 14. GitHub submission
```powershell
git init
git add .
git commit -m "Student Performance Analytics System"
git branch -M main
git remote add origin https://github.com/<your-username>/student-performance-analytics.git
git push -u origin main
```
Create the empty public repository `student-performance-analytics` on GitHub first, confirm it opens in a private/incognito window, then paste the URL into the EWB Google Form (**your action**).

## 15. Known limitations
Single-file uploads only; one fixed subject list (change `SUBJECTS` to adapt); no persistence of uploaded data between browser sessions; screenshots must be captured by you (see `screenshots/`).
