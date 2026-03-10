# ProfAssistant — Azure VM Deployment Guide

Deploy the full stack (frontend + backend + MCP) on a **single Azure VM** with **automatic HTTPS** via Caddy + DuckDNS. Ideal for testing with a small number of users.

**Cost**: ~$30/month for the recommended B2s VM, or ~$5/month for a minimal B1s.

---

## Prerequisites

- An **Azure subscription**
- **Azure CLI** installed locally (`az` command) — [Install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux)
- A free **DuckDNS** account — [duckdns.org](https://www.duckdns.org) (login with GitHub/Google)
- Your `.env` values ready (OpenAI API key, secrets, etc.)

---

## Step 1 — Register a DuckDNS subdomain

1. Go to [duckdns.org](https://www.duckdns.org) and log in (GitHub or Google)
2. Pick a subdomain name, e.g., `profassistant` → you get `profassistant.duckdns.org`
3. Leave the IP blank for now — you'll set it after creating the VM

---

## Step 2 — Create the Azure VM

Run these commands from your **local machine**:

```bash
# Login to Azure
az login

# Create a resource group (westeurope is closest for Hungary)
az group create \
  --name profassistant-rg \
  --location italynorth

# Create the VM (Standard_B2als_v2 = 2 vCPU, 4 GB RAM)
# This also generates SSH keys if you don't have them
az vm create \
  --resource-group profassistant-rg \
  --name profassistant-vm \
  --image Ubuntu2404 \
  --size Standard_B2als_v2 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard

# Open ports 80 (HTTP redirect) and 443 (HTTPS)
az vm open-port \
  --resource-group profassistant-rg \
  --name profassistant-vm \
  --port 80 \
  --priority 1010
az vm open-port \
  --resource-group profassistant-rg \
  --name profassistant-vm \
  --port 443 \
  --priority 1020

# Get the public IP
az vm show \
  --resource-group profassistant-rg \
  --name profassistant-vm \
  --show-details \
  --query publicIps -o tsv
```

**Now go back to DuckDNS** and set the IP of your subdomain to the public IP you just got.

---

## Step 3 — Set up the VM

```bash
# SSH into the VM
ssh azureuser@<VM_PUBLIC_IP>

# Create the app directory
sudo mkdir -p /opt/profassistant
sudo chown azureuser:azureuser /opt/profassistant

# Clone your repo
git clone https://github.com/<your-username>/profAssistant.git /opt/profassistant

# Run the setup script (installs Docker)
cd /opt/profassistant
bash deploy/vm-setup.sh

# IMPORTANT: log out and back in for Docker group to take effect
exit
ssh azureuser@<VM_PUBLIC_IP>
```

---

## Step 4 — Configure environment

```bash
ssh azureuser@<VM_PUBLIC_IP>
cd /opt/profassistant

# Create .env from template
cp .env.example .env

# Edit with your actual values
nano .env
```

**Minimum required values** in `.env`:

```dotenv
# Required
OPENAI_API_KEY=sk-...your-real-key...
JWT_SECRET=<generate-with-command-below>
ENCRYPTION_KEY=<generate-with-command-below>
ADMIN_EMAIL=admin@yourschool.edu
ADMIN_PASSWORD=a-strong-password-here

# Domain & HTTPS (use the DuckDNS subdomain you registered)
DOMAIN_NAME=profassistant.duckdns.org
ALLOWED_ORIGINS=https://profassistant.duckdns.org
```

Generate secrets:

```bash
python3 -c "import secrets,base64,os; print('JWT_SECRET=' + secrets.token_hex(32)); print('ENCRYPTION_KEY=' + base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

---

## Step 5 — Deploy

```bash
cd /opt/profassistant
bash deploy/deploy.sh
```

The script will:

1. Validate your `.env` (including `DOMAIN_NAME`)
2. Build all Docker images
3. Start the services (including Caddy for HTTPS)
4. Caddy automatically provisions a Let's Encrypt TLS certificate
5. Health-check that HTTPS is responding

First build takes **3-5 minutes**. Certificate provisioning takes ~30 seconds extra. After that, visit: **https://profassistant.duckdns.org** (your subdomain)

---

## Day-to-day Operations

### View logs

```bash
cd /opt/profassistant
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
# Or just one service:
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

### Redeploy after code changes

```bash
# On local machine: push changes, then on VM:
cd /opt/profassistant
git pull
bash deploy/deploy.sh
```

### Quick restart (no rebuild)

```bash
bash deploy/deploy.sh --quick
```

### Stop everything

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### Check disk / resource usage

```bash
docker system df          # Docker disk usage
df -h                     # VM disk usage
free -h                   # RAM usage
docker stats --no-stream  # Per-container CPU/RAM
```

---

## Automatic Deploys (CI/CD)

A GitHub Actions workflow (`.github/workflows/deploy.yml`) auto-deploys on every push to `main`.

### One-time setup

1. **Add 3 secrets** in your GitHub repo → Settings → Secrets and variables → Actions:

   | Secret        | Value                                                  |
   | ------------- | ------------------------------------------------------ |
   | `VM_HOST`     | VM public IP or `profassistant.duckdns.org`            |
   | `VM_USERNAME` | `azureuser`                                            |
   | `VM_SSH_KEY`  | Contents of your SSH private key (`cat ~/.ssh/id_rsa`) |

### How it works

1. You push to `main`
2. GitHub Actions SSHes into the VM
3. Runs `git pull` + `bash deploy/deploy.sh`
4. Full rebuild takes ~3-5 minutes

You can also trigger it manually from the **Actions** tab in GitHub.

---

## Estimated Costs

| Resource        | Size               | Monthly Cost   |
| --------------- | ------------------ | -------------- |
| VM (B2s)        | 2 vCPU, 4 GB RAM   | ~$30           |
| OS Disk         | 30 GB Standard SSD | ~$2            |
| Public IP       | Static             | ~$3            |
| **Total (B2s)** |                    | **~$35/month** |

---

## Cleanup

When done, delete everything to stop charges:

```bash
az group delete --name profassistant-rg --yes --no-wait
```

---

## Troubleshooting

| Issue                         | Solution                                                                                                                                                 |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Can't connect to HTTPS        | Check NSG has port 443 open: `az vm open-port --resource-group profassistant-rg --name profassistant-vm --port 443 --priority 1020`                      |
| Certificate not provisioning  | Check Caddy logs: `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy`. Ensure DuckDNS IP matches VM IP and port 80/443 are open |
| DNS not resolving             | Verify at DuckDNS that IP is set. Test: `nslookup profassistant.duckdns.org`                                                                             |
| Docker permission denied      | Log out and back in after `vm-setup.sh`, or use `sudo docker ...`                                                                                        |
| Backend crashes (OOM on B1s)  | Check `docker stats`; consider upgrading to B2s                                                                                                          |
| Cookies not working           | Ensure `ALLOWED_ORIGINS=https://your-subdomain.duckdns.org` (no trailing slash, must be `https`)                                                         |
| Build fails (npm/pip timeout) | VM might have slow network; retry: `bash deploy/deploy.sh`                                                                                               |
| MCP health check fails        | Wait a minute and redeploy; the Wikipedia MCP server can be slow on first start                                                                          |
