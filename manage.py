#!/usr/bin/env python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s -- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

from flask_script import Manager

from app import application
from app.commands.dev import DevCommand

app = application.get_or_create()

if __name__ == '__main__':
    manager = Manager(app)
    manager.add_command('dev', DevCommand)
    manager.run()
