import requests
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os

# Создаем приложение
app = FastAPI()

# Параметры ollama
ollama_url = os.getenv("ollama_url", "http://localhost:11434/api/generate")
ollama_model = "qwen3.5:4b"

# Класс запроса
class llm_request(BaseModel):
    text: str = Field(..., min_length=10, max_length=15000, description="Материалы")
    num_questions: int = Field(..., ge=1, le=15, description="Количество вопросов")

# Запрос LLM
@app.post("/responses")
def post(data: llm_request):
    response, response_date = make_prompt(data.text, data.num_questions)
    request_out = {"response": response, "response_date": response_date}
    return request_out

# Функция создания промпта
def make_prompt(text, num_questions):
    # Обертка для текста
    modified_text = f"""Ты — полезный ассистент. Твоя задача — составить ровно {num_questions} вопросов и ответов по тексту ниже.
    Выведи результат СТРОГО в формате JSON-массива, без лишнего текста.
    Формат:
    [
    {{"question": "Текст вопроса1", "answer": "Текст ответа1"}},
    {{"question": "Текст вопроса2", "answer": "Текст ответа2"}}
    ]
    Текст для анализа:
    {text}"""
    prompt = {
        "model": ollama_model,
        "prompt": modified_text,
        "stream": False,
        "think": False
    }
    try:
        # Запрос
        response = requests.post(ollama_url, json=prompt, timeout = 300)
        response.raise_for_status()
        response_data = response.json() # Преобразование в json
        raw_response = response_data.get("response")
        response_date = response_data.get("created_at")
        questions_list = json.loads(raw_response) # Преобразование в список
        return questions_list, response_date
        # Ошибки
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Ollama не отвечает более 5 минут.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Не удалось подключиться к Ollama.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Модель вернула неверный формат JSON. Повторите попытку.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))