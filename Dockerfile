FROM python:3.10-alpine

WORKDIR /app

# Устанавливаем зависимости для сборки (если нужны)
RUN apk add --no-cache gcc musl-dev

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Добавляем путь к проекту в PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["python", "-m", "app.main"]