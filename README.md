# 🗄️ AWS Database Migration Analyzer - EC2 Deployment Guide

## Overview

This guide covers deploying the AWS Database Migration Analyzer AI application on an AWS EC2 instance. The deployment includes:

- **Streamlit** web application with production settings
- **Nginx** reverse proxy for SSL/load balancing
- **Systemd** service for process management
- **IAM Role** integration for secure AWS access
- **Environment-based** configuration (replacing Streamlit Cloud secrets)

---

## 📋 Prerequisites

### AWS Requirements

| Requirement | Recommended |
|-------------|-------------|
| EC2 Instance | t3.medium or larger |
| Operating System | Amazon Linux 2023 or Ubuntu 22.04 |
| Storage | 20 GB gp3 EBS |
| Security Group | Ports 22 (SSH), 80 (HTTP), 443 (HTTPS) |
| IAM Role | Basic EC2 role (for AWS service access) |

### API Keys Required

| Service | Purpose | Required |
|---------|---------|----------|
| Anthropic API | AI-powered analysis | ✅ Yes |
| Firebase | User authentication | ⚪ Optional |

---

## 🚀 Quick Start Deployment

### Step 1: Launch EC2 Instance

```bash
# Using AWS CLI
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=dbmigration-analyzer}]'
```

### Step 2: Connect to Instance

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
# Or for Ubuntu:
ssh -i your-key.pem ubuntu@your-instance-ip
```

### Step 3: Upload and Run Setup Script

```bash
# Upload the deployment package
scp -i your-key.pem dbmigration-ec2-deployment.zip ec2-user@your-instance-ip:~

# On EC2 instance:
unzip dbmigration-ec2-deployment.zip -d dbmigration
cd dbmigration

# Make scripts executable
chmod +x scripts/*.sh

# Run setup (as root)
sudo ./scripts/setup-ec2.sh
```

### Step 4: Configure Application

```bash
# Edit environment configuration
sudo nano /etc/dbmigration/.env

# IMPORTANT: Add these values:
# - ANTHROPIC_API_KEY (required for AI features)
# - ADMIN_EMAIL and ADMIN_PASSWORD
# - (Optional) Firebase configuration
```

### Step 5: Deploy Application Files

```bash
# Run deployment script
sudo ./scripts/deploy-app.sh
```

### Step 6: Verify Deployment

```bash
# Check service status
sudo systemctl status dbmigration

# View logs
sudo journalctl -u dbmigration -f

# Test application
curl http://localhost:8501/_stcore/health
```

---

## 📁 Directory Structure

After deployment, your EC2 instance will have this structure:

```
/opt/dbmigration/
├── venv/                    # Python virtual environment
├── logs/                    # Application logs
├── data/                    # Application data
├── backups/                 # Deployment backups
├── scripts/                 # Maintenance scripts
│   ├── start.sh
│   ├── stop.sh
│   ├── restart.sh
│   ├── status.sh
│   └── update.sh
├── streamlit_app.py         # Main application
├── streamlit_app_ec2.py     # EC2 launcher
├── ec2_config.py            # Configuration loader
├── requirements.txt         # Python dependencies
└── firebase-config.json     # Firebase config (optional)

/etc/dbmigration/
└── .env                     # Environment configuration

/var/log/dbmigration/
└── app.log                  # Application logs
```

---

## ⚙️ Configuration Reference

### Environment Variables (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key for AI analysis | ✅ Yes |
| `AWS_DEFAULT_REGION` | AWS region | No (default: us-east-1) |
| `ADMIN_EMAIL` | Admin login email | ✅ Yes |
| `ADMIN_PASSWORD` | Admin login password | ✅ Yes |
| `ADMIN_KEY` | Admin secret key | No |
| `FIREBASE_PROJECT_ID` | Firebase project ID | No |
| `FIREBASE_WEB_API_KEY` | Firebase Web API key | No |
| `APP_MODE` | Application mode | No (default: production) |

### Firebase Configuration

You have two options for Firebase:

**Option 1: Environment Variables**
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_WEB_API_KEY=your-web-api-key
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@project.iam.gserviceaccount.com
# ... other Firebase variables
```

**Option 2: JSON File**
```bash
# Place firebase-config.json in /opt/dbmigration/
# The app will automatically detect and load it
```

---

## 🔒 Security Best Practices

### 1. Use Strong Passwords

```bash
# Generate strong admin password
openssl rand -base64 24

# Update in /etc/dbmigration/.env
ADMIN_PASSWORD=your-generated-password
```

### 2. Restrict Security Group

```bash
# Allow only your office IP for HTTP
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxx \
    --protocol tcp \
    --port 80 \
    --cidr YOUR_OFFICE_IP/32
```

### 3. Enable HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 4. Secure API Keys

```bash
# Ensure .env file is protected
sudo chmod 600 /etc/dbmigration/.env
sudo chown dbmigration:dbmigration /etc/dbmigration/.env
```

---

## 📊 Monitoring & Logging

### View Application Logs

```bash
# Real-time logs
sudo journalctl -u dbmigration -f

# Last 100 lines
sudo journalctl -u dbmigration -n 100

# Logs from last hour
sudo journalctl -u dbmigration --since "1 hour ago"
```

### Check Service Status

```bash
# Service status
sudo systemctl status dbmigration

# Nginx status
sudo systemctl status nginx

# Resource usage
htop
```

---

## 🔄 Maintenance Operations

### Restart Application

```bash
sudo systemctl restart dbmigration
```

### Update Application

```bash
cd /opt/dbmigration
sudo ./scripts/update.sh
```

### View Status

```bash
sudo ./scripts/status.sh
```

### Backup Configuration

```bash
sudo cp /etc/dbmigration/.env /etc/dbmigration/.env.backup
```

---

## 🐛 Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u dbmigration -n 50

# Test manually
source /opt/dbmigration/venv/bin/activate
cd /opt/dbmigration
streamlit run streamlit_app_ec2.py --server.port 8502
```

### 502 Bad Gateway

```bash
# Check if Streamlit is running
curl http://localhost:8501/_stcore/health

# Restart services
sudo systemctl restart dbmigration
sudo systemctl restart nginx
```

### AI Features Not Working

```bash
# Verify API key is set
grep ANTHROPIC_API_KEY /etc/dbmigration/.env

# Test API key
source /opt/dbmigration/venv/bin/activate
python3 -c "
import anthropic
client = anthropic.Anthropic()
print('API key is valid')
"
```

### Firebase Authentication Issues

```bash
# Verify Firebase config
cat /opt/dbmigration/firebase-config.json

# Or check environment
grep FIREBASE /etc/dbmigration/.env
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Security Group                            │
│                   (Ports 80, 443)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      EC2 Instance                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                     Nginx                            │    │
│  │              (Reverse Proxy :80/443)                 │    │
│  └────────────────────────┬────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Streamlit                          │    │
│  │         (DB Migration Analyzer :8501)                │    │
│  └────────────────────────┬────────────────────────────┘    │
│                           │                                  │
└───────────────────────────┼─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
       ┌─────────┐    ┌─────────┐    ┌─────────┐
       │Anthropic│    │Firebase │    │   AWS   │
       │  Claude │    │  Auth   │    │Services │
       └─────────┘    └─────────┘    └─────────┘
```

---

## 📞 Support

For issues or questions:

1. Check logs: `sudo journalctl -u dbmigration -f`
2. Review this guide's troubleshooting section
3. Verify API keys are correctly configured
4. Check network connectivity to external services

---

**Version:** 3.0 Enterprise Edition - EC2 Deployment  
**Last Updated:** December 2024
