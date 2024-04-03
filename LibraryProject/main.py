from fastapi import Depends, FastAPI, Body, HTTPException, status, Response, Cookie
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader
from fastapi.openapi.utils import get_openapi
import psycopg2
from contextlib import contextmanager
#connection to postgreSQL

@contextmanager
def connection_pstgr():
    """
    Context manager for establishing a connection to the PostgreSQL database.
    """
    conn = psycopg2.connect(
        dbname="libraryproject",
        host="127.0.0.1",
        user="postgres",
        password="password",
        port="5432"
    )
    cursor = conn.cursor()
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()

app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})     #uvicorn main:app --reloadr

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Library API",
        version="2.2.9",
        summary="This is a very cool Library schema.",
        description="It has a rent function, post method's for all Tables, and Authorisation with Auntification.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://static.vecteezy.com/system/resources/previews/004/852/937/large_2x/book-read-library-study-line-icon-illustration-logo-template-suitable-for-many-purposes-free-vector.jpg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi

@app.get("/", summary="Redirect to login page")
def main():
    """
    Redirect form empty page.
    """
    return RedirectResponse("/login")

def authenticate_user(email: str, password: str):
    """
    Checking in Users table by passed emails to LogIn form.
    """
    with connection_pstgr() as (conn, cursor):
        cursor.execute("SELECT * FROM Users WHERE emailUser = %s", (email,))
        searched_user = cursor.fetchone()
        if searched_user and searched_user['passwordUser'] == password:
            return searched_user
        else:
            return None

@app.get("/login", summary="Login page")
def login_get(email: str | None = Cookie(default=None), password: str | None = Cookie(default=None)):
    """
    Retrieves the login page.
    """
    user = authenticate_user(email, password)
    if user:
        return RedirectResponse("/book-list")
    return FileResponse("templates/login.html")

    
@app.post("/login", summary="Post method for LogIn")
def login(data = Body()):
    """
    Handles the login request.
    """
    email = data.get("emailUser")
    password = data.get("passwordUser")
    with connection_pstgr() as (conn, cursor):
        cursor.execute("SELECT * FROM Users WHERE emailUser = %s", (email))
        searched_user = cursor.fetchone()
    try:
        if searched_user.get("passwordUser") == password:
            response = JSONResponse(content={"message": f"{searched_user}"})
            response.set_cookie(key="email", value=data.get("emailUser"))
            response.set_cookie(key="password", value=data.get("passwordUser"))
            return response
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login failed")
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login failed")

@app.get("/registration", summary="Registration page")
def register_page():
    return FileResponse("templates/registration.html")

@app.post("/registration", summary="Post method for Registration")
def create_user(data = Body()):
    user = User(nameUser=data["nameUser"], surnameUser=data["surnameUser"],
                  passwordUser=data["passwordUser"],emailUser=data["emailUser"],numberUser=data["numberUser"])
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Registration failed")
    response = JSONResponse(content={"message": f"{user}"})
    response.set_cookie(key="email", value=data.get("emailUser"))
    response.set_cookie(key="password", value=data.get("passwordUser"))
    return response

@app.get("/book-list", summary="Books view in library")
def book_list_page(
    db: Session = Depends(get_db),
    email: str | None = Cookie(default=None),
    password: str | None = Cookie(default=None)
):
    user = authenticate_user(db, email, password)
    if user:
        output = render_book_list(db, email, password)
        return HTMLResponse(output)
    else:
        return RedirectResponse("/login")
    
def render_book_list(db: Session, email: str, password: str):
    user = authenticate_user(db, email, password)
    if user.is_admin:
        book_list_page = env.get_template('book-list-roles/admin-book-list.html')
        output = book_list_page.render(
        books=db.query(Book).all(),
        username=email
    )
    else:
        book_list_page = env.get_template('book-list-roles/user-book-list.html')
        output = book_list_page.render(
        books=db.query(Book).all(),
        username=email,
        rents_book_id = [rent.books_id for rent in db.query(History).filter(
            History.user_id == user.id,
            History.isReturned == False
        ).all()]
    )
    return output

@app.get("/book/{book_id}", summary="Get for getting one specific book")
def book_page(book_id, db: Session = Depends(get_db)):
    book =  db.query(Book).filter(Book.id == book_id).first()     # якщо не знайдений, відправляємо статусний код і повідомлення про помилку
    if book==None:
        return JSONResponse(status_code=404, content={ "message": "Книжка не знайдена"})        #якщо користувача знайдено, відправляємо його
    return book

@app.post("/book", summary="Post method for Book")
def book_post_page(email: str| None = Cookie(default=None), password: str | None = Cookie(default=None), book_data = Body(), db: Session = Depends(get_db)):
    book = Book(
        nameBook=book_data.get("nameBook"),
        yearBook=book_data.get("yearBook"),
        availableBook=book_data.get("availableBook"),
        category_id=book_data.get("category_id"),
        author_id=book_data.get("author_id")
    )
    user = authenticate_user(db, email, password)
    if user.is_admin:
        db.add(book)
        db.commit()
        db.refresh(book)
        return book
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
@app.put("/book", summary="Put method for Book")
def edit_book(email: str| None = Cookie(default=None), password: str | None = Cookie(default=None), data = Body(), db: Session = Depends(get_db)):
    user = authenticate_user(db, email, password)
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    # отримуємо book за id
    book = db.query(Book).filter(Book.id == data["id"]).first()
    # якщо не знайдений, відправляємо статусний код і повідомлення про помилку
    if book == None:
        return JSONResponse(status_code=404, content={ "message": "Книжка не знайдена"})
    # якщо book знайдений, змінюємо його дані і відправляємо назад клієнту
    book.nameBook = data["nameBook"]
    book.yearBook = data["yearBook"]
    book.availableBook =  data["availableBook"]
    book.category_id =  data["category_id"]
    book.author_id =  data["author_id"]
    db.commit() # зберігаємо зміни
    db.refresh(book)
    return book

@app.delete("/book/{book_id}", summary="Delete method for Book")
def delete_book(book_id, email: str| None = Cookie(default=None), password: str | None = Cookie(default=None),  db: Session = Depends(get_db)):
    user = authenticate_user(db, email, password)
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    # отримуємо користувача за id
    book = db.query(Book).filter(Book.id == book_id).first()
    # якщо не знайдений, відправляємо статусний код і повідомлення про помилку
    if book == None:
        return JSONResponse( status_code=404, content={ "message": "Книжка не знайдена"})
    # якщо користувача знайдено, видаляємо його
    db.delete(book) # видаляємо об'єкт
    db.commit() # зберігаємо зміни
    return book

@app.post("/book/{book_id}/rent", summary="Renting a book")
def rent_book(
    book_id,
    email: str | None = Cookie(default=None),
    password: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    date_now = datetime.now()
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    # Update existing rental record
    rent = db.query(History).filter(
            History.user_id == user.id,
            History.isReturned == False,
            History.books_id == book_id
        ).first()
    book = db.query(Book).get(book_id)
    if rent:        #returned == False rental rec
        rent.isReturned = True
        rent.dateReturn = date_now
        book.availableBook += 1
        db.commit() # зберігаємо зміни
        db.refresh(rent)
        db.refresh(book)
        return book
    else:       #creating a new rental rec
        # Create new rental record
        rent = History(user_id=user.id, books_id=book_id, dateLoan=date_now, isReturned=False)
        try:
            book.availableBook -= 1
            db.add(rent)
            db.commit()
            db.refresh(rent)
            db.refresh(book)
            return book
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/rents-list", summary="List of Rents")
def book_list_page(
    db: Session = Depends(get_db),
    email: str | None = Cookie(default=None),
    password: str | None = Cookie(default=None)
):
    user = authenticate_user(db, email, password)
    if user:
        output = render_rent_list(db, email, password)
        return HTMLResponse(output)
    else:
        return RedirectResponse("/login")

def render_rent_list(db: Session, email: str, password: str):
    user = authenticate_user(db, email, password)
    if user.is_admin:
        book_list_page = env.get_template('rent-list.html')
        output = book_list_page.render(
        rents = db.query(History).order_by(History.isReturned.asc(), History.dateLoan.desc()).all(),
        username=email
    )
    else:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    return output

@app.post("/authors", summary="Post method for Authors")
def authors_post_page(data: dict = Body(...), db: Session = Depends(get_db)):
    for category_data in data:
        nameAuthor = category_data.get("nameAuthor")
        surnameAuthor = category_data.get("surnameAuthor")
        author = Author(nameAuthor=nameAuthor, surnameAuthor = surnameAuthor)
        db.add(author)
    db.commit()
    db.refresh(author)
    return db.query(Author).all()

@app.post("/categories", summary="Post method for Categories")
def categories_post_page(data: dict = Body(...), db: Session = Depends(get_db)):
    for category_data in data:
        category_name = category_data.get("nameCategory")
        category = Category(nameCategory=category_name)
        db.add(category)
    db.commit()
    db.refresh(category)
    return db.query(Category).all()

@app.post("/book-list", summary="Post method for Books")
def books_post_page(data: dict = Body(...), db: Session = Depends(get_db)):
    for book_data in data:
        book = Book(
            nameBook=book_data.get("nameBook"),
            yearBook=book_data.get("yearBook"),
            availableBook=book_data.get("availableBook"),
            category_id=book_data.get("category_id"),
            author_id=book_data.get("author_id")
        )
        db.add(book)
    db.commit()
    return db.query(Book).all()

@app.get("/clear-cookie", summary="Clearing Cookies")
def clear_cookie(response: Response):
    response.delete_cookie("email")
    response.delete_cookie("password")
    return {"message": "Cookie cleared successfully"}