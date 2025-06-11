FROM node:18-alpine

RUN npm install -g @mockoon/cli@9.2.0

# Install curl for healthcheck and tzdata for timezone support.
RUN apk --no-cache add curl tzdata

COPY ./mastodon_api.json /home/mockoon/mastodon_api.json

# Do not run as root.
RUN adduser --shell /bin/sh --disabled-password --gecos "" mockoon

RUN chown -R mockoon /home/mockoon/mastodon_api.json

USER mockoon
WORKDIR /home/mockoon

EXPOSE 3001

ENTRYPOINT ["mockoon-cli","start","--data","/home/mockoon/mastodon_api.json","--port","3001"]
