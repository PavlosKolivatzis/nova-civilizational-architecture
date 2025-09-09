```mermaid
sequenceDiagram
    participant User
    participant S3 as Slot 3
    participant S2 as Slot 2
    participant S7 as Slot 7
    participant O as Orchestrator

    User ->> S3: submit content
    S3 ->> S2: DELTA_THREAT@1
    S2 ->> S7: PRODUCTION_CONTROL@1
    S7 ->> O: escalate / throttle decision
    O -->> User: response
```
