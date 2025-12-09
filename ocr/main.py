# main.py (OCR + Pipeline integration)

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException

# -------------------------------------------------------------------------
# 0. Ensure root project directory is on PYTHONPATH
#    This allows us to import PipeLine, UnifiedPipeline, db, etc.
# -------------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Now these imports will work:
from db import SessionLocal, engine  # SQLAlchemy engine + session
from models import Base, UploadedFile
from ocr_models import OcrDoc
from ocr_utils import is_allowed_image, run_ocr_on_image_bytes, txt_to_pdf_bytes
from vercel_blob import upload_to_vercel_blob
from supabase_storage import upload_pdf_to_supabase

from dotenv import load_dotenv
from sqlalchemy.orm import Session  # ✅ correct Session type for Depends
from PipeLine import get_db_connection  # ✅ from root-level PipeLine.py
from UnifiedPipeline import process_file  # ✅ from root-level UnifiedPipeline.py

load_dotenv()
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

Base.metadata.create_all(bind=engine)

app = FastAPI()


# -------------------------------------------------------------------------
# Dependency: Database Session (SQLAlchemy, for OCR-related tables)
# -------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------------
# UPLOAD ENDPOINT WITH:
#  - OCR
#  - PDF generation
#  - Upload to Supabase
#  - Run UnifiedPipeline on local PDF copy
# -------------------------------------------------------------------------
@app.post("/upload")
async def upload_file(
    username: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    original_filename = file.filename
    ext = Path(original_filename).suffix.lower()

    # Validate extension (you can also allow PDFs here if you want)
    if not is_allowed_image(original_filename):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    image_bytes = await file.read()

    # -----------------------------------------
    # 1. Upload original image to Vercel Blob
    # -----------------------------------------
    image_url = upload_to_vercel_blob(image_bytes, original_filename)

    # -----------------------------------------
    # 2. OCR extraction (text + tables)
    # -----------------------------------------
    ocr_text, extracted_tables = run_ocr_on_image_bytes(image_bytes, suffix=ext)

    # -----------------------------------------
    # 3. Generate PDF bytes from OCR text/tables
    # -----------------------------------------
    pdf_bytes = txt_to_pdf_bytes(
        ocr_text,
        username=username,
        tables=extracted_tables,
    )

    # -----------------------------------------
    # 4. Upload PDF to Supabase (for frontend download/view)
    # -----------------------------------------
    pdf_filename = f"{username}_ocr.pdf"
    pdf_url = upload_pdf_to_supabase(pdf_bytes, pdf_filename)

    # -----------------------------------------
    # 5. Save OCR doc metadata to ocr_docs table
    # -----------------------------------------
    ocr_doc = OcrDoc(
        user_id=uuid.UUID(DEFAULT_USER_ID),
        username=username,
        extracted_text=ocr_text,
        json_data=json.dumps({"text": ocr_text}),
        image_url=image_url,
    )
    db.add(ocr_doc)
    db.commit()
    db.refresh(ocr_doc)

    # -----------------------------------------
    # 6. Save upload record into uploaded_files table
    # -----------------------------------------
    uploaded_file = UploadedFile(
        username=username,
        original_filename=original_filename,
        mime_type=file.content_type,
        extension=ext,
        data=image_bytes,
        ocr_text=ocr_text,
        pdf_data=pdf_bytes,
        pdf_url=pdf_url,
        report_text=(
            f"Username: {username}\n"
            f"File: {original_filename}\n"
            f"OCR ID: {ocr_doc.ocr_id}"
        ),
        table_data=json.dumps(extracted_tables) if extracted_tables else None,
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    # ---------------------------------------------------------------------
    # 7. Save the PDF locally into data/input and call UnifiedPipeline
    # ---------------------------------------------------------------------
    LOCAL_INPUT_DIR = Path(ROOT_DIR) / "data" / "input"
    LOCAL_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    local_pdf_path = LOCAL_INPUT_DIR / f"{username}_ocr_{uuid.uuid4()}.pdf"
    with open(local_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"[OCR] Local PDF saved for pipeline: {local_pdf_path}")

    # --- Run the classification/ingestion pipeline on this PDF ---
    conn = get_db_connection()
    try:
        pipeline_user_id = DEFAULT_USER_ID  # or look up actual DB user later
        processed, metrics = process_file(conn, str(local_pdf_path), pipeline_user_id)
        print(f"[PIPELINE] Processed {processed} transactions from {local_pdf_path}")
        print(f"[PIPELINE][metrics]: {metrics}")
    except Exception as e:
        print("[PIPELINE ERROR]:", e)
    finally:
        conn.close()

    # ---------------------------------------------------------------------
    # 8. Return API response
    # ---------------------------------------------------------------------
    return {
        "ocr_id": str(ocr_doc.ocr_id),
        "file_id": uploaded_file.id,
        "user_id": str(ocr_doc.user_id),
        "username": username,
        "extracted_text": ocr_doc.extracted_text,
        "image_url": ocr_doc.image_url,
        "pdf_url": pdf_url,
        "pipeline_pdf_path": str(local_pdf_path),
        "created_at": ocr_doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "OCR processed successfully and UnifiedPipeline executed.",
    }


# -------------------------------------------------------------------------
# FILE RETRIEVAL ROUTES (unchanged)
# -------------------------------------------------------------------------
@app.get("/files/{file_id}")
def get_file_info(file_id: int, db: Session = Depends(get_db)):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": db_file.id,
        "username": db_file.username,
        "original_filename": db_file.original_filename,
        "uploaded_at": db_file.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
        "ocr_text": db_file.ocr_text,
        "report_text": db_file.report_text,
        "table_data": json.loads(db_file.table_data) if db_file.table_data else None,
    }


@app.get("/files/{file_id}/pdf")
def download_pdf(file_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import Response

    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file or not db_file.pdf_data:
        raise HTTPException(status_code=404, detail="PDF not found")

    return Response(
        content=db_file.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={db_file.username}_ocr.pdf"},
    )


@app.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    image_bytes = await file.read()
    ext = Path(file.filename).suffix.lower()
    ocr_text, tables = run_ocr_on_image_bytes(image_bytes, suffix=ext)
    return {
        "ocr_text": ocr_text,
        "tables_found": len(tables),
        "length": len(ocr_text),
    }
