from datetime import date, datetime
from pathlib import Path
import csv, io, os
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
from .models import User, Labour, Site, Assignment, Attendance, Advance, Payment, Overtime
from .auth import hash_password, login_user, logout_user, current_user
from .services.ai_service import ask_ai

Base.metadata.create_all(bind=engine)
app=FastAPI(title="Construction Labour Management System")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET","change-this-secret"))
BASE=Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE/"static"), name="static")
templates=Jinja2Templates(directory=BASE/"templates")

def ctx(request, **kw):
    return {"request":request, **kw}

def require_user(request, db):
    u=current_user(request,db)
    return u

@app.get("/", response_class=HTMLResponse)
def home(request:Request, db:Session=Depends(get_db)):
    return RedirectResponse("/dashboard" if current_user(request,db) else "/login")

@app.get("/login", response_class=HTMLResponse)
def login(request:Request): return templates.TemplateResponse("login.html",ctx(request,error=None))

@app.post("/login")
def login(request:Request, email:str=Form(...), password:str=Form(...), db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==email).first()
    if not u or u.password_hash!=hash_password(password):
        return templates.TemplateResponse("login.html",ctx(request,error="Invalid email or password"))
    login_user(request,u.id); return RedirectResponse("/dashboard",status_code=303)

@app.get("/register", response_class=HTMLResponse)
def register(request:Request): return templates.TemplateResponse("register.html",ctx(request,error=None))

@app.post("/register")
def register_post(request:Request,name:str=Form(...),email:str=Form(...),mobile:str=Form(""),password:str=Form(...),db:Session=Depends(get_db)):
    if db.query(User).filter(User.email==email).first():
        return templates.TemplateResponse("register.html",ctx(request,error="Email already registered"))
    u=User(name=name,email=email,mobile=mobile,password_hash=hash_password(password))
    db.add(u); db.commit(); login_user(request,u.id); return RedirectResponse("/dashboard",status_code=303)

@app.get("/logout")
def logout(request:Request): logout_user(request); return RedirectResponse("/login")

@app.get("/dashboard",response_class=HTMLResponse)
def dashboard(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    total_lab=db.query(Labour).filter_by(owner_id=u.id).count()
    total_sites=db.query(Site).filter_by(owner_id=u.id).count()
    present=db.query(Attendance).join(Labour).filter(Labour.owner_id==u.id,Attendance.day==date.today(),Attendance.status=="Present").count()
    wages=sum(x.daily_wage for x in db.query(Labour).filter_by(owner_id=u.id).all())
    adv=sum(x.amount-x.deducted for x in db.query(Advance).join(Labour).filter(Labour.owner_id==u.id).all())
    pay=sum(x.amount for x in db.query(Payment).join(Labour).filter(Labour.owner_id==u.id).all())
    return templates.TemplateResponse("dashboard.html",ctx(request,user=u,total_lab=total_lab,total_sites=total_sites,present=present,wages=wages,advance=adv,payments=pay))

@app.get("/labour",response_class=HTMLResponse)
def labour_list(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("labour.html",ctx(request,user=u,labours=db.query(Labour).filter_by(owner_id=u.id).order_by(Labour.id.desc()).all()))

@app.post("/labour/add")
def labour_add(request:Request,name:str=Form(...),mobile:str=Form(""),labour_type:str=Form(...),skill:str=Form(...),daily_wage:float=Form(...),db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    db.add(Labour(owner_id=u.id,name=name,mobile=mobile,labour_type=labour_type,skill=skill,daily_wage=daily_wage));db.commit()
    return RedirectResponse("/labour",303)

@app.post("/labour/{lid}/delete")
def labour_delete(request:Request,lid:int,db:Session=Depends(get_db)):
    u=require_user(request,db); x=db.query(Labour).filter_by(id=lid,owner_id=u.id).first()
    if x: db.delete(x);db.commit()
    return RedirectResponse("/labour",303)

@app.get("/sites",response_class=HTMLResponse)
def sites(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("sites.html",ctx(request,user=u,sites=db.query(Site).filter_by(owner_id=u.id).order_by(Site.id.desc()).all()))

@app.post("/sites/add")
def site_add(request:Request,name:str=Form(...),client_name:str=Form(""),address:str=Form(""),budget:float=Form(0),db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    db.add(Site(owner_id=u.id,name=name,client_name=client_name,address=address,budget=budget));db.commit()
    return RedirectResponse("/sites",303)

@app.post("/sites/{sid}/delete")
def site_delete(request:Request,sid:int,db:Session=Depends(get_db)):
    u=require_user(request,db);x=db.query(Site).filter_by(id=sid,owner_id=u.id).first()
    if x:db.delete(x);db.commit()
    return RedirectResponse("/sites",303)

@app.get("/attendance",response_class=HTMLResponse)
def attendance(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    labs=db.query(Labour).filter_by(owner_id=u.id).all(); sites_=db.query(Site).filter_by(owner_id=u.id).all()
    rows=db.query(Attendance).join(Labour).filter(Labour.owner_id==u.id).order_by(Attendance.day.desc()).limit(100).all()
    return templates.TemplateResponse("attendance.html",ctx(request,user=u,labours=labs,sites=sites_,rows=rows))

@app.post("/attendance/add")
def attendance_add(request:Request,labour_id:int=Form(...),site_id:int=Form(...),status:str=Form(...),overtime_hours:float=Form(0),db:Session=Depends(get_db)):
    u=require_user(request,db)
    lab=db.query(Labour).filter_by(id=labour_id,owner_id=u.id).first(); site=db.query(Site).filter_by(id=site_id,owner_id=u.id).first()
    if lab and site:
        existing=db.query(Attendance).filter_by(labour_id=labour_id,site_id=site_id,day=date.today()).first()
        if not existing: db.add(Attendance(labour_id=labour_id,site_id=site_id,day=date.today(),status=status,overtime_hours=overtime_hours));db.commit()
    return RedirectResponse("/attendance",303)

@app.get("/salary",response_class=HTMLResponse)
def salary(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    labs=db.query(Labour).filter_by(owner_id=u.id).all()
    data=[]
    for l in labs:
        att=db.query(Attendance).filter_by(labour_id=l.id).all()
        present=sum(1 for a in att if a.status=="Present")
        half=sum(.5 for a in att if a.status=="Half Day")
        ot=sum(a.overtime_hours for a in att)
        gross=(present+half)*l.daily_wage
        adv=sum(a.amount-a.deducted for a in l.advances)
        paid=sum(p.amount for p in l.payments)
        data.append({"labour":l,"present":present,"half":half,"ot":ot,"gross":gross,"advance":adv,"paid":paid,"net":max(gross-adv-paid,0)})
    return templates.TemplateResponse("salary.html",ctx(request,user=u,data=data))

@app.get("/payments",response_class=HTMLResponse)
def payments(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("payments.html",ctx(request,user=u,labours=db.query(Labour).filter_by(owner_id=u.id).all(),payments=db.query(Payment).join(Labour).filter(Labour.owner_id==u.id).order_by(Payment.day.desc()).all()))

@app.post("/payments/add")
def payment_add(request:Request,labour_id:int=Form(...),amount:float=Form(...),method:str=Form(...),reference:str=Form(""),db:Session=Depends(get_db)):
    u=require_user(request,db); lab=db.query(Labour).filter_by(id=labour_id,owner_id=u.id).first()
    if lab: db.add(Payment(labour_id=labour_id,amount=amount,method=method,reference=reference));db.commit()
    return RedirectResponse("/payments",303)

@app.get("/advance",response_class=HTMLResponse)
def advance(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("advance.html",ctx(request,user=u,labours=db.query(Labour).filter_by(owner_id=u.id).all(),advances=db.query(Advance).join(Labour).filter(Labour.owner_id==u.id).order_by(Advance.day.desc()).all()))

@app.post("/advance/add")
def advance_add(request:Request,labour_id:int=Form(...),amount:float=Form(...),reason:str=Form(""),db:Session=Depends(get_db)):
    u=require_user(request,db); lab=db.query(Labour).filter_by(id=labour_id,owner_id=u.id).first()
    if lab: db.add(Advance(labour_id=labour_id,amount=amount,reason=reason));db.commit()
    return RedirectResponse("/advance",303)

@app.get("/overtime",response_class=HTMLResponse)
def overtime(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("overtime.html",ctx(request,user=u,labours=db.query(Labour).filter_by(owner_id=u.id).all(),sites=db.query(Site).filter_by(owner_id=u.id).all(),rows=db.query(Overtime).join(Labour).filter(Labour.owner_id==u.id).order_by(Overtime.day.desc()).all()))

@app.post("/overtime/add")
def overtime_add(request:Request,labour_id:int=Form(...),site_id:int=Form(...),hours:float=Form(...),rate:float=Form(...),reason:str=Form(""),db:Session=Depends(get_db)):
    u=require_user(request,db); lab=db.query(Labour).filter_by(id=labour_id,owner_id=u.id).first(); site=db.query(Site).filter_by(id=site_id,owner_id=u.id).first()
    if lab and site: db.add(Overtime(labour_id=labour_id,site_id=site_id,hours=hours,rate=rate,reason=reason));db.commit()
    return RedirectResponse("/overtime",303)

@app.get("/assignments",response_class=HTMLResponse)
def assignments(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    labs=db.query(Labour).filter_by(owner_id=u.id).all(); sites_=db.query(Site).filter_by(owner_id=u.id).all()
    rows=db.query(Assignment).join(Labour).filter(Labour.owner_id==u.id).order_by(Assignment.id.desc()).all()
    return templates.TemplateResponse("assignments.html",ctx(request,user=u,labours=labs,sites=sites_,rows=rows))

@app.post("/assignments/add")
def assignment_add(request:Request,labour_id:int=Form(...),site_id:int=Form(...),role:str=Form(...),db:Session=Depends(get_db)):
    u=require_user(request,db); lab=db.query(Labour).filter_by(id=labour_id,owner_id=u.id).first(); site=db.query(Site).filter_by(id=site_id,owner_id=u.id).first()
    if lab and site: db.add(Assignment(labour_id=labour_id,site_id=site_id,role=role));db.commit()
    return RedirectResponse("/assignments",303)

@app.get("/reports")
def reports(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    labs=db.query(Labour).filter_by(owner_id=u.id).all()
    rows=[]
    for l in labs:
        att=db.query(Attendance).filter_by(labour_id=l.id).all()
        p=sum(1 for a in att if a.status=="Present"); h=sum(.5 for a in att if a.status=="Half Day")
        rows.append([l.name,l.labour_type,p,h,(p+h)*l.daily_wage])
    out=io.StringIO(); w=csv.writer(out); w.writerow(["Labour","Type","Present Days","Half Days","Estimated Wage"]);w.writerows(rows)
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=labour_report.csv"})

@app.get("/ai",response_class=HTMLResponse)
def ai_page(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("ai.html",ctx(request,user=u,answer=None))

@app.post("/ai",response_class=HTMLResponse)
def ai_post(request:Request,question:str=Form(...),db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    labs=db.query(Labour).filter_by(owner_id=u.id).all();sites_=db.query(Site).filter_by(owner_id=u.id).all()
    context={"labours":[{"name":x.name,"type":x.labour_type,"skill":x.skill,"wage":x.daily_wage} for x in labs],
             "sites":[{"name":x.name,"budget":x.budget,"status":x.status} for x in sites_]}
    answer=ask_ai(question,context)
    return templates.TemplateResponse("ai.html",ctx(request,user=u,answer=answer))

@app.get("/profile",response_class=HTMLResponse)
def profile(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db)
    if not u:return RedirectResponse("/login")
    return templates.TemplateResponse("profile.html",ctx(request,user=u))
