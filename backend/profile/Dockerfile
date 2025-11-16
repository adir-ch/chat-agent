FROM golang:1.22-alpine AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY . .

RUN go build -o profile ./cmd/profile

FROM alpine:3.20

WORKDIR /srv

COPY --from=builder /app/profile ./profile

VOLUME ["/data"]

ENV PROFILE_DB_PATH=/data/profile.db

EXPOSE 8080

CMD ["/srv/profile"]

