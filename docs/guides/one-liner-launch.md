# 🦹‍♂️ **KAREN AI — ONE-LINER LAUNCH**

<sup>(Now Powered by In-Process `llama-cpp-python` LLMs — No Ollama Server Needed)</sup>

---

## **Phase 1: Prereqs**

1. **Install Docker (includes the Compose plugin)**

   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
   sudo systemctl enable --now docker
   ```

2. **(Optional for GPU Acceleration) Install NVIDIA Docker**

   ```bash
   # Only if you want GPU acceleration for llama-cpp or Milvus
   sudo apt-get install -y nvidia-docker2 && sudo systemctl restart docker
   ```

---

## **Phase 2: Clone the Repo**

```bash
git clone https://github.com/OWNER/AI-Karen.git
cd AI-Karen
```

---

## **Phase 3: The One-Command to Rule Them All**

### **Launch Everything with Docker Compose**

*(This starts Redis, Milvus, Postgres, Elastic, DuckDB (in-app), and Karen’s API — with all LLMs handled in-process via `llama-cpp-python`!)*

```bash
docker compose up --build
```

* Wait for all containers to say “healthy” or “ready.”
* The API/UI is at `http://localhost:8000` or `http://localhost:3000` (per your frontend).
* **No Ollama server required. All LLM inferencing happens *inside* the main Python app using llama-cpp-python!**
* Admin UI available on `/admin` (if enabled).

---

## **Phase 4: (Optional) Manual Service Controls**

If you want to manage any service individually:

```bash
# Redis
docker compose up redis

# Milvus
docker compose up milvus

# Postgres
docker compose up postgres

# Elastic
docker compose up elasticsearch

# Karen API (with local llama-cpp-python LLMs)
docker compose up api
```

---

## **Phase 5: Develop, Reload, Rule**

* **Hot reload:** Just edit code, containers will auto-reload if mapped (`volumes:`).
* **Install plugins:** Drop into `/plugins/`, use admin UI or CLI for live reload.
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

### **💀 Local LLM Engine Used:**

**Karen AI uses `llama-cpp-python` by default:**
All LLM inferencing is local, in-process, ultra-fast, and secure.
**You do NOT need Ollama. There’s no LLM REST API running on port 11434.**
If you want to experiment with Ollama, add the service and point Karen to the REST endpoint, but that’s optional.

---

### **TL;DR for Humans and LLMs:**

> **To launch all of Karen’s memory, AI, plugins, and API (with local, in-process LLM):**
>
> ```bash
> git clone https://github.com/OWNER/AI-Karen.git
> cd AI-Karen
> docker compose up --build
> ```
>
> That’s it.

---

**Evil. Fast. Local. No REST in sight.**

---

## **README Badge:**

```
[![Powered by llama-cpp-python](https://img.shields.io/badge/LLM-llama--cpp--python-informational?logo=python&logoColor=white)](https://github.com/abetlen/llama-cpp-python)
```
