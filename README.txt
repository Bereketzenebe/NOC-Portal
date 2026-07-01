Safaricom Ethiopia NOC Portal — Local Setup
============================================

REQUIREMENTS
  Python 3.10+

INSTALL
  pip install -r requirements.txt

RUN
  uvicorn main:app --reload --port 8000

OPEN
  http://localhost:8000/

CREDENTIALS
  admin    / Admin@NOC2024
  operator / Operator@2024
  guest    / Guest@2024

NOTES
  - PDFs are in the docs/ subfolder
  - All CSV data files are in the same folder as main.py
  - Guest accounts cannot download PDFs
