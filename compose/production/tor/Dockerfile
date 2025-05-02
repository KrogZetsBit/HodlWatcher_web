FROM alpine:3.15
RUN apk --no-cache add tor
COPY ./compose/production/tor/torrc /torrc
USER tor
ENTRYPOINT ["tor"]
CMD ["-f", "/torrc"]
