FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY static ./static

RUN mkdir -p /data

ENV DATABASE_PATH=/data/contacts.db
ENV PORT=3000

EXPOSE 3000

CMD ["python", "app.py"]
