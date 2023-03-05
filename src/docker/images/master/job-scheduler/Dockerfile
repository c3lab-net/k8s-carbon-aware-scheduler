FROM gitlab-registry.nrp-nautilus.io/c3lab/common/python-flask:3.10-bullseye
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

# RUN pip3 install numpy arrow requests pyyaml
RUN pip3 install "marshmallow-dataclass[enum,union]"
RUN pip3 install requests pyyaml

RUN apt-get update
RUN apt-get install -y amqp-tools

COPY api /api
WORKDIR /
CMD [   "gunicorn", \
        "-b=:8000", \
        "--workers=4", \
        "--log-level=info", \
        "--access-logfile", "-", \
        "--access-logformat", "%({X-Real-IP}i)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"", \
        "api:create_app()" \
]
