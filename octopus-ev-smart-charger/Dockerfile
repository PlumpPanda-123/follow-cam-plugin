FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY evcharger ./evcharger
ENV TZ=Europe/London PYTHONUNBUFFERED=1
CMD ["python", "-m", "evcharger"]
