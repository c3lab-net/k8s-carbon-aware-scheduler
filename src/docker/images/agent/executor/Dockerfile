FROM gitlab-registry.nrp-nautilus.io/c3lab/common/kubectl:1.23.14
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

RUN apk add --update python3 coreutils rabbitmq-c-utils

COPY entrypoint.sh /
RUN chmod u+x /entrypoint.sh
COPY worker.py /
RUN chmod u+x /worker.py

CMD [ "/entrypoint.sh" ]
