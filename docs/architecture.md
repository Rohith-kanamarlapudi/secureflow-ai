# SecureFlow AI — Architecture

## 1. System Architecture

```mermaid
flowchart LR
    U[User / Browser]

    FE[React + Vite + Tailwind]
    API[FastAPI Backend]

    AUTH[Authentication + RBAC]
    DOC[Document Service]
    CRYPTO[Encryption / Integrity / Signature]
    SHARE[Sharing + Versioning]
    AUDIT[Audit Logging]
    KMS[KMS Abstraction]
    AGENT[Security Investigation Agent]

    DB[(PostgreSQL)]
    REDIS[(Redis)]
    MINIO[(MinIO Object Storage)]
    WORKER[Celery / RQ Worker]

    U --> FE
    FE -->|REST / JWT| API

    API --> AUTH
    API --> DOC
    API --> CRYPTO
    API --> SHARE
    API --> AUDIT
    API --> KMS
    API --> AGENT

    DOC --> DB
    DOC --> MINIO

    CRYPTO --> MINIO
    CRYPTO --> DB

    SHARE --> DB
    AUTH --> DB
    AUDIT --> DB
    KMS --> DB

    API --> REDIS
    API --> WORKER

    WORKER --> CRYPTO
    WORKER --> MINIO
    WORKER --> DB

    AGENT -->|Read-only| AUDIT
    AGENT -->|Read-only| DOC