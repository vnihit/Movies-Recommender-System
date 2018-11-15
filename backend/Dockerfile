FROM python:3

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

ADD ./ /backend
WORKDIR /backend

EXPOSE 8000
