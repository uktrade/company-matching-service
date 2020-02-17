FROM python:3.6

RUN apt-get update -y

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"

ADD scripts scripts
RUN scripts/install_dockerize.sh
RUN scripts/install_miniconda.sh

ADD environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml
# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc


WORKDIR /app

COPY . /app

CMD /app/scripts/entrypoint.sh
