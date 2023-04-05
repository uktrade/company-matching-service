FROM python:3.8

RUN apt-get update -y

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"

ADD scripts scripts
RUN scripts/install_dockerize.sh

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /app

COPY . /app

CMD /app/scripts/entrypoint.sh
