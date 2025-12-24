"""
Detection modules for products and obstacles
"""

from .product_detector import ProductDetector
from .obstacle_detector import ObstacleDetector
from .quality_inspector import QualityInspector

__all__ = ["ProductDetector", "ObstacleDetector", "QualityInspector"]
