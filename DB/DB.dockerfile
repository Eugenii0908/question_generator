FROM python:3.12-slim

COPY requirements_DB.txt .
RUN pip install -r requirements_DB.txt

RUN mkdir DB

COPY db.py ./DB/

COPY main.py .
COPY interface.html .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]