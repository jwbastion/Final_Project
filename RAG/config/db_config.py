import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DB_URI")
engine = create_engine(DB_URI, echo=False)
Session = sessionmaker(bind=engine)