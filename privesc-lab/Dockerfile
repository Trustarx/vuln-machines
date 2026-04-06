FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iputils-ping \
    cron \
    sudo \
    vim \
    openssh-server \
    openssh-client \
    libcap2-bin \
    net-tools \
    curl \
    wget \
    nmap \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask

WORKDIR /app
COPY app.py /app/app.py
COPY setup-vulns.sh /app/setup-vulns.sh
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/setup-vulns.sh /app/entrypoint.sh
RUN /app/setup-vulns.sh

EXPOSE 8080 22

ENTRYPOINT ["/app/entrypoint.sh"]
