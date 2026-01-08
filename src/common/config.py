# src/common/config.py
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()


# --- Pydantic Models for Type-Safe Configs ---


class CameraConfig(BaseModel):
    resolution: List[int]
    fps: int


class LoggingConfig(BaseModel):
    level: str
    file_path: str


class AppConfig(BaseModel):
    camera: CameraConfig
    logging: LoggingConfig


class DbConfig(BaseModel):
    aws_rds: Dict[str, Any]


class DetectorConfig(BaseModel):
    weights: str
    confidence: float
    iou_threshold: Optional[float] = None
    danger_threshold_low: Optional[float] = None
    danger_threshold_high: Optional[float] = None


class ModelConfig(BaseModel):
    obstacle_detector: DetectorConfig
    product_recognizer: DetectorConfig


class PC1Config(BaseModel):
    ip: str
    udp_port_front: int
    udp_port_cart: int


class PC2Config(BaseModel):
    ip: str
    cart_code: str
    event_port: int
    ui_port: int
    udp_front_cam_port: int
    udp_cart_cam_port: int


class PC3Config(BaseModel):
    ip: str
    ui_port: int


class NetworkConfig(BaseModel):
    pc1_ai: PC1Config
    pc2_main: PC2Config
    pc3_ui: PC3Config


# --- Main Config Class ---


class Config(BaseModel):
    """
    A unified, type-safe configuration object that loads all YAML configs.
    """

    app: AppConfig
    db: DbConfig
    model: ModelConfig
    network: NetworkConfig

    @classmethod
    def load_from_dir(cls, path: str = "configs") -> "Config":
        """
        Loads all .yaml files from a directory and merges them into a single Config object.
        Environment variables from .env file are automatically substituted in YAML values.
        """
        config_dir = Path(path)
        if not config_dir.is_dir():
            raise FileNotFoundError(f"Configuration directory not found: {config_dir}")

        all_configs = {}
        for config_file in config_dir.glob("*.yaml"):
            config_name = config_file.stem.replace("_config", "")
            with open(config_file, "r") as f:
                content = f.read()
                # Replace environment variables in format ${VAR_NAME}
                content = os.path.expandvars(content)
                all_configs[config_name] = yaml.safe_load(content)

        return cls.model_validate(all_configs)


# --- Singleton Instance ---
# Create a single config instance to be used throughout the application
try:
    config = Config.load_from_dir()
except Exception as e:
    print(f"FATAL: Could not load configuration. Error: {e}")
    # Provide a dummy config object to avoid import errors on initial startup
    # In a real app, you might exit or have a more robust fallback.
    config = None
