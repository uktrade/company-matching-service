#!/usr/bin/env python
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s -- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

env = {**os.environ, 'FLASK_APP': "app.application:get_or_create()"}

cmd = ['flask'] + sys.argv[1:]
subprocess.run(cmd, env=env)
