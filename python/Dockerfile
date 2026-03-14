FROM python:3.13-alpine
WORKDIR /app
COPY ./python ./
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
