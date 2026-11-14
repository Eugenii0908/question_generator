from fastapi import FastAPI, HTTPException, File, UploadFile 
from DB import db
import os
import requests
from pydantic import BaseModel, Field
import json
from fastapi.responses import FileResponse
from pypdf import PdfReader
from io import BytesIO
from docx import Document

class user_data(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название набора")
    text: str = Field(..., min_length=10, max_length=15000, description="Материалы")
    num_questions: int = Field(..., ge=1, le=15, description="Количество вопросов")

# Создаем приложение
app = FastAPI()    
url_llm = os.getenv("llm_url","http://localhost:8001/responses")

# Интерфейс
@app.get("/")
def read_root():
    return FileResponse("interface.html")
    
# Работа с файлами
@app.post("/files")
def upload_pdf(file: UploadFile = File(...)):
    name = file.filename.lower()
    text = ""
    if name.endswith(".pdf"):
        contents = file.file.read()
        reader = PdfReader(BytesIO(contents))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + '\n'
    elif name.endswith(".docx"):
        contents = file.file.read()
        doc = Document(BytesIO(contents))
        for page in doc.paragraphs:
            extracted = page.text
            if extracted:
                text += extracted + '\n'
    else:
        raise HTTPException(status_code=400, detail="Поддерживаются только форматы .pdf и .docx")
    if len(text) < 11:
        raise HTTPException(status_code=400, detail="Не удалось извлечь текст. Возможно, это сканы (картинки).")
    return {"text": text}

# Создание записи в бд
@app.post("/request")
def post(user_request: user_data):
    if db.check_name_exists(user_request.name):
        raise HTTPException(status_code=409, detail="Набор с таким названием уже существует. Введите другое.")
    try:
        r = requests.post(url_llm, json={"text": user_request.text, "num_questions": user_request.num_questions})
        r.raise_for_status()
        llm_data = r.json()
        request = db.requests_data(name=user_request.name, text=user_request.text, response=llm_data["response"], date=llm_data["response_date"])
        new_request = db.request_insert(request)
        return new_request
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM сервис не отвечает более 5 минут.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Не удалось подключиться к LLM сервису.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Сервис вернул неверный формат JSON. Повторите попытку.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Получение всех записей из бд
@app.get("/request")
def get_all():
    request = db.all_request_get()
    return request

# Получение записи из бд
@app.get("/request/{name}")
def get(name: str):
    request = db.request_get(name)
    return request

# Удаление записи из бд
@app.delete("/request/{name}")
def delete(name: str):
    success = db.request_delete(name)
    if success:
        return {"ok": True, "message": "Набор удален."}