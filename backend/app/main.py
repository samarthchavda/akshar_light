from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi import Body
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import base64


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        html = render_template_by_id(req.template_id, req.context or {})
        pdf_bytes = HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = f"{req.template_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

