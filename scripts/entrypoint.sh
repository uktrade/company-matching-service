#!/bin/bash

source ./scripts/functions.sh

PATH=/root/miniconda3/envs/cms/bin:${PATH}
# run the scheduled task to populate the database in the celery app
run "make run_dev_server"
