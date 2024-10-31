from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class User(BaseModel):
#    id: Optional[int]
    username: str
    firstname: str
    lastname: str
    email: str
    password: str

class Subject(BaseModel):
    id: Optional[int]
    name: str
    day: str
    time: time

    class Config:
        orm_mode = True

class ToDo(BaseModel):
    id: Optional[int]
    task: str
    deadline: date
    completed: bool

    class Config:
        orm_mode = True

class FileData(BaseModel):
    id: Optional[int]
    filename: str
    file_type: str

    class Config:
        orm_mode = True

class Album(BaseModel):
    id: Optional[int]
    user_id: int
    album_name: str

    class Config:
        orm_mode = True

class Picture(BaseModel):
    id: Optional[int]
    album_id: int
    filename: str

    class Config:
        orm_mode = True