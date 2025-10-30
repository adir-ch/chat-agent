FROM golang:1.22-alpine AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY . .

RUN go build -o adapter ./cmd/adapter

FROM alpine:3.20

WORKDIR /srv

COPY --from=builder /app/adapter ./adapter

VOLUME ["/data"]

ENV ADAPTER_DB_PATH=/data/adapter.db

EXPOSE 8080

CMD ["/srv/adapter"]

