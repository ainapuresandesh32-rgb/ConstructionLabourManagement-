from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    name: Mapped[str]=mapped_column(String(120))
    email: Mapped[str]=mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    mobile: Mapped[str|None]=mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    labours=relationship("Labour", back_populates="owner", cascade="all, delete-orphan")
    sites=relationship("Site", back_populates="owner", cascade="all, delete-orphan")

class Labour(Base):
    __tablename__="labours"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    name: Mapped[str]=mapped_column(String(120))
    mobile: Mapped[str|None]=mapped_column(String(30), nullable=True)
    labour_type: Mapped[str]=mapped_column(String(80))
    skill: Mapped[str]=mapped_column(String(100))
    daily_wage: Mapped[float]=mapped_column(Float, default=0)
    joining_date: Mapped[date]=mapped_column(Date, default=date.today)
    status: Mapped[str]=mapped_column(String(30), default="Active")
    owner=relationship("User", back_populates="labours")
    attendance=relationship("Attendance", back_populates="labour", cascade="all, delete-orphan")
    advances=relationship("Advance", back_populates="labour", cascade="all, delete-orphan")
    payments=relationship("Payment", back_populates="labour", cascade="all, delete-orphan")
    overtime=relationship("Overtime", back_populates="labour", cascade="all, delete-orphan")

class Site(Base):
    __tablename__="sites"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    name: Mapped[str]=mapped_column(String(150))
    client_name: Mapped[str|None]=mapped_column(String(120), nullable=True)
    address: Mapped[str|None]=mapped_column(String(250), nullable=True)
    budget: Mapped[float]=mapped_column(Float, default=0)
    start_date: Mapped[date]=mapped_column(Date, default=date.today)
    completion_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    status: Mapped[str]=mapped_column(String(30), default="Active")
    owner=relationship("User", back_populates="sites")
    assignments=relationship("Assignment", back_populates="site", cascade="all, delete-orphan")

class Assignment(Base):
    __tablename__="assignments"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    labour_id: Mapped[int]=mapped_column(ForeignKey("labours.id"))
    site_id: Mapped[int]=mapped_column(ForeignKey("sites.id"))
    role: Mapped[str]=mapped_column(String(80))
    start_date: Mapped[date]=mapped_column(Date, default=date.today)
    end_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    status: Mapped[str]=mapped_column(String(30), default="Active")
    site=relationship("Site", back_populates="assignments")
    labour=relationship("Labour")

class Attendance(Base):
    __tablename__="attendance"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    labour_id: Mapped[int]=mapped_column(ForeignKey("labours.id"))
    site_id: Mapped[int]=mapped_column(ForeignKey("sites.id"))
    day: Mapped[date]=mapped_column(Date)
    status: Mapped[str]=mapped_column(String(30))
    overtime_hours: Mapped[float]=mapped_column(Float, default=0)
    notes: Mapped[str|None]=mapped_column(Text, nullable=True)
    labour=relationship("Labour", back_populates="attendance")

class Advance(Base):
    __tablename__="advances"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    labour_id: Mapped[int]=mapped_column(ForeignKey("labours.id"))
    amount: Mapped[float]=mapped_column(Float)
    deducted: Mapped[float]=mapped_column(Float, default=0)
    day: Mapped[date]=mapped_column(Date, default=date.today)
    reason: Mapped[str|None]=mapped_column(String(250), nullable=True)
    labour=relationship("Labour", back_populates="advances")

class Payment(Base):
    __tablename__="payments"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    labour_id: Mapped[int]=mapped_column(ForeignKey("labours.id"))
    amount: Mapped[float]=mapped_column(Float)
    day: Mapped[date]=mapped_column(Date, default=date.today)
    method: Mapped[str]=mapped_column(String(40), default="Cash")
    reference: Mapped[str|None]=mapped_column(String(120), nullable=True)
    labour=relationship("Labour", back_populates="payments")

class Overtime(Base):
    __tablename__="overtime"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    labour_id: Mapped[int]=mapped_column(ForeignKey("labours.id"))
    site_id: Mapped[int]=mapped_column(ForeignKey("sites.id"))
    day: Mapped[date]=mapped_column(Date, default=date.today)
    hours: Mapped[float]=mapped_column(Float)
    rate: Mapped[float]=mapped_column(Float)
    reason: Mapped[str|None]=mapped_column(String(250), nullable=True)
    labour=relationship("Labour", back_populates="overtime")
