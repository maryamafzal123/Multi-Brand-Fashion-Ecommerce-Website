# Brand Bazar by Mirsa

Full-stack multi-brand fashion e-commerce platform.
Live: https://brandbazarbymirsa.com

**Stack:** Next.js 16 (TypeScript, Zustand) | Django REST Framework | PostgreSQL (Supabase) | Cloudinary | JWT

## DevOps Setup

Besides the original deployment (Vercel + Render + Supabase), the app is also containerized and deployed on AWS EC2.

**Live EC2 deployment:** https://aws.brandbazarbymirsa.com

### Architecture

```
Browser -> HTTPS -> Nginx (EC2, ports 80/443)
                      |-- /api, /admin, /static -> Django + Gunicorn (container, :8000)
                      |-- everything else       -> Next.js (container, :3000)
Django -> Supabase PostgreSQL, Cloudinary
```

### What was done
- **Docker:** separate Dockerfiles for backend and frontend, one `docker-compose.yml`, `.dockerignore` so secrets never enter images.
- **CI/CD:** GitHub Actions builds both images on every push and publishes them to GitHub Container Registry (GHCR).
- **AWS EC2:** Ubuntu instance, Elastic IP, security group allowing only 22 (my IP), 80 and 443.
- **Nginx:** reverse proxy routing API and frontend traffic to the right container.
- **DNS + SSL:** Namecheap A record for the subdomain, free Let's Encrypt certificate via Certbot with auto-renewal.
- **Monitoring:** `healthcheck.sh` checks disk, memory, CPU load, container status and API response; runs every 5 minutes via cron and logs to a file.

### Run locally
```bash
cp .env.example .env      # fill in your values
docker compose up --build
# frontend: http://localhost:3000   backend: http://localhost:8000/api/products/
```

### Deploy on EC2
```bash
docker compose pull
docker compose up -d
docker compose ps
```

### Troubleshooting notes
| Problem | Cause | Fix |
|---|---|---|
| Frontend showed "No products" | `NEXT_PUBLIC_API_URL` included `/api`, but code also adds `/api/...`, so requests went to `/api/api/...` (404) | Set the URL without `/api` and rebuild the frontend image |
| Changing `NEXT_PUBLIC_API_URL` had no effect | `NEXT_PUBLIC_` variables are baked in at build time | Rebuild the image, a restart is not enough |
| Django returned 400 on the new domain | Domain missing from `ALLOWED_HOSTS` | Add it to the server `.env` and restart |
| First Docker build took ~26 min | No layer cache | Later builds are fast because dependency layers are cached |

### Key concepts
- **Build-time vs run-time variables:** `NEXT_PUBLIC_*` values are embedded in the frontend bundle during build. Backend variables from `.env` are injected when the container starts.
- **Reverse proxy:** only Nginx faces the internet; the app containers stay behind it.