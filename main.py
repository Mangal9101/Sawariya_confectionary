from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User, Product
from passlib.context import CryptContext

app = FastAPI(title="Sawariya Confectionary")
# app.add_middleware(SessionMiddleware, secret_key="change-this-secret-key")
app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-secret-key",
    https_only=True,
    same_site="lax"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def seed_users():
    db = next(get_db())
    if db.query(User).count() == 0:
        users = [
            User(username="Vishal", password_hash=pwd_context.hash("vishal123")),
            User(username="Mangal", password_hash=pwd_context.hash("mangal123")),
            User(username="Sachin", password_hash=pwd_context.hash("sachin123")),
        ]
        db.add_all(users)
        db.commit()
    db.close()

seed_users()

def current_user(request: Request):
    return request.session.get("username")

# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if current_user(request):
        return RedirectResponse("/products", status_code=303)
    # return templates.TemplateResponse("login.html", {"request": request, "error": None})
    return templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"error": None}
)

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
    #     return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
    # request.session["username"] = username
        return templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"error": "Invalid username or password"}
)
    return RedirectResponse("/products", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/products", response_class=HTMLResponse)
def products(request: Request, q: str = "", db: Session = Depends(get_db)):
    if not current_user(request):
        return RedirectResponse("/login", status_code=303)
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    products = query.order_by(Product.id.desc()).all()
    # return templates.TemplateResponse(
    #     "products.html",
    #     {"request": request, "products": products, "q": q, "username": current_user(request)}
    # )
    return templates.TemplateResponse(
    request=request,
    name="products.html",
    context={
        "products": products,
        "q": q,
        "username": current_user(request)
    }
)

@app.post("/products/add")
def add_product(request: Request, name: str = Form(...), quantity: int = Form(...),
                wholesale_price: float = Form(...), retailer_price: float = Form(...),
                db: Session = Depends(get_db)):
    if not current_user(request):
        return RedirectResponse("/login", status_code=303)
    db.add(Product(name=name.strip(), quantity=quantity,
                   wholesale_price=wholesale_price, retailer_price=retailer_price))
    db.commit()
    return RedirectResponse("/products", status_code=303)

@app.post("/products/{product_id}/update")
def update_product(request: Request, product_id: int, name: str = Form(...), quantity: int = Form(...),
                   wholesale_price: float = Form(...), retailer_price: float = Form(...),
                   db: Session = Depends(get_db)):
    if not current_user(request):
        return RedirectResponse("/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.name = name.strip()
    product.quantity = quantity
    product.wholesale_price = wholesale_price
    product.retailer_price = retailer_price
    db.commit()
    return RedirectResponse("/products", status_code=303)

@app.post("/products/{product_id}/delete")
def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    if not current_user(request):
        return RedirectResponse("/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse("/products", status_code=303)
