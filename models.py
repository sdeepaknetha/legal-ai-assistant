from sqlalchemy import Column, Integer, String
from database import Base

class LegalSection(Base):
    __tablename__ = "legal_sections"

    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, unique=True, index=True)
    crime = Column(String)
    punishment = Column(String)