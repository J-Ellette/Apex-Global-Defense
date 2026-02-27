FROM rust:latest AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends protobuf-compiler && rm -rf /var/lib/apt/lists/*
COPY Cargo.toml Cargo.toml
COPY build.rs build.rs
COPY proto proto
COPY src src

RUN cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/target/release/sim-engine /usr/local/bin/sim-engine

EXPOSE 50051

ENV SIM_ENGINE_HOST=0.0.0.0
ENV SIM_ENGINE_PORT=50051

CMD ["sim-engine"]