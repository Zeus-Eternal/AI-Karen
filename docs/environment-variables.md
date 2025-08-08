# Environment Variables

Before running `main.py`, copy `.env.example` to `.env` and set the following mandatory variables:

| Variable | Purpose | Example Value |
| --- | --- | --- |
| `SECRET_KEY` | JWT signing key for API tokens | `SECRET_KEY=super-secret-key-change-me` |
| `POSTGRES_URL` | PostgreSQL connection string | `POSTGRES_URL=postgresql://karen_user:karen_secure_pass_change_me@postgres:5432/ai_karen` |
| `REDIS_URL` | Redis connection string | `REDIS_URL=redis://redis:6379/0` |
| `KARI_LOG_DIR` | Directory for application logs | `KARI_LOG_DIR=./logs` |
| `KARI_MODEL_SIGNING_KEY` | Verifies models loaded by the orchestrator | `KARI_MODEL_SIGNING_KEY=dev-signing-key-1234567890abcdef` |
| `KARI_DUCKDB_PASSWORD` | Encryption password for automation DuckDB database | `KARI_DUCKDB_PASSWORD=dev-duckdb-pass` |
| `KARI_JOB_SIGNING_KEY` | Signs automation jobs for integrity checks | `KARI_JOB_SIGNING_KEY=dev-job-key-456` |
| `KARI_JOB_ENC_KEY` | Base64 encoded 32-byte key for automation job encryption | `KARI_JOB_ENC_KEY=MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo=` |

These values can be stored in a `.env` file in the repository root or supplied through your hosting environment.
