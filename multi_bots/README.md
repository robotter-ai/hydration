# Multi-Bot Setup Guide

This guide explains how to set up and run multiple Hummingbot instances with a shared Gateway using Docker Compose.

## Prerequisites

1. Complete the setup process described in the [parent directory README.md](../README.md)
2. Ensure you have the following files in your `volumes` folder:
   - Certificates in `volumes/common/certs/`
   - Client configuration files in `volumes/client/conf/`
   - Gateway configuration files in `volumes/gateway/conf/`

## Setup Instructions

### 1. Copy Configuration Files

After completing the main setup, create the required directories and copy the relevant configuration files:

```bash
# Create required directories
mkdir -p multi_bots/common/certs
mkdir -p multi_bots/gateway/conf
mkdir -p multi_bots/bot1/conf
mkdir -p multi_bots/bot2/conf

# Copy certificates to shared common folder
cp -r volumes/common/certs/* multi_bots/common/certs/

# Copy gateway configuration
cp -r volumes/gateway/conf/* multi_bots/gateway/conf/

# Copy client configuration to bot instances (including hidden files)
cp -r volumes/client/conf/* multi_bots/bot1/conf/
cp volumes/client/conf/.password_verification multi_bots/bot1/conf/
cp -r volumes/client/conf/* multi_bots/bot2/conf/
cp volumes/client/conf/.password_verification multi_bots/bot2/conf/
```

### 2. Configure Environment Variables

1. Copy the default environment file:
   ```bash
   cp .default.env .env
   ```

2. Edit the `.env` file and set your passwords:
   ```bash
   CONFIG_PASSWORD=your_hummingbot_password
   GATEWAY_PASSPHRASE=your_gateway_passphrase
   ```

   **Important**: Use the same passwords you configured during the main setup process.

### 3. Run the Multi-Bot Setup

Navigate to the multi_bots directory and start the containers:

```bash
cd multi_bots
docker-compose up -d
```

## Default Behavior

After running `docker-compose up -d`, the following will be available:

- **bot1**: Hummingbot instance logged in but in standby mode
- **bot2**: Hummingbot instance logged in but in standby mode  
- **gateway**: Shared Gateway instance serving both bots

Both bots will be logged in automatically using the `CONFIG_PASSWORD` but will remain in standby mode until you specify scripts to run.

## Running Scripts Automatically

To have bots automatically run scripts on startup, you have two options:

### Simple Scripts
For basic scripts:

1. Edit `docker-compose.yml`
2. Uncomment the `CONFIG_FILE_NAME` line for the desired bot(s)
3. Set the script filename:

```yaml
environment:
  - CONFIG_PASSWORD=${CONFIG_PASSWORD}
  - CONFIG_FILE_NAME=amm_data_feed_example.py  # Uncomment and set script name
```

Example scripts are available in the `scripts/` folder, and configuration files should be placed in the respective bot's `conf/` directory.

## Managing the Setup

### View running containers
```bash
docker-compose ps
```

### View logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs bot1
docker-compose logs bot2  
docker-compose logs gateway
```

### Stop the setup
```bash
docker-compose down
```

### Restart a specific bot
```bash
docker-compose restart bot1
```

### Attach to a bot console
```bash
docker attach bot1
# or
docker attach bot2
```

## Directory Structure

```
multi_bots/
├── bot1/conf/          # Bot 1 configuration files
├── bot2/conf/          # Bot 2 configuration files
├── common/certs/       # Shared certificates
├── gateway/conf/       # Gateway configuration
├── scripts/            # Trading scripts
├── controllers/        # Strategy controllers
├── docker-compose.yml  # Docker Compose configuration
├── .env               # Environment variables
└── README.md          # This file
```

## Notes

- Each bot instance maintains its own configuration, logs, and data
- The Gateway is shared between all bot instances
- Both bots use the same certificates for Gateway communication
- Make sure to use the same passwords configured during the initial setup