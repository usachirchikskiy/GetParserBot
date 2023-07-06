FROM python:3.9

RUN mkdir /GetParserBot

WORKDIR /GetParserBot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh
# WORKDIR src

# CMD gunicorn src.main:app --preload --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000