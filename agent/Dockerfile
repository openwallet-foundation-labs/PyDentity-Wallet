FROM ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.2.4

USER root

# install plugins as binaries
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@1.2.4#subdirectory=webvh
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@1.2.4#subdirectory=connection_update
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@1.2.4#subdirectory=basicmessage_storage
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@1.2.4#subdirectory=multitenant_provider

USER $user
COPY ./configs.yml configs.yml

CMD ["start", "--arg-file", "configs.yml"]
