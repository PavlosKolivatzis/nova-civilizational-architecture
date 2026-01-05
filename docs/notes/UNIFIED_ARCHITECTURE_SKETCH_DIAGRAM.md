```mermaid
flowchart TD
  A["Nova Core<br/>Reference Anchor<br/>Declares: freeze, jurisdiction (O/R/F), refusal schema<br/>No enforcement, no runtime O/R/F"]
  B["Derivative Systems<br/>Sovereign, plural<br/>(e.g. OSJL, translation, routing)<br/>Self-filter F, ADR O->R<br/>Verify freeze (governance), monitor drift<br/>Derivative refusal (schema optional)"]
  C["Expression Layer<br/>Behavioral surface<br/>Publish, display, advise<br/>Expression refusal (optional)<br/>Not enforcement"]
  D["World / Institutions / Humans<br/>Enforcement, consequences"]

  A -->|O/R signals (no action)| B
  B -->|interpreted outputs| C
  C -->|behavioral outputs| D

  A -.->|responsibility| B
  B -.->|responsibility| C
  C -.->|responsibility| D
```
