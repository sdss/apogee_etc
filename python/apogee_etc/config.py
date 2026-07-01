from importlib.resources import files
import yaml


def load_yaml(filename):
    """Load a YAML file from apogee_etc/data."""
    path = files("apogee_etc") / "data" / filename
    with open(path, "r") as f:
        return yaml.safe_load(f)


# Convenience dictionaries loaded at import time
INSTRUMENTS = load_yaml("instruments.yaml")
SKY_MODELS = load_yaml("sky_models.yaml")
VERSIONS = load_yaml("versions.yaml")
