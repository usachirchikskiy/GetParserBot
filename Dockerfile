FROM python:3.9

RUN mkdir /GetParserBot

WORKDIR /GetParserBot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh