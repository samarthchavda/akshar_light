from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import os
import json
from datetime import datetime
from urllib import request as urlrequest, error as urlerror
from functools import lru_cache

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


@lru_cache(maxsize=1)
def get_font_data_url() -> str | None:
    font_path = TEMPLATE_DIR / "fonts" / "NotoSansGujarati-Regular.ttf"
    if not font_path.exists():
        return None
    return "data:font/ttf;base64," + base64.b64encode(font_path.read_bytes()).decode()


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
    subtotal: float = Field(default=0, ge=0)
    gst_enabled: bool = False
    gst_amount: float = Field(default=0, ge=0)
    total_words: str = ""
    notes: str = ""
    language: str = "auto"


class TemplateRenderRequest(BaseModel):
    template_id: str = Field(...)
    context: dict = Field(default_factory=dict)


class LetterFormatRequest(BaseModel):
    text: str = Field(default="")
    recipient_name: str = Field(default="")
    bill_date: str = Field(default="")


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

# Get allowed origins from environment or use safe defaults
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://akshar-light.vercel.app")
configured_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [
    origin.strip()
    for origin in configured_origins.split(",")
    if origin.strip()
] if configured_origins else [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://akshar-light.vercel.app",
    FRONTEND_URL,
]
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
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
    empty_rows = max(0, 26 - len(items))
    
    # Calculate GST and final total first
    gst_amount = payload.gst_amount or 0
    gst_enabled = payload.gst_enabled or False
    subtotal = payload.subtotal or total
    final_total = total if not gst_enabled else (subtotal + gst_amount)
    
    # Now calculate total_words using final_total
    final_total_words = (payload.total_words or "").strip() or amount_to_words_i18n(final_total, payload)
    
    # embed font as base64 if available so blob previews render Gujarati correctly
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
        subtotal=subtotal,
        gst_enabled=gst_enabled,
        gst_amount=gst_amount,
        total=final_total,
        total_words=final_total_words,
        notes=payload.notes or "",
        font_data_url=None,
        lang=(payload.language or 'en'),
    )


def render_invoice_pdf(payload: InvoiceRequest) -> bytes:
    html = render_invoice_html(payload)
    return HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()


def render_invoice_template_html(payload: InvoiceRequest, template_id: str = "akhar_invoice") -> str:
    """Render invoice-based templates with full invoice processing (items, GST, etc.)"""
    template = env.get_template(ALLOWED_TEMPLATES.get(template_id, "invoice_template.html"))
    items, total = compute_items(payload)
    empty_rows = max(0, 26 - len(items))
    
    # Calculate GST and final total
    gst_amount = payload.gst_amount or 0
    gst_enabled = payload.gst_enabled or False
    subtotal = payload.subtotal or total
    final_total = total if not gst_enabled else (subtotal + gst_amount)
    
    # Calculate total words using final_total
    final_total_words = (payload.total_words or "").strip() or amount_to_words_i18n(final_total, payload)
    
    # Embed font as base64
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
        subtotal=subtotal,
        gst_enabled=gst_enabled,
        gst_amount=gst_amount,
        total=final_total,
        total_words=final_total_words,
        notes=payload.notes or "",
        font_data_url=None,
        lang=(payload.language or 'en'),
    )


ALLOWED_TEMPLATES = {
    "letter_pad": "letter_pad_demo.html",
    "akhar_invoice": "invoice_template.html",
    "invoice_template": "invoice_template.html",
    "invoice": "invoice_template.html",
}


def normalize_template_id(template_id: str | None) -> str:
    value = (template_id or "").strip()
    if not value:
        return ""
    return value.lower()


def render_template_by_id(template_id: str, context: dict) -> str:
    filename = ALLOWED_TEMPLATES.get(normalize_template_id(template_id))
    if not filename:
        raise ValueError("Unknown template")
    
    # Special handling for invoice template with items
    if normalize_template_id(template_id) == "akhar_invoice" and "items" in context:
        # Create an InvoiceRequest object from context for processing
        invoice_data = {
            "company_name": context.get("company_name", "Sanjay Dharamshibhai Chavda"),
            "company_tagline": context.get("company_tagline", "ALL TYPE OF ELECTRICAL WORKS"),
            "company_address": context.get("company_address", '"KOMAL DEEP" Satya Narayan Nagar MainRoad, Near. BatukMaharaj Guaashala, Gandhigram, Rajkot.'),
            "company_contact": context.get("company_contact", "Call. +91 92274 20287, Email. aksharlight@yahoo.in"),
            "customer_name": context.get("customer_name", ""),
            "customer_address": context.get("customer_address", ""),
            "bill_date": context.get("bill_date", ""),
            "bill_no": context.get("bill_no", ""),
            "pan_no": context.get("pan_no", "AGGPC1817R"),
            "items": context.get("items", []),
            "subtotal": context.get("subtotal", 0),
            "gst_enabled": context.get("gst_enabled", False),
            "gst_amount": context.get("gst_amount", 0),
            "total_words": context.get("total_words", ""),
            "notes": context.get("notes", ""),
            "language": context.get("language", "auto"),
        }
        payload = InvoiceRequest(**invoice_data)
        return render_invoice_template_html(payload, template_id)
    
    # Normalize items if present so templates can rely on `item.amount` etc.
    if "items" in context:
        items = context.get("items") or []
        normalized: list[dict[str, Any]] = []
        total = 0.0
        for index, it in enumerate(items, start=1):
            qty = float(it.get("qty") or it.get("quantity") or 0)
            rate = float(it.get("rate") or it.get("price") or 0)
            amount = float(it.get("amount") if it.get("amount") is not None else qty * rate)
            total += amount
            normalized.append(
                {
                    "no": it.get("no") or index,
                    "description": it.get("description") or it.get("desc") or "",
                    "qty": qty,
                    "rate": rate,
                    "amount": amount,
                }
            )
        context["items"] = normalized
        context.setdefault("subtotal", context.get("subtotal", total))
        context.setdefault("total", context.get("total", context.get("subtotal", total) + context.get("gst_amount", 0)))
        # Provide empty_rows for templates that expect a fixed table height
        try:
            context["empty_rows"] = int(max(0, 26 - len(normalized)))
        except Exception:
            context["empty_rows"] = 0
        context.setdefault("total_words", context.get("total_words", ""))

    template = env.get_template(filename)
    return template.render(**context)


@app.get("/", response_class=HTMLResponse)
def health_page() -> str:
    return "<h1>Akhar Light Billing API</h1><p>Use POST /api/invoice/pdf to generate PDFs.</p>"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def local_letter_formatter(text: str) -> str:
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""

    lines = [line.strip(" -•\t") for line in raw.split("\n") if line.strip()]

    # If a single long paragraph is provided, break it into readable lines.
    if len(lines) <= 1:
        chunks = re.split(
            r"\s{2,}|(?<=[\.!?।])\s+|\s+(?=(?:not include|terms|amount|camera|mcb|total)\b)",
            raw,
            flags=re.IGNORECASE,
        )
        if len(chunks) <= 1:
            chunks = re.split(r"(?<=[\.!?।])\s+", raw)
        lines = [chunk.strip(" -•\t") for chunk in chunks if chunk.strip()]

    formatted: list[str] = []
    for line in lines:
        compact = re.sub(r"\s+", " ", line).strip()
        if not compact:
            continue
        if re.match(r"^(to\b|dear\b|respected\b|શ્રી\b|શ્રીમતી\b|માટે\b)", compact, flags=re.IGNORECASE):
            formatted.append(compact)
        elif compact.startswith("•"):
            formatted.append(f"• {compact.lstrip('• ').strip()}")
        else:
            formatted.append(f"• {compact}")

    # Keep letters concise for template rendering.
    return "\n".join(formatted[:22])


def normalize_letter_output(text: str) -> str:
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""

    # Remove code fences or accidental markdown wrappers from AI outputs.
    raw = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", raw)
    raw = re.sub(r"\n```$", "", raw)

    normalized_lines: list[str] = []
    for line in raw.split("\n"):
        compact = re.sub(r"\s+", " ", line).strip()
        if not compact:
            continue

        # Convert numbered/checklist prefixes to clean bullet format.
        compact = re.sub(r"^(?:[-*]|\d+[\.)]|[a-zA-Z][\.)])\s*", "", compact)
        compact = compact.lstrip("• ").strip()
        if not compact:
            continue

        if re.match(r"^(to\b|dear\b|respected\b|શ્રી\b|શ્રીમતી\b|માટે\b)", compact, flags=re.IGNORECASE):
            normalized_lines.append(compact)
        else:
            normalized_lines.append(f"• {compact}")

    return "\n".join(normalized_lines[:22])


def openai_letter_formatter(text: str, recipient_name: str = "", bill_date: str = "") -> str | None:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None

    model = (os.getenv("OPENAI_MODEL") or "gpt-4.1-mini").strip()
    system_prompt = (
        "You are a formatter for Indian business letter-pad text. "
        "Rewrite messy raw notes into clean, professional lines for print. "
        "Keep original meaning, language (Gujarati/English mix), names, numbers, and amounts exactly. "
        "Return plain text only, one point per line, prefer bullet lines with the bullet symbol •. "
        "Do not add any explanation."
    )
    user_prompt = (
        f"Recipient: {recipient_name or '-'}\n"
        f"Date: {bill_date or '-'}\n"
        f"Raw text:\n{text}"
    )

    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
        "temperature": 0.2,
        "max_output_tokens": 500,
    }

    req = urlrequest.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            output_text = (data.get("output_text") or "").strip()
            if output_text:
                return output_text
    except (urlerror.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
        return None

    return None


def gemini_letter_formatter(text: str, recipient_name: str = "", bill_date: str = "") -> str | None:
    api_key = (
        (os.getenv("GEMINI_API_KEY") or "").strip()
        or (os.getenv("GOOGLE_API_KEY") or "").strip()
    )
    if not api_key:
        # Backward compatibility: treat Google-style key in OPENAI_API_KEY as Gemini key.
        maybe_gemini = (os.getenv("OPENAI_API_KEY") or "").strip()
        if maybe_gemini.startswith("AIza"):
            api_key = maybe_gemini
    if not api_key:
        return None

    configured_model = (os.getenv("GEMINI_MODEL") or "").strip()
    model_candidates = [
        configured_model,
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
    ]
    models = [m for m in model_candidates if m]

    system_prompt = (
        "You are a formatter for Indian business letter-pad text. "
        "Rewrite messy raw notes into clean, professional lines for print. "
        "Keep original meaning, language (Gujarati/English mix), names, numbers, and amounts exactly. "
        "Return plain text only, one point per line, prefer bullet lines with the bullet symbol •. "
        "Do not add any explanation."
    )
    user_prompt = (
        f"Recipient: {recipient_name or '-'}\n"
        f"Date: {bill_date or '-'}\n"
        f"Raw text:\n{text}"
    )

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 500,
        },
    }

    for model in models:
        req = urlrequest.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates") or []
                if not candidates:
                    continue
                parts = ((candidates[0].get("content") or {}).get("parts") or [])
                text_parts = [str(part.get("text", "")).strip() for part in parts if part.get("text")]
                formatted = "\n".join([p for p in text_parts if p]).strip()
                if formatted:
                    return formatted
        except (urlerror.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
            continue

    return None


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
        context = dict(req.context or {})
        # provide defaults for common fields
        context.setdefault('company_name', 'Sanjay Dharamshibhai Chavda')
        context.setdefault('company_tagline', 'ALL TYPE OF ELECTRIK WORK')
        context.setdefault('bill_date', '')
        context.setdefault('recipient_name', '')
        context.setdefault('lines', [])
        context.setdefault('thanks_text', 'Thanks,\nSanjay Chavda')
        context['font_data_url'] = get_font_data_url()
        context['lang'] = context.get('lang') or 'gu' if contains_gujarati(context.get('recipient_name','') + '\n' + '\n'.join([str(x) for x in context.get('lines',[])])) else 'en'

        html = render_template_by_id(req.template_id, context)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return html


@app.post("/api/template/pdf")
def template_pdf(req: TemplateRenderRequest = Body(...)) -> Response:
    try:
        context = dict(req.context or {})
        context.setdefault('company_name', 'Sanjay Dharamshibhai Chavda')
        context.setdefault('company_tagline', 'ALL TYPE OF ELECTRIK WORK')
        context.setdefault('bill_date', '')
        context.setdefault('recipient_name', '')
        context.setdefault('lines', [])
        context.setdefault('thanks_text', 'Thanks,\nSanjay Chavda')
        context['font_data_url'] = None
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


@app.post("/api/letter/format")
def format_letter_text(payload: LetterFormatRequest) -> dict[str, str]:
    raw_text = (payload.text or "").strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text is required")

    ai_text = openai_letter_formatter(
        text=raw_text,
        recipient_name=payload.recipient_name,
        bill_date=payload.bill_date,
    )
    if ai_text:
        return {"formatted_text": normalize_letter_output(ai_text), "provider": "openai"}

    gemini_text = gemini_letter_formatter(
        text=raw_text,
        recipient_name=payload.recipient_name,
        bill_date=payload.bill_date,
    )
    if gemini_text:
        return {"formatted_text": normalize_letter_output(gemini_text), "provider": "gemini"}

    return {"formatted_text": normalize_letter_output(local_letter_formatter(raw_text)), "provider": "local"}



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
