#!/usr/bin/env python3
"""
Azure Key Vault Client for local development
Connects to Azure Key Vault using credentials from .env file
"""

import os
import sys
import ssl
import urllib3
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import AzureError
from azure.core.pipeline.transport import RequestsTransport
import requests
from urllib.parse import urlparse

class AzureKeyVaultClient:
    """Client for interacting with Azure Key Vault"""
    
    def __init__(self, vault_url: Optional[str] = None, disable_ssl_verify: bool = False):
        """
        Initialize the Azure Key Vault client
        
        Args:
            vault_url: The Azure Key Vault URL (e.g., https://your-vault.vault.azure.net/)
            disable_ssl_verify: Whether to disable SSL verification (use only for testing)
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.vault_url = vault_url or os.getenv('AZURE_KEYVAULT_URL')
        self.disable_ssl_verify = disable_ssl_verify or os.getenv('DISABLE_SSL_VERIFY', 'false').lower() == 'true'
        
        if not self.vault_url:
            raise ValueError("AZURE_KEYVAULT_URL not found in environment variables or .env file")
        
        # Ensure the URL ends with a slash
        if not self.vault_url.endswith('/'):
            self.vault_url += '/'
        
        print(f"Connecting to Key Vault: {self.vault_url}")
        if self.disable_ssl_verify:
            print("WARNING: SSL verification is disabled")
        
        # Initialize credentials
        self.credential = self._get_credential()
        
        # Create transport with SSL configuration
        transport = self._create_transport()
        
        # Initialize client with custom transport
        self.client = SecretClient(
            vault_url=self.vault_url, 
            credential=self.credential,
            transport=transport
        )
    
    def _create_transport(self) -> RequestsTransport:
        """Create a custom transport with SSL configuration"""
        session = requests.Session()
        
        # Check if we're connecting to an internal IP or custom domain
        parsed_url = urlparse(self.vault_url)
        is_internal = (
            parsed_url.hostname.startswith('10.') or
            parsed_url.hostname.startswith('192.168.') or
            parsed_url.hostname.startswith('172.') or
            parsed_url.hostname in ['localhost', '127.0.0.1'] or
            not parsed_url.hostname.endswith('.azure.net')
        )
        
        if self.disable_ssl_verify or is_internal:
            # Disable SSL verification for internal Key Vaults or when explicitly requested
            session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            if is_internal:
                print(f"Detected internal Key Vault ({parsed_url.hostname}) - SSL verification disabled")
            else:
                print("WARNING: SSL verification is disabled. This should only be used for testing.")
        else:
            # Configure SSL context for public Azure Key Vault
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            session.verify = True
            print("Configured for public Azure Key Vault (strict SSL verification)")
        
        # Configure session with SSL context
        adapter = requests.adapters.HTTPAdapter()
        session.mount('https://', adapter)
        
        return RequestsTransport(session=session)
    
    def _get_credential(self) -> DefaultAzureCredential:
        """Get Azure credentials using various authentication methods"""
        try:
            # Use DefaultAzureCredential (Azure CLI, managed identity, etc.)
            return DefaultAzureCredential()
        except Exception as e:
            print(f"DefaultAzureCredential failed: {e}")
            raise ValueError(
                "No valid credentials found. Please ensure you have:\n"
                "1. Azure CLI installed and logged in (az login)\n"
                "2. Or running in Azure with managed identity enabled\n"
                "3. AZURE_KEYVAULT_URL set in environment variables"
            )
    
    def test_connection(self) -> bool:
        """
        Test the connection to Azure Key Vault
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            print("Testing connection...")
            # Try to list secrets as a connection test
            secrets = list(self.client.list_properties_of_secrets())
            print(f"✓ Connection to Azure Key Vault successful! Found {len(secrets)} secrets.")
            return True
        except Exception as e:
            print(f"✗ Connection to Azure Key Vault failed: {e}")
            print("\nTroubleshooting suggestions:")
            print("1. For internal Key Vaults, try setting DISABLE_SSL_VERIFY=true")
            print("2. Verify your Azure credentials with 'az login'")
            print("3. Check if the Key Vault URL is correct")
            return False
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get a secret from Azure Key Vault
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            The secret value or None if not found
        """
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except AzureError as e:
            print(f"Error retrieving secret '{secret_name}': {e}")
            return None
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Set a secret in Azure Key Vault
        
        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.set_secret(secret_name, secret_value)
            print(f"Secret '{secret_name}' set successfully")
            return True
        except AzureError as e:
            print(f"Error setting secret '{secret_name}': {e}")
            return False
    
    def list_secrets(self) -> list:
        """
        List all secrets in the Key Vault
        
        Returns:
            List of secret names
        """
        try:
            secrets = []
            for secret_properties in self.client.list_properties_of_secrets():
                secrets.append(secret_properties.name)
            return secrets
        except AzureError as e:
            print(f"Error listing secrets: {e}")
            return []
    
    def get_multiple_secrets(self, secret_names: list) -> Dict[str, Optional[str]]:
        """
        Get multiple secrets from Azure Key Vault
        
        Args:
            secret_names: List of secret names to retrieve
            
        Returns:
            Dictionary mapping secret names to their values
        """
        results = {}
        for secret_name in secret_names:
            results[secret_name] = self.get_secret(secret_name)
        return results

def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python keyvault_client.py test")
        print("  python keyvault_client.py get <secret_name>")
        print("  python keyvault_client.py set <secret_name> <secret_value>")
        print("  python keyvault_client.py list")
        print("  python keyvault_client.py get-multiple <secret1> <secret2> ...")
        print("\nEnvironment variables:")
        print("  DISABLE_SSL_VERIFY=true  # Disable SSL verification (testing only)")
        sys.exit(1)
    
    try:
        # Check if SSL verification should be disabled
        disable_ssl = os.getenv('DISABLE_SSL_VERIFY', 'false').lower() == 'true'
        
        client = AzureKeyVaultClient(disable_ssl_verify=disable_ssl)
        command = sys.argv[1].lower()
        
        if command == "test":
            client.test_connection()
        
        elif command == "get" and len(sys.argv) >= 3:
            secret_name = sys.argv[2]
            value = client.get_secret(secret_name)
            if value:
                print(f"{secret_name}: {value}")
            else:
                print(f"Secret '{secret_name}' not found or error occurred")
        
        elif command == "set" and len(sys.argv) >= 4:
            secret_name = sys.argv[2]
            secret_value = sys.argv[3]
            success = client.set_secret(secret_name, secret_value)
            if not success:
                sys.exit(1)
        
        elif command == "list":
            secrets = client.list_secrets()
            if secrets:
                print("Available secrets:")
                for secret in secrets:
                    print(f"  - {secret}")
            else:
                print("No secrets found or error occurred")
        
        elif command == "get-multiple" and len(sys.argv) >= 3:
            secret_names = sys.argv[2:]
            results = client.get_multiple_secrets(secret_names)
            for name, value in results.items():
                if value:
                    print(f"{name}: {value}")
                else:
                    print(f"{name}: [NOT FOUND]")
        
        else:
            print("Invalid command or missing arguments")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 