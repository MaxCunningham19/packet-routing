FROM ubuntu
WORKDIR /compnets
RUN apt-get update
RUN apt-get install -y net-tools netcat tcpdump inetutils-ping python3
CMD ["/bin/bash"]
