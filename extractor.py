import os
import json
import io
import base64
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _image_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def extract_text_from_image(file_bytes):
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    b64 = _image_to_base64(image)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "high"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this receipt image exactly as it appears. Do not summarise, just transcribe everything."
                    }
                ]
            }
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content.strip()


def extract_invoice_fields(raw_text):
    prompt = f"""
You are a Walmart receipt parser. Extract ALL important fields from this receipt text.
Return ONLY valid JSON, nothing else. No explanation, no markdown, just raw JSON.

Fields to extract:
- store_name (string)
- store_address (string)
- store_id (string)
- manager (string)
- cashier (string)
- terminal_id (string)
- transaction_id (string)
- date (string)
- time (string)
- items (list of objects with: name, quantity, unit_price, total, taxable (true/false))
- subtotal (string)
- tax_amount (string)
- tax_rate (string)
- total_amount (string)
- payment_method (string)
- amount_paid (string)
- change_due (string)
- items_sold (string)

If a field is not found, use null.

Receipt text:
{raw_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_json = response.choices[0].message.content.strip()

    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    return json.loads(raw_json)


def process_invoice(file_bytes, filename):
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file_bytes)
        img_bytes = io.BytesIO()
        images[0].save(img_bytes, format="JPEG")
        file_bytes = img_bytes.getvalue()

    raw_text = extract_text_from_image(file_bytes)
    fields = extract_invoice_fields(raw_text)
    return raw_text, fields