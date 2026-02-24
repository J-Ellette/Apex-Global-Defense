# Build stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o auth-svc ./main.go

# Final stage
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /app/auth-svc /auth-svc

EXPOSE 8080

ENTRYPOINT ["/auth-svc"]
