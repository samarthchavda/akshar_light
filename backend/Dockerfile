FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/pyproject.toml backend/requirements.txt backend/ /app/

RUN pip install --upgrade pip && \
    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
