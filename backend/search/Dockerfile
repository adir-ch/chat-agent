FROM golang:1.22-alpine AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY . .

RUN go build -o search ./cmd/search

FROM alpine:3.20

WORKDIR /srv

COPY --from=builder /app/search ./search

EXPOSE 8090

CMD ["/srv/search"]

