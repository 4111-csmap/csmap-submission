#!/bin/sh

pip3 install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
