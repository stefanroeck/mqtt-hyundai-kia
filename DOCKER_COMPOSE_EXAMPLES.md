# Docker Compose Examples

This directory contains Docker Compose examples for running the newly built Hyundai MQTT integration service.

## Quick Start Options

### 1. Quick Test (docker-compose.quickstart.yml)
Perfect for quick testing with your existing MQTT broker.

```bash
# 1. Edit the environment variables in the file
nano docker-compose.quickstart.yml

# 2. Start the service
docker-compose -f docker-compose.quickstart.yml up -d

# 3. View logs
docker-compose -f docker-compose.quickstart.yml logs -f

# 4. Stop the service
docker-compose -f docker-compose.quickstart.yml down
```

### 2. Complete Setup with MQTT Broker (docker-compose.with-broker.yml)
Includes both the Hyundai service and a Mosquitto MQTT broker - perfect for testing without external dependencies.

```bash
# 1. Edit your Hyundai credentials in the file
nano docker-compose.with-broker.yml

# 2. Start both services
docker-compose -f docker-compose.with-broker.yml up -d

# 3. Check service status
docker-compose -f docker-compose.with-broker.yml ps

# 4. View logs
docker-compose -f docker-compose.with-broker.yml logs -f hyundai-mqtt

# 5. Stop both services
docker-compose -f docker-compose.with-broker.yml down
```

### 3. Production Setup (docker-compose.example.yml)
Full-featured configuration with resource limits, persistent volumes, and network isolation.

```bash
# 1. Copy and customize the example
cp docker-compose.example.yml docker-compose.yml

# 2. Edit the configuration with your credentials and settings
nano docker-compose.yml

# 3. Start the production service
docker-compose up -d

# 4. Monitor health status
docker ps
docker inspect --format='{{.Name}}: {{.State.Health.Status}}' hyundai-mqtt
```

## Environment Variables

### Required Variables
- `HYUNDAI_USERNAME`: Your Hyundai/Kia/Genesis account email
- `HYUNDAI_PASSWORD`: Your account password  
- `HYUNDAI_PIN`: Your vehicle PIN (for control commands)
- `MQTT_BROKER_HOST`: MQTT broker hostname or IP address

### Optional Variables
- `HYUNDAI_REGION`: 1=Europe, 2=Canada, 3=USA (default: 1)
- `HYUNDAI_BRAND`: 1=Hyundai, 2=Kia, 3=Genesis (default: 1)
- `MQTT_BROKER_PORT`: MQTT broker port (default: 1883)
- `MQTT_USERNAME`: MQTT authentication username (optional)
- `MQTT_PASSWORD`: MQTT authentication password (optional)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `INITIAL_REFRESH`: Load cached data on startup (default: true)
- `REFRESH_INTERVAL`: Refresh interval in seconds (default: 60)
- `MQTT_BASE_TOPIC`: Base topic for MQTT messages (default: hyundai)

## Using Different Image Tags

You can specify different image tags:

```yaml
services:
  hyundai-mqtt:
    image: ghcr.io/pigmej/mqtt-hyundai-kia:main-32c9136  # Specific commit
    # or
    image: ghcr.io/pigmej/mqtt-hyundai-kia:latest        # Latest version
```

## Monitoring and Troubleshooting

### Check Container Health
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' hyundai-mqtt

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' hyundai-mqtt
```

### View Logs
```bash
# Recent logs
docker logs --tail 100 hyundai-mqtt

# Follow logs in real-time
docker logs -f hyundai-mqtt

# Logs from Docker Compose
docker-compose logs -f hyundai-mqtt
```

### Resource Monitoring
```bash
# Check resource usage
docker stats hyundai-mqtt

# Detailed container information
docker inspect hyundai-mqtt
```

## Production Tips

1. **Use Environment Files**: Store credentials in `.env` file instead of hardcoding
2. **Set Resource Limits**: Use the production example as a template for memory/CPU limits
3. **Enable Health Checks**: Monitor container health for automatic restarts
4. **Use Persistent Volumes**: Store logs and data outside the container
5. **Network Isolation**: Use custom networks for better security

## Example .env File

Create a `.env` file in the same directory:

```bash
# Hyundai Credentials
HYUNDAI_USERNAME=your_email@example.com
HYUNDAI_PASSWORD=your_password
HYUNDAI_PIN=1234
HYUNDAI_REGION=1
HYUNDAI_BRAND=1

# MQTT Configuration
MQTT_BROKER_HOST=your_mqtt_broker
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Application Settings
LOG_LEVEL=INFO
INITIAL_REFRESH=true
REFRESH_INTERVAL=60
MQTT_BASE_TOPIC=hyundai
```

Then reference it in your Docker Compose:

```yaml
services:
  hyundai-mqtt:
    image: ghcr.io/pigmej/mqtt-hyundai-kia:latest
    env_file:
      - .env
```

## Security Considerations

1. **Never commit credentials** to version control
2. **Use read-only volumes** where possible
3. **Run as non-root user** (already configured in the image)
4. **Use network isolation** in production environments
5. **Regularly update** the Docker image for security patches