from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from typing import Dict, List
from docx import Document
import os
from io import BytesIO
from PIL import Image


MEDIA_FOLDER = "media/word_images/"
os.makedirs(MEDIA_FOLDER, exist_ok=True)

app = FastAPI()

@app.post("/process-word/")
async def process_word(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form(...),
    duration: int = Form(...)
) -> Dict:
    if duration not in [30, 60, 90]:
        raise HTTPException(status_code=400, detail="Faqat 30, 60 yoki 90 qiymatlari qabul qilinadi")

    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail=f"{file.filename} docx formatda emas")

    try:
        # Word faylni vaqtinchalik saqlash
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Word faylni ochish
        doc = Document(temp_file_path)
        result = []
        image_counter = 1
        image_refs = {}

        # Rasmlarni aniqlash va saqlash
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_bytes = BytesIO(rel.target_part.blob)
                image = Image.open(image_bytes)

                # Rasmni saqlash
                image_filename = f"image_{image_counter}.png"
                image_path = os.path.join(MEDIA_FOLDER, image_filename)
                image.save(image_path)

                image_refs[rel.target_ref] = image_path
                image_counter += 1

        # Savollarni, variantlarni va javoblarni yig'ish
        paragraphs = iter(doc.paragraphs)
        current_block = {"question": "", "variants": [], "correct_answer": None, "image_path": None}

        for paragraph in paragraphs:
            text = paragraph.text.strip()
            if not text:  
                continue

            if not current_block["question"]:
                current_block["question"] = text
            elif text.startswith(("A)", "B)", "C)", "D)")):
                current_block["variants"].append(text)
                # Qizil rangdagi javobni aniqlash
                for run in paragraph.runs:
                    if run.font.color and run.font.color.rgb == (255, 0, 0):  # Qizil rang (RGB)
                        current_block["correct_answer"] = run.text.strip()
            else:
                # Rasmni aniqlash va bog'lash
                for rel_ref, path in image_refs.items():
                    if rel_ref in paragraph._p.xml:
                        current_block["image_path"] = path

                # To'liq blokni natijaga qo'shish
                if current_block["image_path"] or current_block["correct_answer"]:
                    result.append(current_block)
                    current_block = {"question": text, "variants": [], "correct_answer": None, "image_path": None}

        # Oxirgi blokni qo'shish
        if current_block["question"]:
            result.append(current_block)

        os.remove(temp_file_path)

        return {
            "name": name,
            "category": category,
            "duration": duration,
            "questions": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xatolik yuz berdi: {str(e)}")
