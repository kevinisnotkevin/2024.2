FROM python:3.12-slim

WORKDIR /usr/src/app

COPY . .
#COPY .env .

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
