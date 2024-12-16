from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from typing import Dict
from docx import Document
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from io import BytesIO
from PIL import Image

# Bazani sozlash
DATABASE_URL = "postgresql://postgres:IyemKEneTFbrBaGOSHTtLsHrKUGvjagt@autorack.proxy.rlwy.net:47798/railway"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class WordData(Base):
    __tablename__ = "zaybal"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    correct_answer = Column(String)
    category = Column(String, index=True)  # Kategoriya (Asosiy Fan, Fan 1, Fan 2)
    duration = Column(Integer, index=True)  # Davomiylik (30, 60, 90)
    image_path = Column(String)  # Rasmlar yo'li uchun ustun

# Jadvallarni yaratish
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

MEDIA_FOLDER = "media/word_images/"
os.makedirs(MEDIA_FOLDER, exist_ok=True)

@app.post("/process-word/")
async def process_word(
    file: UploadFile = File(...),
    category: str = Form(...),
    duration: int = Form(...),
    db: Session = Depends(get_db)
) -> Dict:
    if duration not in [30, 60, 90]:
        raise HTTPException(status_code=400, detail="Faqat 30, 60 yoki 90 qiymatlari qabul qilinadi")

    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail=f"{file.filename} docx formatda emas")

    try:
        # Faylni vaqtinchalik saqlash
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Word faylni ochish
        doc = Document(temp_file_path)
        questions = []
        correct_answers = []
        image_paths = []

        # Word faylni parchalash
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                question = paragraph.text
                correct_answer = None

                # Qizil rangdagi javoblarni aniqlash
                for run in paragraph.runs:
                    if run.font.color and run.font.color.rgb == (255, 0, 0):  # Qizil rang (RGB)
                        correct_answer = run.text

                # Ma'lumotlarni bazaga yozish
                word_data = WordData(question=question, correct_answer=correct_answer, category=category, duration=duration)
                db.add(word_data)
                db.commit()
                questions.append(question)
                if correct_answer:
                    correct_answers.append(correct_answer)

        # Rasmlarni o'qish va saqlash
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_part = rel.target_part
                image_bytes = BytesIO(image_part.blob)
                image = Image.open(image_bytes)

                # Rasmlarni fayl tizimiga saqlash
                image_filename = f"{file.filename.split('.')[0]}_{rel.target_ref.split('/')[-1]}"
                image_path = os.path.join(MEDIA_FOLDER, image_filename)
                image.save(image_path)
                image_paths.append(image_path)

                # Bazaga yozish
                word_data = WordData(question=None, correct_answer=None, category=category, duration=duration, image_path=image_path)
                db.add(word_data)
                db.commit()

        # Vaqtinchalik faylni o'chirish
        os.remove(temp_file_path)

        return {
            "category": category,
            "duration": duration,
            "questions": questions,
            "correct_answers": correct_answers,
            "image_paths": image_paths
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Xatolik yuz berdi: {str(e)}")