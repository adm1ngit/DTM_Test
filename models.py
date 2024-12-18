from docx import Document
from io import BytesIO
from PIL import Image
import os

# Media fayllarni saqlash uchun papka
MEDIA_FOLDER = "media/word_images/"
os.makedirs(MEDIA_FOLDER, exist_ok=True)

def extract_images_from_word(file_path: str):
    """
    Word faylidan rasmlarni ajratib olish va ularni saqlash.
    Rasmning oldidan kelgan savolni aniqlash.
    """
    # Word faylni ochamiz
    doc = Document(file_path)
    image_counter = 1
    question_with_images = []

    # Rasmlarni saqlash uchun
    image_refs = {}
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

    # Savollarni yig'ish va rasmni bog'lash
    paragraphs = iter(doc.paragraphs)
    last_question = ""
    for paragraph in paragraphs:
        text = paragraph.text.strip()
        if text:  # Bo'sh paragraphni o'tkazib yuboramiz
            last_question = text  # Oxirgi savol sifatida saqlaymiz

        # Rasm tekshirish
        for rel_ref, path in image_refs.items():
            if rel_ref in paragraph._p.xml:
                question_with_images.append({
                    "question": last_question,
                    "image_path": path
                })

    return question_with_images

# Word fayl yo'li
file_path = "9-sinf biolog (1).docx"

# Funksiyani chaqirish
results = extract_images_from_word(file_path)

# Natijalarni chop etish
for idx, item in enumerate(results, start=1):
    print(f"{idx}. Savol: {item['question']}")
    print(f"   Rasm yo'li: {item['image_path']}")
