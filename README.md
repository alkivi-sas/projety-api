# Alkivi ProjectY API

This repository contains the code for the API.

## Installation

Python 2.7+ only because of salt compatibility.

As usual, create a virtual environment and install the requirements with pip.

    pip install -r requirements.txt

## Detailed installation

All is done using a standart user.

### Clone repo and install virtualenvyy

    git clone git@git.alkivi.fr:alkivi/projety-api.git ~/projety-api
    cd ~/projety-api
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

### Install git-hooks

At every commit, we check for lint and test errors.

    cd ~/projety-api
    ./git-hooks/create-hook-symlinks

## Running

As a standart user (cf detailed installation):

    cd ~/projety-api
    python manage.py runserver

##  Usage

By default listen on localhost port 5000.
Get a token

    curl -X POST -i -u 'user:password' http://127.0.0.1:5000/api/v1.0/tokens

Use the token then to get user
    
    curl -i -H "Authorization: Bearer previoustoken" http://127.0.0.1:5000/api/v1.0/users
