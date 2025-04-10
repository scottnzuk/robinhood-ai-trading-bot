# Activepieces Docker Setup (macOS M1 Pro)

1. **Start Docker Desktop**

- Open **Docker Desktop** from Applications or Spotlight.
- Wait until Docker is fully running (whale icon stable in menu bar).

2. **Launch Activepieces**

In your project root:

```bash
docker compose -f docker-compose-activepieces.yml up -d
```

3. **Access Activepieces**

- Open browser: [http://localhost:9912](http://localhost:9912)

4. **Stop Activepieces**

```bash
docker compose -f docker-compose-activepieces.yml down
```

---

**Note:** All other MCP servers run natively without Docker.