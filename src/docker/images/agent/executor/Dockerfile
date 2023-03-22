FROM gitlab-registry.nrp-nautilus.io/c3lab/common/kubectl:1.23.14
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

RUN apk add --update python3 py3-pip coreutils rabbitmq-c-utils
RUN pip install pyyaml psycopg2-binary

COPY src/* /

CMD [ "/worker.py" ]
