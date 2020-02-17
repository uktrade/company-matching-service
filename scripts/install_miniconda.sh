#!/bin/bash

source ./scripts/functions.sh

# Set PATH before installing miniconda.sh
PATH=/root/miniconda3/envs/cms/bin:${PATH}
#
## Add the following lines to DockerFile
## ADD environment.yml /tmp/environment.yml
## RUN conda env create -f /tmp/environment.yml
# Pull the environment name out of the environment.yml
# RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc

run "curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh  --output miniconda.sh"
run "bash miniconda.sh -b"
run "rm -f miniconda.sh"
