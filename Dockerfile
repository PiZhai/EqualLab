FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10086

CMD ["uvicorn", "equallab.web:app", "--host", "0.0.0.0", "--port", "10086"]


