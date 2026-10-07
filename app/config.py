import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Second Brain AI (人を天才にするAIプロダクト)"
    VERSION: str = "1.0.0-demo"
    
    # Ollama Local Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434" if os.name == "nt" else "http://host.docker.internal:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "hermes3")
    
    # Obsidian Vault Local Directory
    VAULT_PATH: Path = Path(os.getenv("VAULT_PATH", "/app/vault"))
    
    # LINE Bot Settings (Mock/Production)
    LINE_CHANNEL_SECRET: str = os.getenv("LINE_CHANNEL_SECRET", "mock_secret")
    LINE_CHANNEL_ACCESS_TOKEN: str = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "mock_token")

settings = Settings()
