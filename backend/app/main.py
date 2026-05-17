from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi import Body
from pydantic import BaseModel, Field, EmailStr
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import base64
from pymongo import MongoClient
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)
db = client.get_database("akshar_light")
invoices_collection = db.get_collection("invoices")
users_collection = db.get_collection("users")

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


class Item(BaseModel):
    no: int = Field(default=1, ge=1)
    description: str = ""
    qty: float = Field(default=1, ge=0)
    rate: float = Field(default=0, ge=0)


class InvoiceRequest(BaseModel):
    company_name: str = "Sanjay Dharamshibhai Chavda"
    company_tagline: str = "ALL TYPE OF ELECTRICAL WORKS"
    company_address: str = '"KOMAL DEEP" Satya Narayan Nagar MainRoad, Near. BatukMaharaj Guaashala, Gandhigram, Rajkot.'
    company_contact: str = "Call. +91 92274 20287, Email. aksharlight@yahoo.in"
    customer_name: str = ""
    customer_address: str = ""
    bill_date: str = ""
    bill_no: str = ""
    pan_no: str = "AGGPC1817R"
    items: list[Item] = Field(default_factory=list)
    total_words: str = ""
    notes: str = ""
    language: str = "auto"


class TemplateRenderRequest(BaseModel):
    template_id: str = Field(...)
    context: dict = Field(default_factory=dict)


class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class InvoiceSave(BaseModel):
    user_email: str
    invoice_data: dict


class LetterSave(BaseModel):
    user_email: str
    letter_data: dict


ONES = [
    "",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
]

TENS = [
    "",
    "",
    "Twenty",
    "Thirty",
    "Forty",
    "Fifty",
    "Sixty",
    "Seventy",
    "Eighty",
    "Ninety",
]

GUJ_ONES = [
    "",
    "એક",
    "બે",
    "ત્રણ",
    "ચાર",
    "પાંચ",
    "છ",
    "સાત",
    "આઠ",
    "નવ",
    "દસ",
    "અગિયાર",
    "બાર",
    "તેર",
    "ચૌદ",
    "પંદર",
    "સોળ",
    "સત્તર",
    "અઢાર",
    "ઓગણીસ",
]

GUJ_TENS = [
    "",
    "",
    "વીસ",
    "ત્રીસ",
    "ચાલીસ",
    "પચાસ",
    "સાઠ",
    "સિત્તેર",
    "એંસી",
    "નેવું",
]


app = FastAPI(title="Akhar Light Billing API")

# Get allowed origins from environment or use defaults
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_URL,
]

# Add Railway frontend URL pattern
if "railway.app" in FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Railway deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


def compute_items(payload: InvoiceRequest) -> tuple[list[dict[str, Any]], float]:
    normalized: list[dict[str, Any]] = []
    total = 0.0
    for index, item in enumerate(payload.items, start=1):
        amount = float(item.qty) * float(item.rate)
        total += amount
        normalized.append(
            {
                "no": item.no or index,
                "description": item.description,
                "qty": float(item.qty),
                "rate": float(item.rate),
                "amount": amount,
            }
        )
    return normalized, total


def two_digit_words(value: int) -> str:
    if value < 20:
        return ONES[value]
    ten = value // 10
    one = value % 10
    return (TENS[ten] + (" " + ONES[one] if one else "")).strip()


def three_digit_words(value: int) -> str:
    hundred = value // 100
    remainder = value % 100
    text = ""
    if hundred:
        text = f"{ONES[hundred]} Hundred"
    if remainder:
        text = f"{text} {two_digit_words(remainder)}".strip()
    return text


def integer_to_indian_words(value: int) -> str:
    if value == 0:
        return "Zero"

    parts: list[str] = []
    crore = value // 10000000
    value %= 10000000
    lakh = value // 100000
    value %= 100000
    thousand = value // 1000
    value %= 1000
    hundred_block = value

    if crore:
        parts.append(f"{two_digit_words(crore)} Crore")
    if lakh:
        parts.append(f"{two_digit_words(lakh)} Lakh")
    if thousand:
        parts.append(f"{two_digit_words(thousand)} Thousand")
    if hundred_block:
        parts.append(three_digit_words(hundred_block))

    return " ".join(part for part in parts if part).strip()


def amount_to_words(amount: float) -> str:
    safe_amount = max(0.0, float(amount))
    rupees = int(safe_amount)
    paise = int(round((safe_amount - rupees) * 100))

    if paise == 100:
        rupees += 1
        paise = 0

    rupee_words = integer_to_indian_words(rupees)
    if paise:
        paise_words = integer_to_indian_words(paise)
        return f"Rupees {rupee_words} and {paise_words} Paise Only"
    return f"Rupees {rupee_words} Only"


def two_digit_words_gu(value: int) -> str:
    if value < 20:
        return GUJ_ONES[value]
    ten = value // 10
    one = value % 10
    return (GUJ_TENS[ten] + (" " + GUJ_ONES[one] if one else "")).strip()


def three_digit_words_gu(value: int) -> str:
    hundred = value // 100
    remainder = value % 100
    text = ""
    if hundred:
        text = f"{GUJ_ONES[hundred]} સો"
    if remainder:
        text = f"{text} {two_digit_words_gu(remainder)}".strip()
    return text


def integer_to_indian_words_gu(value: int) -> str:
    if value == 0:
        return "શૂન્ય"

    parts: list[str] = []
    crore = value // 10000000
    value %= 10000000
    lakh = value // 100000
    value %= 100000
    thousand = value // 1000
    value %= 1000
    hundred_block = value

    if crore:
        parts.append(f"{two_digit_words_gu(crore)} કરોડ")
    if lakh:
        parts.append(f"{two_digit_words_gu(lakh)} લાખ")
    if thousand:
        parts.append(f"{two_digit_words_gu(thousand)} હજાર")
    if hundred_block:
        parts.append(three_digit_words_gu(hundred_block))

    return " ".join(part for part in parts if part).strip()


def contains_gujarati(text: str) -> bool:
    return bool(re.search(r"[\u0A80-\u0AFF]", text or ""))


def amount_to_words_i18n(amount: float, payload: InvoiceRequest) -> str:
    text_blob = " ".join(
        [
            payload.customer_name,
            payload.customer_address,
            payload.company_name,
            payload.company_address,
            payload.notes,
            payload.total_words,
        ]
    )
    language = (payload.language or "auto").strip().lower()
    use_gujarati = language == "gu" or (language == "auto" and contains_gujarati(text_blob))

    safe_amount = max(0.0, float(amount))
    rupees = int(safe_amount)
    paise = int(round((safe_amount - rupees) * 100))
    if paise == 100:
        rupees += 1
        paise = 0

    if use_gujarati:
        rupee_words = integer_to_indian_words_gu(rupees)
        if paise:
            paise_words = integer_to_indian_words_gu(paise)
            return f"રૂપિયા {rupee_words} અને {paise_words} પૈસા માત્ર"
        return f"રૂપિયા {rupee_words} માત્ર"

    return amount_to_words(safe_amount)


def render_invoice_html(payload: InvoiceRequest) -> str:
    template = env.get_template("bill_template.html")
    items, total = compute_items(payload)
    empty_rows = max(0, 20 - len(items))
    final_total_words = (payload.total_words or "").strip() or amount_to_words_i18n(total, payload)
    # embed font as base64 if available so blob previews render Gujarati correctly
    font_path = TEMPLATE_DIR / "fonts" / "NotoSansGujarati-Regular.ttf"
    font_data_url = None
    if font_path.exists():
        font_data_url = "data:font/ttf;base64," + base64.b64encode(font_path.read_bytes()).decode()

    return template.render(
        company_name=payload.company_name,
        company_tagline=payload.company_tagline,
        company_address=payload.company_address,
        company_contact=payload.company_contact,
        customer_name=payload.customer_name,
        customer_address=payload.customer_address,
        bill_date=payload.bill_date,
        bill_no=payload.bill_no,
        pan_no=payload.pan_no,
        items=items,
        empty_rows=empty_rows,
        total=total,
        total_words=final_total_words,
        notes=payload.notes or "",
        font_data_url=font_data_url,
        lang=(payload.language or 'en'),
    )


def render_invoice_pdf(payload: InvoiceRequest) -> bytes:
    html = render_invoice_html(payload)
    return HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()


ALLOWED_TEMPLATES = {
    "akhar_classic": "bill_template.html",
    "letter_pad": "letter_pad_demo.html",
}


def render_template_by_id(template_id: str, context: dict) -> str:
    filename = ALLOWED_TEMPLATES.get(template_id)
    if not filename:
        raise ValueError("Unknown template")
    template = env.get_template(filename)
    return template.render(**context)


@app.get("/", response_class=HTMLResponse)
def health_page() -> str:
    return "<h1>Akhar Light Billing API</h1><p>Use POST /api/invoice/pdf to generate PDFs.</p>"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/invoice/html", response_class=HTMLResponse)
def invoice_html(payload: InvoiceRequest) -> str:
    return render_invoice_html(payload)


@app.post("/api/invoice/pdf")
def invoice_pdf(payload: InvoiceRequest) -> Response:
    try:
        pdf_bytes = render_invoice_pdf(payload)
    except Exception as exc:  # pragma: no cover - surfaced to client
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc
    filename = f"bill_{payload.bill_no or 'invoice'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@app.post("/api/template/render", response_class=HTMLResponse)
def template_render(req: TemplateRenderRequest = Body(...)) -> str:
    try:
        # prepare font data url
        font_path = TEMPLATE_DIR / "fonts" / "NotoSansGujarati-Regular.ttf"
        font_data_url = None
        if font_path.exists():
            font_data_url = "data:font/ttf;base64," + base64.b64encode(font_path.read_bytes()).decode()

        context = dict(req.context or {})
        # provide defaults for common fields
        context.setdefault('company_name', 'Sanjay Dharamshibhai Chavda')
        context.setdefault('company_tagline', 'ALL TYPE OF ELECTRIK WORK')
        context.setdefault('bill_date', '')
        context.setdefault('recipient_name', '')
        context.setdefault('lines', [])
        context.setdefault('thanks_text', 'Thanks,\nSanjay Chavda')
        context['font_data_url'] = font_data_url
        context['lang'] = context.get('lang') or 'gu' if contains_gujarati(context.get('recipient_name','') + '\n' + '\n'.join([str(x) for x in context.get('lines',[])])) else 'en'

        html = render_template_by_id(req.template_id, context)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return html


@app.post("/api/template/pdf")
def template_pdf(req: TemplateRenderRequest = Body(...)) -> Response:
    try:
        font_path = TEMPLATE_DIR / "fonts" / "NotoSansGujarati-Regular.ttf"
        font_data_url = None
        if font_path.exists():
            font_data_url = "data:font/ttf;base64," + base64.b64encode(font_path.read_bytes()).decode()

        context = dict(req.context or {})
        context.setdefault('company_name', 'Sanjay Dharamshibhai Chavda')
        context.setdefault('company_tagline', 'ALL TYPE OF ELECTRIK WORK')
        context.setdefault('bill_date', '')
        context.setdefault('recipient_name', '')
        context.setdefault('lines', [])
        context.setdefault('thanks_text', 'Thanks,\nSanjay Chavda')
        context['font_data_url'] = font_data_url
        context['lang'] = context.get('lang') or 'gu' if contains_gujarati(context.get('recipient_name', '') + '\n' + '\n'.join([str(x) for x in context.get('lines', [])])) else 'en'

        html = render_template_by_id(req.template_id, context)
        pdf_bytes = HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = f"{req.template_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )



# ==================== Authentication Endpoints ====================

@app.post("/api/auth/signup")
def signup(user: UserSignup):
    """User signup - create new account"""
    try:
        # Check if user already exists
        existing_user = users_collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create new user
        user_doc = {
            "name": user.name,
            "email": user.email,
            "password": hash_password(user.password),
            "created_at": datetime.utcnow(),
        }
        result = users_collection.insert_one(user_doc)
        
        return {
            "success": True,
            "message": "Account created successfully",
            "user": {
                "email": user.email,
                "name": user.name,
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Signup failed: {exc}") from exc


@app.post("/api/auth/login")
def login(credentials: UserLogin):
    """User login - verify credentials"""
    try:
        # Find user
        user = users_collection.find_one({"email": credentials.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "email": user["email"],
                "name": user["name"],
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Login failed: {exc}") from exc


# ==================== Invoice & Letter Management ====================

@app.post("/api/invoices/save")
def save_invoice(data: InvoiceSave):
    """Save invoice to database"""
    try:
        invoice_doc = {
            "user_email": data.user_email,
            "invoice_data": data.invoice_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        # Check if invoice already exists (by invoice ID)
        invoice_id = data.invoice_data.get("id")
        if invoice_id:
            existing = invoices_collection.find_one({
                "user_email": data.user_email,
                "invoice_data.id": invoice_id
            })
            if existing:
                # Update existing invoice
                invoices_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"invoice_data": data.invoice_data, "updated_at": datetime.utcnow()}}
                )
                return {"success": True, "message": "Invoice updated"}
        
        # Insert new invoice
        invoices_collection.insert_one(invoice_doc)
        return {"success": True, "message": "Invoice saved"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Save failed: {exc}") from exc


@app.get("/api/invoices/{user_email}")
def get_invoices(user_email: str):
    """Get all invoices for a user"""
    try:
        invoices = list(invoices_collection.find(
            {"user_email": user_email},
            {"_id": 0, "invoice_data": 1}
        ))
        return {
            "success": True,
            "invoices": [inv["invoice_data"] for inv in invoices]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc


@app.delete("/api/invoices/{user_email}/{invoice_id}")
def delete_invoice(user_email: str, invoice_id: int):
    """Delete an invoice"""
    try:
        result = invoices_collection.delete_one({
            "user_email": user_email,
            "invoice_data.id": invoice_id
        })
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"success": True, "message": "Invoice deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete failed: {exc}") from exc
