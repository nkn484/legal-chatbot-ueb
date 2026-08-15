# Threat data flow — design only

Core lines are solid; LATER paths are dashed and default denied. This is not an implementation claim.

```mermaid
flowchart LR
  subgraph TB01[TB-01 Public]
    U[Browser] --> A[Admin browser]
  end
  subgraph TB02[TB-02 Gateway]
    U --> G[API Gateway]
    A --> G
  end
  subgraph TB03[TB-03 Identity]
    G <--> I[Identity]
    I --> IS[(Identity store)]
  end
  subgraph TB04[TB-04 Document]
    D[Document] --> DS[(Document store)]
    D --> Q[Quarantine object]
  end
  subgraph TB05[TB-05 Processing sandbox]
    Q --> P[Processing sandbox]
    P --> PA[Artifact store]
  end
  subgraph TB06[TB-06 Service and broker]
    G --> D[Document]
    G --> P[Processing]
    G --> AU[Audit]
    G --> C[Chat]
    D --> B[Broker]
    P --> B
    B --> X[Retry/DLQ]
    B --> IX[Index]
    B --> AU[Audit]
    AU --> AS[(Audit store)]
  end
  subgraph TB07[TB-07 Retrieval]
    C --> R
    R <--> IX
    R --> RS[(Retrieval store)]
    IX --> XS[(Index store)]
  end
  subgraph TB08[TB-08 Citation]
    R --> C
    C --> CT[Citation]
    CT --> CS[(Citation store)]
    CT --> IX
    CT --> D
    CT --> P
  end
  subgraph TB09[TB-09 Response]
    C --> U
  end
  subgraph TB11[TB-11 Operations]
    T[Telemetry]
    K[KMS/Vault] --> AU
  end
  G --> T
  D -. DENIED .-> BK[Backup/restore]
  P -. DENIED .-> BK
  C -. DENIED .-> BK
  I --> K
  D --> K
  P --> K
  C --> K
  AU --> K
  PR[Provider] -. DENIED .-> E[DNS/Egress]
  PR -. DENIED .-> PSM[Provider secret manager]
  E -. DENIED .-> EP[External Provider]
  SC[Source connector] -. DENIED .-> E
  D -. DENIED .-> SSM[Source secret manager]
  E -. DENIED .-> TS[Third-party source]
  C -. DENIED .-> F[Feedback]
  F -. DENIED .-> EV[Evaluation]
  F --> FS[(Feedback store)]
  EV --> ES[(Evaluation store)]
```

## Registry flow table
| Flow IDs | Data / sensitivity | Primary control |
|---|---|---|
| FLOW-01, FLOW-02, FLOW-03, FLOW-31 | gateway ingress and routed PDF/bearer; PII/secret body forbidden | CTRL-AUTH-003 |
| FLOW-04, FLOW-05 | isolated local/demo identity and service context; secret body forbidden | CTRL-AUTH-003 |
| FLOW-06, FLOW-07, FLOW-08 | quarantine/original/artifact; PII body forbidden | CTRL-UPLOAD-001 |
| FLOW-09, FLOW-10, FLOW-11 | schema/type/hash/revision only; no body/DLQ body | CTRL-EVENT-001 |
| FLOW-12, FLOW-13, FLOW-14, FLOW-15, FLOW-35 | published references, retrieval context, evidence/sufficiency/refusal | CTRL-RAG-002 |
| FLOW-16, FLOW-17, FLOW-18, FLOW-36 | Chat→Citation opaque context; Index/Document/Processing validation | CTRL-CITE-001 |
| FLOW-19 | public answer/refusal and citation | CTRL-CITE-002 |
| FLOW-20, FLOW-21 | sanitized audit / redacted telemetry | CTRL-AUDIT-001 |
| FLOW-22, FLOW-23 | LATER backup/DR; DENIED_NOT_SENT, REQ-OPS-002 | CTRL-PRIV-003 |
| FLOW-24 | Core scoped cryptographic-operation metadata; no raw key | CTRL-KEY-001 |
| FLOW-25, FLOW-26, FLOW-37 | LATER provider endpoint/content/secret; DENIED_NOT_SENT | CTRL-PRIV-004 |
| FLOW-27, FLOW-28 | LATER feedback/evaluation; DENIED_NOT_SENT | CTRL-RELEASE-001 |
| FLOW-29, FLOW-30, FLOW-38 | LATER source endpoint/content/secret; DENIED_NOT_SENT | CTRL-SOURCE-001 |
| FLOW-32, FLOW-33, FLOW-34 | gateway→Processing job query, Audit query, Chat question route | CTRL-AUTH-003 |

The complete source, destination, protocol, class, retention, protection, and owner fields are authoritative in `contracts/security/privacy-data-map.yaml`.
