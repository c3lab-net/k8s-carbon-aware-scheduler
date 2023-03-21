FROM alpine:3.17.2
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

RUN apk --no-cache add postgresql14-client

COPY schemas /schemas
COPY entrypoint.sh /

ENTRYPOINT [ "/entrypoint.sh" ]
