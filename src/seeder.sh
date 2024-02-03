#!/bin/sh
rm media/ -r 
python3 manage.py flush --no-input
python3 manage.py sqlflush 
python3 manage.py makemigrations users subscriptions
python3 manage.py migrate
python3 manage.py seed_users
