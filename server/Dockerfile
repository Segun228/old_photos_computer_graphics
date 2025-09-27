FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


RUN mkdir -p uploads static/results

EXPOSE 8000


CMD ["python", "app.py"]