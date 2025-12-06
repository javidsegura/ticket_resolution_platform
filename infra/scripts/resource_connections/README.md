# Resource Connections

Scripts for establishing connections to remote resources (SSH, database tunnels, port forwarding) with automatic secret management.

## 📁 Directory Structure

```
resource_connections/
├── create_connection.py          # Main connection handler
├── utils/
│   ├── models/                   # Pydantic models for Terraform outputs
│   │   ├── production.py         # Production connection models (AWS & Azure)
│   │   └── staging.py            # Staging connection models
│   └── secrets/                  # Secret fetchers
│       ├── ssh.py                # SSH key fetcher from AWS Secrets Manager
│       └── db.py                 # DB credentials fetcher from AWS/Azure
```

## 🎯 Components

### Connection Handler
- **`create_connection.py`** - Establishes SSH, database tunnels, and port forwarding connections

### Models (`utils/models/`)
- **`production.py`** - AWS and Azure production connection models
- **`staging.py`** - AWS staging connection model (with bastion host)

### Secret Fetchers (`utils/secrets/`)
- **`ssh.py`** - Fetches SSH keys from AWS Secrets Manager, caches in `~/.ssh/`
- **`db.py`** - Extracts database credentials from AWS Secrets Manager or Azure Key Vault

## 🚀 Usage

### SSH to Server

```bash
# Production
make -C infra connection-ssh-web-server \
  ENVIRONMENT=production \
  CLOUD_PROVIDER=aws

# Staging (via bastion)
make -C infra connection-ssh-web-server \
  ENVIRONMENT=staging \
  CLOUD_PROVIDER=aws
```

### Database Tunnel

```bash
make -C infra connection-db \
  ENVIRONMENT=production \
  CLOUD_PROVIDER=aws

# Then connect
mysql -h 127.0.0.1 -P 3307 -u root -p
```

### Fetch SSH Key Manually

```bash
make -C infra fetch-ssh-key \
  ENVIRONMENT=production \
  CLOUD_PROVIDER=aws
```

### Extract DB Credentials

```bash
make -C infra extract-db-credentials \
  ENVIRONMENT=production \
  CLOUD_PROVIDER=aws
```

## 🔧 Direct Python Usage

### SSH Key

```bash
cd infra
source .venv/bin/activate
python -m scripts.resource_connections.utils.secrets.ssh \
  --terraform-dir terraform/aws/environment/production
```

### DB Credentials

```bash
cd infra
source .venv/bin/activate
python -m scripts.resource_connections.utils.secrets.db \
  --terraform-dir terraform/aws/environment/production
```

### Connection

```bash
cd infra
source .venv/bin/activate
python -m scripts.resource_connections.create_connection \
  --environment production \
  --terraform-dir terraform/aws/environment/production \
  --type-of-connection ssh
```

## 📊 Architecture Flow

```
1. Terraform Outputs
   ↓
2. Pydantic Models (validation)
   ↓
3. Secret Fetchers (SSH/DB)
   ↓
4. Connection Handler
   ↓
5. Established Connection
```

## 🔐 Security

- **SSH Keys**: Stored in AWS Secrets Manager with random suffix (e.g., `ec2-ssh-private-key-production-a3f9`), cached in `~/.ssh/`
- **DB Credentials**: Fetched on-demand from AWS/Azure
- **No hardcoded secrets**: All fetched at runtime
- **Proper permissions**: SSH keys cached with `chmod 600`
- **Soft-delete safe**: Random suffixes prevent conflicts with deleted secrets

## 📝 Examples

### SSH Connection Flow

```python
# 1. Get Terraform outputs
outputs = extract_terraform_outputs()

# 2. Validate with model
model = ProdConnectionModelAWS(**outputs)

# 3. Fetch SSH key from Secrets Manager
ssh_key_path = get_ssh_key_path(terraform_dir)

# 4. Connect
subprocess.call(["ssh", "-i", ssh_key_path, f"{user}@{host}"])
```

### Port Forwarding

```bash
# Grafana
make -C infra connection-grafana \
  ENVIRONMENT=production \
  CLOUD_PROVIDER=aws \
  LOCAL_PORT=3000 \
  REMOTE_PORT=3000

# Generic port
make -C infra connection-port \
  ENVIRONMENT=production \
  CLOUD_PROVIDER=aws \
  LOCAL_PORT=8080 \
  REMOTE_PORT=80
```

## ✅ Features

- ✅ Automatic secret fetching
- ✅ Local caching (SSH keys)
- ✅ Multi-cloud support (AWS, Azure)
- ✅ Type-safe models (Pydantic)
- ✅ Clear error messages
- ✅ Makefile integration
- ✅ CI/CD ready

## 🎯 Benefits of New Structure

**Before:**
- Flat structure, everything in root
- Hard to find specific functionality
- Models mixed with utilities

**After:**
- Clear separation: models vs secrets vs connections
- Easy to navigate and maintain
- Logical grouping by purpose
- Scalable for adding new features
