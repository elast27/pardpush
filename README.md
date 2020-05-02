# PardPush

[![Python Version](https://img.shields.io/badge/python-3.6-brightgreen.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-2.0-brightgreen.svg)](https://djangoproject.com)

Domain: http://pardpush.cs.lafayette.edu/

## How to run

0. Setup
https://docs.google.com/document/d/1RNd1AdDJ3Nki7hKG13TTajcS8xBCer3QgMXsiGRniT0/edit

1. Activate virtual environment and install the requirements:

```bash
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

2. Create the database:

```bash
python manage.py migrate
```

3. run the development server:

```bash
python manage.py runserver
```

The project will be available at **127.0.0.1:8000**.
