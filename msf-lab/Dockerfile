FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

COPY setup.sh /setup.sh
RUN chmod +x /setup.sh && /setup.sh

COPY services/ /services/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# FTP + backdoor shell
EXPOSE 21 6200
# Shellshock CGI
EXPOSE 80
# distcc RCE
EXPOSE 3632

ENTRYPOINT ["/entrypoint.sh"]
