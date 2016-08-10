# Alkivi ProjectY API

This repository contains the code for the API.

## Requirements

You should install this dependencies (debian)

    apt-get install libyaml-dev libzmq-dev python-virtualenv libpython-dev

## Installation

Python 2.7+ only because of salt compatibility.

As usual, create a virtual environment and install the requirements with pip.

    pip install -r requirements.txt

A broker for messages in necessary, default to redis (rabbitmq to come)

    apt-get install redis-server

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

So far, due to salt implemention of wheel, we should start the program as root.
Moving to a standard user is in the backlog.

There is two components. First the server to dispatch request

    python manage.py runserver

The second component of this application is the Celery workers, which must be
started with the following command:

    python manage.py celery


##  Usage

### Basic : Authentificatin

By default listen on localhost port 5000. I'll defined the url as:

    URL='http://127.0.0.1:5000'

Get a token

    curl -i -X POST \
        -u 'user:password' \
        ${URL}/api/v1.0/tokens

Use the token then to get user

    TOKEN='previous_token'
    curl -i -X GET \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/users

### List availables keys

    curl -i -X GET \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/keys

### Ping one minion

    curl -i -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/ping/<minion_from_keys>

### Ping a list minion

    curl -X POST -i \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d '{"target":["minion1","minion2"]}' \
        ${URL}/api/v1.0/ping

