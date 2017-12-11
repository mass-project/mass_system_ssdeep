FROM alpine
RUN apk add --no-cache python3 && \
    apk add --no-cache git
# packages required for building ssdeep
RUN apk add --no-cache build-base && \
    apk add --no-cache python3-dev && \
    apk add --no-cache libffi && \
    apk add --no-cache libffi-dev && \
    apk add --no-cache py3-cffi && \
    apk add --no-cache automake && \
    apk add --no-cache libtool && \
    apk add --no-cache autoconf
COPY requirements.txt /
RUN pip3 install hurry.filesize
RUN BUILD_LIB=1 pip3 install -r /requirements.txt
ADD . /
ENTRYPOINT python3 ssdeep_analysis_instance.py
