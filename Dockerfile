FROM python:3.8-slim-buster

WORKDIR /src

COPY . .

CMD ["python", "./chat_server.py", "-sp", "8080"]
