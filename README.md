# Azure Key Vault Client

A Python client for connecting to Azure Key Vault with support for local development, corporate proxies, and internal Key Vault instances.

## Features

- 🔐 **Secure Authentication**: Supports Azure CLI, managed identity, and service principal authentication
- 🛡️ **SSL Configuration**: Configurable SSL verification for development and testing
- 📝 **Environment Variables**: Easy configuration via .env file
- 🖥️ **Command Line Interface**: Simple CLI for testing and basic operations

## Prerequisites

- Python 3.7 or higher
- Azure subscription with Key Vault access
- One of the following authentication methods:
  - Azure CLI (`az login`)
  - Service principal credentials
  - Managed identity (when running in Azure)
- **For internal Key Vault access**: Ivanti VPN connection and proper hosts file configuration

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd az-keyvault-connect
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
# Required: Azure Key Vault URL
AZURE_KEYVAULT_URL=https://your-vault.vault.azure.net/

```

## Internal Key Vault Configuration

For accessing internal Azure Key Vault instances, additional configuration is required:

### 1. Configure Hosts File

**For WSL/Linux:**
```bash
# Edit the hosts file with sudo privileges
sudo nano /etc/hosts

# Add the following line, IP for example purpose, use the correct one:
255.255.255.255    https://your-vault.vault.azure.net/
```

**For Windows:**
```cmd
# Edit the hosts file as Administrator, request it from IT department
notepad C:\Windows\System32\drivers\etc\hosts

# Add the following line, IP for example purpose, use the correct one:
255.255.255.255    https://your-vault.vault.azure.net/
```

### 2. VPN Connection

1. **Connect to Ivanti VPN** using your corporate credentials
2. **Request Azure Key Vault access** by submitting a ticket to IT department
3. **Wait for approval** and access provisioning

## Usage

### Command Line Interface

The client provides a simple CLI for basic operations:

```bash
# Test connection to Key Vault
python keyvault_client.py test

# List all secrets
python keyvault_client.py list

# Get a secret
python keyvault_client.py get my-secret-name

# Get multiple secrets
python keyvault_client.py get-multiple secret1 secret2 secret3

# Get secrets by prefix (e.g., all secrets starting with "AI-")
python keyvault_client.py get-prefix AI

# Get secrets by prefix and save to .env file (e.g., saves to AI.env)
python keyvault_client.py get-prefix-save AI

# Set a secret (No tested)
python keyvault_client.py set my-secret-name "my-secret-value"
```

### Python API

```python
from keyvault_client import AzureKeyVaultClient

# Initialize client
client = AzureKeyVaultClient()

# Test connection
if client.test_connection():
    print("Connected successfully!")

# Get a secret
secret_value = client.get_secret("my-secret-name")
print(f"Secret value: {secret_value}")

# Set a secret
success = client.set_secret("new-secret", "new-value")

# List all secrets
secrets = client.list_secrets()
print(f"Available secrets: {secrets}")

# Get multiple secrets
results = client.get_multiple_secrets(["secret1", "secret2", "secret3"])
for name, value in results.items():
    print(f"{name}: {value}")

# Get secrets by prefix (e.g., all secrets starting with "AI-")
secrets_by_prefix = client.get_secrets_by_prefix("AI")
for name, value in secrets_by_prefix.items():
    print(f"{name}: {value}")

# Save secrets to .env file
client.save_secrets_to_env_file(secrets_by_prefix, "AI.env")
```

## Prefix-Based Secret Management

The client provides powerful prefix-based secret management capabilities for organizing and retrieving related secrets:

### How It Works

Secrets are filtered by their prefix (letters before the first "-"). For example:
- `AI-api-key` → prefix: `AI`
- `AI-model-name` → prefix: `AI` 
- `DB-connection-string` → prefix: `DB`
- `DB-username` → prefix: `DB`

### Usage Examples

```bash
# Get all secrets with "AI-" prefix and display them
python keyvault_client.py get-prefix AI

# Get all secrets with "AI-" prefix and save them to AI.env file
python keyvault_client.py get-prefix-save AI
```

### Generated .env File Format

When using `get-prefix-save`, the secrets are saved to a `.env` file with the following format:

```env
# AI.env file example
AI_API_KEY=your_api_key_here
AI_MODEL_NAME=gpt-4
AI_ENDPOINT=https://api.openai.com/v1
AI_ORGANIZATION=your_org_id
```

The secret names are automatically converted to uppercase and hyphens are replaced with underscores for proper environment variable format.

### Python API for Prefix Operations

```python
# Get all secrets with a specific prefix
secrets = client.get_secrets_by_prefix("AI")
print(f"Found {len(secrets)} AI-related secrets")

# Save prefix-based secrets to a file
client.save_secrets_to_env_file(secrets, "AI.env")
```

## Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_KEYVAULT_URL` | Azure Key Vault URL | Yes | - |


### Constructor Parameters

```python
client = AzureKeyVaultClient(
    vault_url="https://your-vault.vault.azure.net/",
    disable_ssl_verify=False
)
```

## Authentication Methods

### 1. Azure CLI (Recommended for Development)

```bash
# Install Azure CLI and login
az login
```

## Error Handling

The client provides detailed error messages and troubleshooting suggestions:

```python
try:
    client = AzureKeyVaultClient()
    if not client.test_connection():
        print("Connection failed - check the troubleshooting suggestions above")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure you're logged in with `az login`
   - Verify your account has Key Vault permissions

2. **Connection Timeout**
   - Verify the Key Vault URL is correct
   - Check your internet connection
   - **For internal Key Vaults**: Ensure Ivanti VPN is connected
   - **For internal Key Vaults**: Verify hosts file configuration

3. **SSL Certificate Errors**
   - For internal Key Vaults, SSL verification is disabled automatically
   - For testing, set `DISABLE_SSL_VERIFY=true`
   - Check if the Key Vault uses a valid SSL certificate

4. **Permission Denied**
   - Ensure your account has Key Vault access
   - Check Key Vault access policies
   - Verify the Key Vault exists and is accessible
   - **For internal Key Vaults**: Ensure VPN access ticket is approved

5. **Internal Key Vault Access Issues**
   - Verify hosts file entry: `255.255.255.255 your-vault.vault.azure.net`
   - Ensure Ivanti VPN is connected and stable
   - Check if your VPN access ticket has been approved
   - Try setting `DISABLE_SSL_VERIFY=true` in your `.env` file
