from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.security.encryption import EncryptedString
from app.database import Base

class CareSpecialist(Base):
    __tablename__ = "care_specialists"

    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    specialization = Column(String)
    patients = relationship("Patient", back_populates="care_specialist")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    diagnosis = Column(String)
    tumor_location = Column(String)
    tumor_stage = Column(String)
    treatment_plan = Column(Text)
    notes = Column(Text)
    care_specialist_id = Column(String, ForeignKey("care_specialists.specialist_id"))
    treatment_cycle = Column(Integer, default=1)
    biomarkers = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    care_specialist = relationship("CareSpecialist", back_populates="patients")

class CareSpecialistBase(BaseModel):
    specialist_id: str
    first_name: str
    last_name: str
    email: str
    specialization: str

    class Config:
        from_attributes = True

class PatientCSV(BaseModel):
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
    biomarkers: Optional[str] = None  # Add biomarkers field
    treatment_cycle: Optional[int] = None  # Add treatment cycle field

    class Config:
        from_attributes = True

class PatientResponse(BaseModel):
    id: int
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
    care_specialist_id: str
    created_at: datetime
    treatment_cycle: int
    biomarkers: Optional[str] = None

    class Config:
        from_attributes = True 