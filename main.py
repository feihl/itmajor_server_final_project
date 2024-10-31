from fastapi import FastAPI, HTTPException, UploadFile, File
from models import User, Subject, ToDo, FileData, Album, Picture
import sqlite3
from datetime import datetime
import random
import string
import qrcode
from io import BytesIO
from typing import List



server = FastAPI()

####################################
#connection of the database
con = sqlite3.connect("SmartStudyPlanner.db", check_same_thread=False)
cursor = con.cursor()

#################################################
#creating database
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    profile_picture BLOB,
    qr_code BLOB
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    day VARCHAR(255) NOT NULL,
    time TIME NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY,
    task VARCHAR(255) NOT NULL,
    deadline DATE NOT NULL,
    completed BOOLEAN NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(255) NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY,
    user_id INT NOT NULL,
    album_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pictures (
    id INTEGER PRIMARY KEY,
    album_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    FOREIGN KEY (album_id) REFERENCES albums(id)
);
""")
########################################
#generate username
def generate_unique_username():
    cursor = con.cursor()
    
    while True:
        username = "@user" + ''.join(random.choices(string.digits, k=6))
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if cursor.fetchone()[0] == 0:
            break
    return username

################################################
#R  E  G  I  S  T  E  R
@server.post("/api/register/", response_model=User)
async def register(register: User):
    username = generate_unique_username()
    cursor = con.cursor()

    insert_query = "INSERT INTO users (username, firstname, lastname, email, password) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(insert_query, (username, register.firstname, register.lastname, register.email, register.password))
    con.commit()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()
    
    cursor.close()

    return {
        "id": user_id[0],
        "username": username,
        "firstname": register.firstname,
        "lastname": register.lastname,
        "email": register.email,
        "password": register.password,
        "message": "Registered Successfully"
    }


######################################################
#L O G I N
@server.post("/api/login/")
async def login(email: str, password: str):
    cursor = con.cursor()
    
    cursor.execute("SELECT id, username, firstname, lastname, email FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return {
            "id": user[0],
            "username": user[1],
            "firstname": user[2],
            "lastname": user[3],
            "email": user[4],
            "message": "Login Successful"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")


########################################################
@server.put("/users/{user_id}", response_model=User)
async def update_username(user_id: int, new_username: str):
    
    cursor = con.cursor()
    update_query = "UPDATE users SET username = ? WHERE id = ?;"



    cursor.execute(update_query, (new_username, user_id))
    con.commit()
    cursor.close()
    con.close()
    return User(id=user_id, username=new_username)

################################################
# Upload Users Profile Picture
@server.post("/users/{user_id}/profile_picture/")
async def upload_profile_picture(user_id: int, file: UploadFile = File(...)):
    
    cursor = con.cursor()
    file_data = file.file.read()
    update_query = "UPDATE users SET profile_picture = ? WHERE id = ?;"
    cursor.execute(update_query, (file_data, user_id))
    con.commit()
    cursor.close()
    con.close()
    return {"filename": file.filename}

################################################
# QR Code to Share
@server.post("/users/{user_id}/qr_code/")
async def generate_qr_code(user_id: int):
    
    cursor = con.cursor()

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"User ID: {user_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    byte_io = BytesIO()
    img.save(byte_io, format='PNG')
    qr_code_data = byte_io.getvalue()

    update_query = "UPDATE users SET qr_code = ? WHERE id = ?;"
    cursor.execute(update_query, (qr_code_data, user_id))
    con.commit()
    
    return {"message": "QR code generated and saved successfully"}

################################################
# Subject Scheduler
@server.post("/subjects/", response_model=Subject)
async def create_subject(subject: Subject):
    
    cursor = con.cursor()
    insert_query = "INSERT INTO subjects (name, day, time) VALUES (?, ?, ?);"
    cursor.execute(insert_query, (subject.name, subject.day, subject.time))
    con.commit()
    cursor.close()
    con.close()
    return subject


@server.put("/subjects/{subject_id}", response_model=Subject)
async def update_subject(subject_id: int, updated_subject: Subject):
    
    cursor = con.cursor()
    update_query = "UPDATE subjects SET name = ?, day = ?, time = ? WHERE id = ?;"
    cursor.execute(update_query, (updated_subject.name, updated_subject.day, updated_subject.time, subject_id))
    con.commit()
    cursor.close()
    con.close()
    return updated_subject

@server.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: int):
    
    cursor = con.cursor()
    delete_query = "DELETE FROM subjects WHERE id = ?;"
    cursor.execute(delete_query, (subject_id,))
    con.commit()
    cursor.close()
    con.close()
    return {"message": "Subject deleted successfully"}

################################################
# To-Do List
@server.post("/todos/", response_model=ToDo)
async def create_todo(todo: ToDo):
    
    cursor = con.cursor()
    insert_query = "INSERT INTO todos (task, deadline, completed) VALUES (?, ?, ?);"
    cursor.execute(insert_query, (todo.task, todo.deadline, todo.completed))
    con.commit()
    cursor.close()
    con.close()
    return todo

@server.get("/todos/", response_model=List[ToDo])
async def get_todos():
    
    cursor = con.cursor()
    select_query = "SELECT id, task, deadline, completed FROM todos;"
    cursor.execute(select_query)
    results = cursor.fetchall()
    cursor.close()
    con.close()
    return [ToDo(id=row[0], task=row[1], deadline=row[2], completed=row[3]) for row in results]

@server.put("/todos/{todo_id}", response_model=ToDo)
async def update_todo(todo_id: int, updated_todo: ToDo):
    
    cursor = con.cursor()
    update_query = "UPDATE todos SET task = ?, deadline = ?, completed = ? WHERE id = ?;"
    cursor.execute(update_query, (updated_todo.task, updated_todo.deadline, updated_todo.completed, todo_id))
    con.commit()
    cursor.close()
    con.close()
    return updated_todo

@server.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    
    cursor = con.cursor()
    delete_query = "DELETE FROM todos WHERE id = ?;"
    cursor.execute(delete_query, (todo_id,))
    con.commit()
    cursor.close()
    con.close()
    return {"message": "Task deleted successfully"}

################################################
# File Manager
@server.post("/files/")
async def upload_file(file: UploadFile = File(...)):
    
    cursor = con.cursor()
    insert_query = "INSERT INTO files (filename, file_type) VALUES (?, ?);"
    cursor.execute(insert_query, (file.filename, file.content_type))
    con.commit()
    
    cursor.execute("SELECT id FROM files WHERE filename = ?", (file.filename,))
    file_id = cursor.fetchone()[0]
    
    cursor.close()
    con.close()
    return {"filename": file.filename, "file_type": file.content_type, "id": file_id}

@server.get("/files/", response_model=List[FileData])
async def get_files():
    
    cursor = con.cursor()
    select_query = "SELECT id, filename, file_type FROM files;"
    cursor.execute(select_query)
    results = cursor.fetchall()
    cursor.close()
    con.close()
    return [FileData(id=row[0], filename=row[1], file_type=row[2]) for row in results]

@server.delete("/files/{file_id}")
async def delete_file(file_id: int):
    
    cursor = con.cursor()
    delete_query = "DELETE FROM files WHERE id = ?;"
    cursor.execute(delete_query, (file_id,))
    con.commit()
    cursor.close()
    con.close()
    return {"message": "File deleted successfully"}

################################################
# Album Manager
@server.post("/albums/", response_model=Album)
async def create_album(album: Album):
    
    cursor = con.cursor()
    insert_query = "INSERT INTO albums (user_id, album_name) VALUES (?, ?);"
    cursor.execute(insert_query, (album.user_id, album.album_name))
    con.commit()

    cursor.execute("SELECT id FROM albums WHERE user_id = ? AND album_name = ?", (album.user_id, album.album_name))
    album_id = cursor.fetchone()[0]
    
    cursor.close()
    con.close()
    return Album(id=album_id, user_id=album.user_id, album_name=album.album_name)

@server.get("/albums/{album_id}", response_model=Album)
async def get_album(album_id: int):
    
    cursor = con.cursor()
    select_query = "SELECT id, user_id, album_name FROM albums WHERE id = ?;"
    cursor.execute(select_query, (album_id,))
    result = cursor.fetchone()
    
    if result:
        album = Album(id=result[0], user_id=result[1], album_name=result[2])
        cursor.close()
        con.close()
        return album
    else:
        cursor.close()
        con.close()
        raise HTTPException(status_code=404, detail="Album not found")

################################################
# Upload Picture
@server.post("/albums/{album_id}/pictures/")
async def upload_picture(album_id: int, file: UploadFile = File(...)):
    
    cursor = con.cursor()
    insert_query = "INSERT INTO pictures (album_id, filename) VALUES (?, ?);"
    cursor.execute(insert_query, (album_id, file.filename))
    con.commit()
    
    cursor.execute("SELECT id FROM pictures WHERE album_id = ? AND filename = ?", (album_id, file.filename))
    picture_id = cursor.fetchone()[0]
    
    cursor.close()
    con.close()
    return {"filename": file.filename, "id": picture_id}

@server.get("/albums/{album_id}/pictures/", response_model=List[Picture])
async def get_pictures(album_id: int):
    
    cursor = con.cursor()
    select_query = "SELECT id, album_id, filename FROM pictures WHERE album_id = ?;"
    cursor.execute(select_query, (album_id,))
    results = cursor.fetchall()
    cursor.close()
    con.close()
    return [Picture(id=row[0], album_id=row[1], filename=row[2]) for row in results]

@server.delete("/pictures/{picture_id}")
async def delete_picture(picture_id: int):
    
    cursor = con.cursor()
    delete_query = "DELETE FROM pictures WHERE id = ?;"
    cursor.execute(delete_query, (picture_id,))
    con.commit()
    cursor.close()
    con.close()
    return {"message": "Picture deleted successfully"}