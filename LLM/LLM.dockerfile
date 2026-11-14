FROM python:3.12-slim

COPY requirements_LLM.txt .
RUN pip install -r requirements_LLM.txt

COPY *.py .

CMD ["uvicorn", "LLM:app", "--host", "0.0.0.0", "--port", "8001"]
