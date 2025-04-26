from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from sqlalchemy.sql import func
from ..database import Base

class CareSpecialist(Base):
    __tablename__ = "care_specialists"

    specialist_id = Column(String, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    specialization = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    patients = relationship("Patient", back_populates="care_specialist")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    diagnosis = Column(String)
    tumor_location = Column(String)
    tumor_stage = Column(String)
    treatment_plan = Column(String)
    notes = Column(String)
    specialist_id = Column(String, ForeignKey("care_specialists.specialist_id"))
    biomarkers = Column(String)
    treatment_cycle = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    care_specialist = relationship("CareSpecialist", back_populates="patients")

class CareSpecialistBase(BaseModel):
    specialist_id: str
    first_name: str
    last_name: str
    email: str
    specialization: str

    class Config:
        orm_mode = True

class PatientCSV(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    diagnosis: str
    tumor_location: str
    tumor_stage: str
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    specialist_id: str
    biomarkers: Optional[str] = None
    treatment_cycle: Optional[int] = None

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    diagnosis: str
    tumor_location: str
    tumor_stage: str
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    specialist_id: str
    biomarkers: Optional[str] = None
    treatment_cycle: int
    created_at: datetime
    updated_at: Optional[datetime] = None 