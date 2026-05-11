FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \ 
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

#INSTALAMOS DEPENDENCIAS
COPY requeriments.txt ./
RUN pip install --no-cache-dir -r requeriments.txt

#COPIAMOS EL CODIGO DE LA APP
COPY code  ./code

#Compilamos los .po -> .mo
WORKDIR /app/code
RUN python -m compile_translations.py || true

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0", "--port", "8000"]