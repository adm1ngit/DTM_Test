from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Bazani sozlash
DATABASE_URL = "postgresql://postgres:IyemKEneTFbrBaGOSHTtLsHrKUGvjagt@autorack.proxy.rlwy.net:47798/railway"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
