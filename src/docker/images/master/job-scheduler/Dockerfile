FROM gitlab-registry.nrp-nautilus.io/c3lab/common/python-flask:3.10-bullseye
MAINTAINER Yibo Guo <nil.yibo@gmail.com>

# RUN pip3 install numpy arrow requests pyyaml
RUN pip3 install "marshmallow-dataclass[enum,union]"

COPY job-scheduler.py /
RUN chmod u+x /job-scheduler.py

CMD [ "/job-scheduler.py" ]
