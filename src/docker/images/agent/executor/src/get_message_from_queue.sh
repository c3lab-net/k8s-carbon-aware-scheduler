#!/bin/sh

/usr/bin/amqp-consume --url=$BROKER_URL -q "$QUEUE_PERFIX.$REGION" -c 1 cat
