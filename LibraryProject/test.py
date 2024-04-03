from fastapi import FastAPI, Response, Path, Query, Body
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# app.mount("/", StaticFiles(directory="templates", html=True))

@app.get("/index")
def read_root():
    html_content = "<h2>Hello WebPython!</h2>"
    return HTMLResponse(content=html_content)

@app.get("/json")
def json_page():
    return {"message": "Hello WebPython!"}

@app.get("/json/encoder")
def json_encoded_page():
    data = {"message": "Hello encoded WebPython!"}
    json_data = jsonable_encoder(data)
    return JSONResponse(content=json_data)

@app.get("/media")
def media_type():
    data = "Hello WebPython!"
    return Response(content=data, media_type="text/plain")

@app.get("/plain")
def plain_text():
    data = "Hello plain WebPython!"
    return PlainTextResponse(content=data)

@app.get("/plain/method", response_class = PlainTextResponse)
def plain_text():
    return "Hello method WebPython!"

# @app.get("/", response_class = FileResponse)
# def root():
#     return "templates/index.html"

# @app.get("/")
# def root():
#     return FileResponse("templates/index.html",
#     filename="mainpage.html",
#     media_type="application/octet-stream")

@app.get("/users/{id}")
def users(id: int):
    return {"user_id": id}

@app.get("/users/{name}/{age}")
def users(name:str = Path(min_length=3, max_length=20), 
          age: int = Path(ge=18, lt=101)):
    return {"name": name, "age": age}

@app.get("/numb/{phone}")
def users(phone:str = Path(regex="^\d{11}$")):       #з 11 цифр.
    return {"phone": phone}

@app.get("/register")       #/register?name=Alex&age=45
def get_model(name:str= Query(default="Undefined", min_length=3, max_length=20), age: int= Query(ge=18, lt=101)):
    return {"user name": name, "user age": age}

@app.get("/people")
def users(people: list[str] = Query()):
    return {"people": people}

@app.get("/old")
def old():
    return RedirectResponse("/new")

@app.get("/new")
def new():
    return PlainTextResponse("New page")

@app.get("/postdata", response_class = FileResponse)
def post_data():
    return "templates/index1.html"

# @app.post("/hello")
# #def hello(name = Body(embed=True)):
# def hello(data = Body()):
#     name = data["name"]
#     age = data["age"]
#     return {"message": f"{name}, your age - {age}"}

@app.post("/hello")
def hello(name:str = Body(embed=True, min_length=3, max_length=20),
        age: int = Body(embed=True, ge=18, lt=101)):
    return {"message": f"{name}, ваш вік - {age}"}