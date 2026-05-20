from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import os

DB_URL = "sqlite:///./aoc.db"

Base = declarative_base()

class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    normalised_name = Column(String, unique=True, index=True, nullable=False)
    
    inputs = relationship("Input", back_populates="participant")
    solutions = relationship("Solution", back_populates="participant")

class Input(Base):
    __tablename__ = "inputs"
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    day = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    participant = relationship("Participant", back_populates="inputs")
    results = relationship("Result", back_populates="input")

class Solution(Base):
    __tablename__ = "solutions"
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    day = Column(Integer, nullable=False)
    part = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    language_id = Column(Integer, nullable=False)
    uuid = Column(String, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    participant = relationship("Participant", back_populates="solutions")
    results = relationship("Result", back_populates="solution")

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    solution_id = Column(Integer, ForeignKey("solutions.id"), nullable=False)
    input_id = Column(Integer, ForeignKey("inputs.id"), nullable=False)
    execution_time = Column(Float)
    status = Column(String)
    stdout = Column(Text)
    stderr = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    solution = relationship("Solution", back_populates="results")
    input = relationship("Input", back_populates="results")

from sqlalchemy import create_engine
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
