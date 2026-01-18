"""
ACE Core: Adaptive Context Engineering Framework
Preventing Context Collapse in LLM Agents via Incremental Updates
"""

from .manual import EvolvingManual, ManualItem
from .metadata import Metadata, MetadataManager
from .generator import Generator
from .reflector import Reflector
from .curator import Curator
from .updates import DeltaUpdate, IncrementalUpdater
from .merge import DeterministicMerger
from .framework import ACEFramework

__version__ = "0.1.0"
__all__ = [
    "EvolvingManual",
    "ManualItem",
    "Metadata",
    "MetadataManager",
    "Generator",
    "Reflector",
    "Curator",
    "DeltaUpdate",
    "IncrementalUpdater",
    "DeterministicMerger",
    "ACEFramework",
]
