from sqlalchemy import Column, String, BigInteger, Integer, Float

from src.database import Base


class User(Base):
    __tablename__ = "user"
    id = Column(BigInteger, primary_key=True)
    type = Column(String)
    checking_status = Column(String)
    balance = Column(Float)
