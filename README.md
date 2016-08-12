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

At this time, bug with salt in debug mode so run the server using gunicorn

    ./webserver/gunicorn-eventlet.sh

The second component of this application is the Celery workers, which must be
started with the following command:

    python manage.py celery


##  Usage

### Before start

You need to create a new user

    python manage.py createuser awesome_user

The password will then be displayed on the command line

### Basic : Authentification

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

### List availables tasks

    curl -i -X GET \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/tasks

### Ping machines (salt ping)

#### Ping one minion synchronously

    curl -i -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/ping/<minion_from_keys>

#### Ping a list minion synchronously

    curl -X POST -i \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d '{"target":["minion1","minion2"]}' \
        ${URL}/api/v1.0/ping

#### Ping one minion asynchronously

    curl -i -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/tasks/ping/<minion_from_keys>

#### Ping a list minion asynchronously

    curl -X POST -i \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d '{"target":["minion1","minion2"]}' \
        ${URL}/api/v1.0/tasksping

## Working with asynchronous request

When performing and asynchronous request, you will get a 202.
In the response, there is a header location.
Use this location using GET, you will get a 202 until the end
of the request and then the response.

Example with async ping

    curl -i -X POST \
         -H "Authorization: Bearer ${TOKEN}" \
         ${URL}/api/v1.0/tasks/ping/my_awesome_minion

In the answer you will get

    HTTP/1.1 202 ACCEPTED
    Server: gunicorn/19.6.0
    Date: Fri, 12 Aug 2016 08:37:24 GMT
    Connection: keep-alive
    Location: http://127.0.0.1:5000/api/v1.0/tasks/status/a1d652eb-0311-49b9-abbe-aa141ddd7447
    Content-Type: text/html; charset=utf-8
    Content-Length: 0

Now just get the location 

    curl -i \
        -H "Authorization: Bearer ${TOKEN}" \
        ${URL}/api/v1.0/tasks/status/a1d652eb-0311-49b9-abbe-aa141ddd7447

And you'll get full answer

    HTTP/1.1 200 OK
    Server: gunicorn/19.6.0
    Date: Fri, 12 Aug 2016 08:39:01 GMT
    Connection: keep-alive
    Content-Type: application/json
    Content-Length: 50

    {
      "my_awesome_minion": true
    }
