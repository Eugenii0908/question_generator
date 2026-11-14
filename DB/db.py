from fastapi import HTTPException
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, String, JSON, create_engine 
from pydantic import BaseModel, Field, ConfigDict 
import os

llm_url = os.getenv("llm_url", "http://127.0.0.1:8001/responses")

# Класс хранения
class requests_data(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название набора")
    text: str = Field(..., min_length=10, max_length=15000, description="Материалы")
    response: list
    date: str

class requests_data_out(requests_data):
    id: int
    model_config = ConfigDict(from_attributes=True) 

engine = create_engine('sqlite:////app/data/requests.db')

Base = declarative_base()

# Класс таблицы БД
class requests_orm(Base):
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    text= Column(String, nullable=False)
    response= Column(JSON, nullable=False)
    date= Column(String, nullable=False)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

# Создание объекта
def request_insert(data: requests_data):
    data_dict = data.model_dump()
    request = requests_orm(**data_dict)
    with Session() as session:
        session.add(request)
        try:
            session.commit()
            return requests_data_out.model_validate(request)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409, 
                detail=f"Набор с названием '{data.name}' уже существует. Выберите другое имя."
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, 
                detail="Не удалось сохранить данные в базу. Ошибка сервера."
            )

# Получение всех объектов
def all_request_get():
    with Session() as session:
        try:
            request = session.query(requests_orm).all()
            if request == None:
                raise HTTPException(
                status_code=404, 
                detail="Список наборов пуст."
            )
            return request
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail="Не удалось загрузить данные из базы. Ошибка сервера."
            )

# Получение объекта
def request_get(name: str):
    with Session() as session:
        try:
            request = session.query(requests_orm).filter(requests_orm.name == name).first()
            if request == None:
                raise HTTPException(
                status_code=404, 
                detail="Набора с таким именем не существует."
            )
            return request
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail="Не удалось загрузить данные из базы. Ошибка сервера."
            )

# Удаление объекта
def request_delete(name: str):
    with Session() as session:
        try:
            request = session.query(requests_orm).filter(requests_orm.name == name).first()
            if request == None:
                raise HTTPException(
                status_code=404, 
                detail="Набора с таким именем не существует."
            )
            session.delete(request)
            session.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, 
                detail="Не удалось удалить данные. Ошибка сервера."
            )

# Проверка уникальности имени набора
def check_name_exists(name: str):
    with Session() as session:
        request = session.query(requests_orm).filter(requests_orm.name == name).first()
        return request is not None