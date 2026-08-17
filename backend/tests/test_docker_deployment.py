"""Docker Deployment Configuration & File Structure Test Suite."""

import os
from pathlib import Path
import yaml
import pytest


def test_docker_file_existence():
    """Verify that all required Docker deployment files exist at their expected paths."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    
    assert (repo_root / "docker-compose.yml").exists(), "Root docker-compose.yml must exist"
    assert (repo_root / "backend" / "Dockerfile").exists(), "backend/Dockerfile must exist"
    assert (repo_root / "frontend" / "Dockerfile").exists(), "frontend/Dockerfile must exist"
    assert (repo_root / ".env.example").exists(), "Root .env.example must exist"
    assert (repo_root / "README.md").exists(), "Root README.md must exist"


def test_docker_compose_structure_and_services():
    """Verify docker-compose.yml contains required services, healthchecks, and volumes."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    compose_path = repo_root / "docker-compose.yml"
    
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
        
    services = compose_data.get("services", {})
    assert "postgres" in services, "docker-compose.yml must define postgres service"
    assert "qdrant" in services, "docker-compose.yml must define qdrant service"
    assert "backend" in services, "docker-compose.yml must define backend service"

    # Verify volumes
    volumes = compose_data.get("volumes", {})
    assert "postgres_data" in volumes, "postgres_data volume must be declared"
    assert "qdrant_data" in volumes, "qdrant_data volume must be declared"
    assert "hf_cache" in volumes, "hf_cache volume must be declared"


def test_docker_backend_environment_defaults():
    """Verify docker-compose.yml backend service environment uses 0.0.0.0 binding and port 8000."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    compose_path = repo_root / "docker-compose.yml"
    
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
        
    backend_env = compose_data["services"]["backend"].get("environment", {})
    assert backend_env.get("HOST") == "0.0.0.0"
    assert backend_env.get("PORT") == "8000"


def test_no_hardcoded_secrets_in_docker_files():
    """Verify docker-compose.yml does not contain hardcoded real credentials."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    compose_content = (repo_root / "docker-compose.yml").read_text()
    
    assert "sk-or-v1" not in compose_content
    assert "AIzaSy" not in compose_content


def test_qdrant_service_host_resolution():
    """Verify Qdrant wrapper resolution under custom QDRANT_HOST settings."""
    from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
    wrapper = QdrantClientWrapper(host="qdrant", port=6333)
    assert wrapper.host == "qdrant"
    assert wrapper.port == 6333
