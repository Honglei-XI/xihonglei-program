from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from config import Base

class User(Base):
    __tablename__ = "user"
    
    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    name = Column(String(50))
    password = Column(String(100))
    userStatus = Column(Integer)
    phone = Column(String(20))
    email = Column(String(100))
    createTime = Column(DateTime)
    updateTime = Column(DateTime)

class Patient(Base):
    __tablename__ = "patient"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    age = Column(String(10))
    male = Column(String(10))
    phone = Column(String(20))
    address = Column(String(200))
    doctorId = Column(String(50))
    departmentId = Column(String(50))
    diagnosis = Column(String(200))
    text = Column(String(500))
    createTime = Column(Date)
    updateTime = Column(Date)

class Todo(Base):
    __tablename__ = "todo"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(500))
    time = Column(DateTime)
    type = Column(String(50))
    completed = Column(Boolean)
    userId = Column(Integer)
    createTime = Column(DateTime)
    updateTime = Column(DateTime)

class Notification(Base):
    __tablename__ = "notification"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    title = Column(String(100))
    content = Column(String(500))
    createTime = Column(DateTime)
    updateTime = Column(DateTime)

class EegRecord(Base):
    __tablename__ = "eeg_record"
    
    id = Column(Integer, primary_key=True, index=True)
    patientId = Column(Integer)
    fileName = Column(String(200))
    fileUrl = Column(String(500))
    analysisResult = Column(String(1000))
    createTime = Column(DateTime)
    updateTime = Column(DateTime)

class Ward(Base):
    __tablename__ = "ward"
    
    id = Column(Integer, primary_key=True, index=True)
    roomNo = Column(String(50))
    bedCount = Column(Integer)
    doctor = Column(String(50))
    nurse = Column(String(50))
    status = Column(String(20))
    createTime = Column(DateTime)
    updateTime = Column(DateTime)
