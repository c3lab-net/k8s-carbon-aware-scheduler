FROM alpine:3.17.2
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

RUN apk add --update python3 coreutils rabbitmq-c-utils

COPY job-scheduler.py /
RUN chmod u+x /job-scheduler.py

CMD [ "/job-scheduler.py" ]
