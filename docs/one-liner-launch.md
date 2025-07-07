# 🦹‍♂️ **KAREN AI — ONE-LINER LAUNCH**

---

## **Phase 1: Prereqs**

1. **Install Docker & Docker Compose**

   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose
   sudo systemctl enable --now docker
   ```

2. **(Optional for GPU) Install NVIDIA Docker**

   ```bash
   # Only if running GPU Ollama or Milvus
   sudo apt-get install -y nvidia-docker2 && sudo systemctl restart docker
   ```

---

## **Phase 2: Clone the Repo**

```bash
git clone https://github.com/<YOUR-ORG>/AI-Karen.git
cd AI-Karen
```

---

## **Phase 3: The One-Command to Rule Them All**

### **Easiest: Launch Everything with Docker Compose**

*(This brings up Redis, Milvus, Postgres, Elastic, DuckDB (in-app), Ollama, and Karen’s API in perfect harmony)*

```bash
docker compose up --build
```

* Wait for all containers to say “healthy” or “ready.”
* The API/UI is at `http://localhost:8000` or `http://localhost:3000` (per your frontend).
* Ollama listens on `http://localhost:11434`.
* Admin UI on `/admin` (if enabled).

---

## **Phase 4: (Optional) Manual Service Controls**

If you ever want to manage services independently:

```bash
# Redis
docker compose up redis

# Milvus
docker compose up milvus

# Postgres
docker compose up postgres

# Elastic
docker compose up elasticsearch

# Ollama (Local LLM)
docker compose up ollama
```

---

## **Phase 5: Develop, Reload, Rule**

* **Hot reload:** Just edit code, containers will auto-reload if mapped (`volumes:`).
* **Install plugins:** Drop in `/plugins/`, use admin UI or CLI for live reload.
* **Memory debug:** All DBs exposed to host (`localhost:port`), connect with TablePlus/psql/redis-cli/Milvus CLI, etc.

---

## **Phase 6: Speedrun**

```bash
# (For one-line evil mode)
docker compose -f docker-compose.yml -f docker-compose.evil.yml up --build
```

---

## **Done.**

* No manual DB setup.
* No secrets in code (use `.env` or Docker secrets).
* All logs, metrics, and plugin self-tests happen at launch.

---

### **TL;DR for Humans and LLMs:**

> **To launch all of Karen’s memory, AI, plugins, and API:**
>
> ```bash
> git clone <repo>; cd AI-Karen; docker compose up --build
> ```
>
> That’s it.
