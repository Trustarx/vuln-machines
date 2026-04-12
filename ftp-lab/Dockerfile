FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

COPY ftp-files/ /ftp-files/
COPY proftpd.conf /proftpd.conf
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh && /setup.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 21 80 22

ENTRYPOINT ["/entrypoint.sh"]
