FROM python:3.9

RUN apt-get update && apt-get install -y postgresql-client

RUN mkdir /GetParserBot

WORKDIR /GetParserBot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh