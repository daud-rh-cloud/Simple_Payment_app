from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates 
from fastapi import Form 
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

import csv 
import jwt
from datetime import datetime, timedelta , timezone
from  dotenv import load_dotenv 
import os 
 

app = FastAPI()
template = Jinja2Templates(directory="template")

app.mount("/static", StaticFiles(directory="static"), name="static") # browsers request comes at /static/style.css


load_dotenv("seqret.env")
Secret_key = os.environ.get("SECRET_KEY")

 
@app.get("/register")
def register(request : Request):
    return template.TemplateResponse(request=request, name="register.html")



@app.get("/")
@app.get("/login")
def login( request : Request):
    return (template.TemplateResponse(request=request,name="login.html"))



@app.post("/login")
def cheak_cred(request :Request, username:str =Form(), password:str =Form()):
    usernames = {}
    cheakedname = None
    user_id = None #--> (reqire for data fetch)

    with open("username.csv", "r",newline="")as f: 
        for row in csv.DictReader(f):
            if row.get("username") == username:
                cheakedname = username
                user_id = row["id"]
            else :
                continue 

        if cheakedname == None:
            return template.TemplateResponse(request=request, name="login.html",context={"error" : "Wrong username"} )
        
        else :
            f.seek(0)
            for row in csv.DictReader(f):
                if not row.get("username") == cheakedname:
                    continue
                elif row.get("username") == cheakedname:
                    if not row.get("password") == password:
                        return template.TemplateResponse(request=request, name = "login.html",context={"error" : "Wrong Password! Try Again"})   
                             
                    else:
                        # Creatig token = Encode payload + HASH (Payload + Key) 
                        token = jwt.encode(payload={"user_id": user_id,"username" : username, "exp" : datetime.now(timezone.utc)+ timedelta(minutes=20)} , 
                                            key = Secret_key , algorithm="HS256")



                        # create a respoce object + set cokkie (this ask browser to re- request /home page )
                        # We could use template.responce to create Responce object but this will keep the same /login/path in browser. 
                       
                        responce = RedirectResponse(url="/home", status_code=303)   # 303 -> always a GET to the new address
                        responce.set_cookie(key="token", value=token, httponly=True )

                        return responce 



@app.get("/home")
def home(request : Request):

    # Cheak JWT TOKEN 
    try : 
        JWTtoken = request.cookies.get("token") # abstructing the token cookie from Request object 
        payload = jwt.decode(jwt=JWTtoken, key= Secret_key,algorithms=["HS256"])
        username = payload.get("username")
        
    except jwt.InvalidTokenError as e:
        return e 
    
    cheaked_name = None 
    account_number = None 
    balance = None 

    with open ("username.csv", "r", newline="") as f :
        for row in csv.DictReader(f):
            if row.get("username") == username:
                cheaked_name= username 
            else : 
                continue 

        #get the acccount nummer and the balance 
        f.seek(0)
        if not cheaked_name == None : 
            for row in csv.DictReader(f):
                if row.get ("username") == username:
                    account_number = row["account_number"]
                    balance = row["balance"]
                else :
                    continue 

        if account_number is not None and balance is not None:
            return template.TemplateResponse(request=request, name="home.html",context={"username" : cheaked_name, "account_number": account_number, "balance": balance})  





@app.get("/transfer")
def transfer (request : Request):

    # Cheak JWT TOKEN 
    try: 
        JWTtoken = request.cookies.get("token") # Cokkie name was "token" )
        payload = jwt.decode(jwt=JWTtoken, key = Secret_key,algorithms=["HS256"] )
    except jwt.InvalidTokenError as e: 
        return e 

    user_id = payload.get("user_id")
    balance = None  

    with open ("username.csv", "r") as f :
        for row in csv.DictReader(f):
            if row["id"] != user_id:
                continue
            else :
                balance = row["balance"]
                


    return template.TemplateResponse(request=request, name= "transfer.html", context= {"balance" : balance})







@app.post("/transfer") 
def makeTransfer(request : Request, to_account:str =Form(), amount:int  =Form()):   #asking for data which broswer sent in Form 
   
    # Cheak JWT TOKEN 
    try: 
            JWTtoken = request.cookies.get("token") # Cokkie name was "token" )
            payload = jwt.decode(jwt=JWTtoken, key = Secret_key,algorithms=["HS256"] )
    except jwt.InvalidTokenError as e: 
            return e 

    # the app just removes the ammout from the balance. and only +adds to balance if any account matches from the own list!
    user_id = payload.get("user_id")
    to_account = to_account 



    with open ("username.csv", "r") as f :
        for row in csv.DictReader(f):
            if row["id"] != user_id:
                continue
            else :
                row["balance"]  = float (row["balance"])  - amount

        for row in csv.DictReader(f):
            if row["account_number"] != to_account:
                continue
            elif row["account_number"] == to_account: 
                row["balance"] += float (row["balance"]) + amount
            else :
                pass

    return template.TemplateResponse(request=request, name= "transfer.html", context={"success" : "Trasfer has been successfull !"})
    









@app.get("/transactions")
def transactions(request : Request):
    # fetch user id from jwt token, & find all the transections for that  id, sort them with date and return the list 
    
    # Cheak JWT TOKEN 
    try: 
        JWTtoken = request.cookies.get("token") # Cokkie name was "token" )
        payload = jwt.decode(jwt=JWTtoken, key = Secret_key,algorithms=["HS256"] )
    except jwt.InvalidTokenError as e: 
        return e 


    user_id = payload.get("user_id")
    transactions = []

    with open ("transaction.csv", "r", newline="") as f :
        for row in csv.DictReader(f):
            if row["id"] != user_id:
                continue
            else :
                transactions.append({ "date":row["date"], "type":row["type"], "other_account":row["other_account"], "amount":row["amount"]  })

        return template.TemplateResponse(request=request, name = "transactions.html",
             context={"transactions":transactions})
    


