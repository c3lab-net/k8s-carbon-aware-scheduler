FROM gitlab-registry.nrp-nautilus.io/c3lab/common/python-flask:3.10-bullseye
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

RUN pip3 install numpy arrow requests pyyaml
RUN pip3 install psycopg2-binary marshmallow_dataclass
RUN pip3 install Flask-Caching

COPY energy-data/api /api
WORKDIR /
CMD [   "gunicorn", \
        "-b=:8000", \
        "--workers=4", \
        "--log-level=info", \
        "--access-logfile", "-", \
        "--access-logformat", "%({X-Real-IP}i)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s %(M)s \"%(f)s\" \"%(a)s\"", \
        "api:create_app()" \
]
