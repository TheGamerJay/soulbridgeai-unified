#!/bin/bash
exec gunicorn -c gunicorn.conf.py app:app