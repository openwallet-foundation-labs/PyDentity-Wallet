FROM ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.2.0

USER root

# install plugins as binaries
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@main#subdirectory=webvh
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@main#subdirectory=connection_update
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@main#subdirectory=basicmessage_storage
RUN pip install git+https://github.com/openwallet-foundation/acapy-plugins@main#subdirectory=multitenant_provider

USER $user
COPY ./configs.yml configs.yml

CMD ["start", "--arg-file", "configs.yml"]
