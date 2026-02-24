# Build stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o oob-svc ./main.go

# Final stage
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /app/oob-svc /oob-svc

EXPOSE 8080

ENTRYPOINT ["/oob-svc"]
