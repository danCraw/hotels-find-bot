FROM python:3.10-alpine

WORKDIR /app


RUN apk add --no-cache gcc musl-dev libc-dev libffi-dev openssl-dev

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["python", "-m", "app.main"]
