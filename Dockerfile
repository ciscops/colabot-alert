FROM python:3.7-alpine

RUN apk update && apk upgrade && apk add bash && pip install -U pip

RUN adduser -D alert
WORKDIR /home/alert
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
COPY main.py main.py
COPY docker_boot.sh docker_boot.sh
RUN chmod +x docker_boot.sh
RUN chown -R alert:alert ./

USER alert
ENTRYPOINT ["./docker_boot.sh"]


