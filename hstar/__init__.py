"""
H-STAR: LLM-driven Hybrid SQL-Text Adaptive Reasoning on Tables

This package implements the full H-STAR pipeline for table reasoning tasks.
"""

__version__ = "0.1.0"

from hstar.pipeline import HStar
from hstar.config import Config

__all__ = ["HStar", "Config"]
