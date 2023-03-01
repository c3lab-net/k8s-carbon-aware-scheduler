FROM python:3-alpine
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

RUN apk add --update coreutils rabbitmq-c-utils
# RUN apk add --update python3 py3-pip
RUN apk --no-cache add musl-dev g++
RUN pip3 install numpy
RUN pip3 install arrow pyyaml flask flask_restful psycopg2-binary webargs requests gunicorn marshmallow_dataclass

COPY energy-data/api /api
WORKDIR /
CMD [   "gunicorn", \
        "-b=:8000", \
        "--workers=4", \
        "--log-level=info", \
        "--access-logfile", "-", \
        "--access-logformat", "%({X-Real-IP}i)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"", \
        "api:create_app()" \
]
