# sim-engine

Rust gRPC simulation engine prototype for AGD.

## What it implements

- `RunScenario(SimRequest) -> stream SimEvent`
- `PauseRun(RunRef) -> RunStatus`
- `ResumeRun(RunRef) -> RunStatus`
- `StepTurn(RunRef) -> SimEvent`
- `GetState(RunRef) -> SimState`
- `InjectEvent(EventInjection) -> Ack`

Proto contract: `proto/sim_engine.proto`.

## Local build

From repository root:

```bash
docker compose -f docker-compose.dev.yml build sim-engine
```

## Run

```bash
docker compose -f docker-compose.dev.yml up sim-engine
```

Default bind:

- host: `0.0.0.0`
- port: `50051`

Configured through:

- `SIM_ENGINE_HOST`
- `SIM_ENGINE_PORT`

## Current state

This is an in-memory engine implementation intended to establish the gRPC interface and runtime wiring. It does not yet persist state or execute full high-fidelity combat physics.
