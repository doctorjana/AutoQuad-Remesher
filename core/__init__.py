"""
AutoQuad Remesher - Core Geometry and Topology Package
"""

from .adaptive_density import AdaptiveDensityField
from .curvature_field import CurvatureFieldSolver
from .patch_extractor import QuadPatchExtractor
from .relaxation import SurfaceRelaxationEngine
from .retopology_engine import run_retopology
from .mesh_preprocessing import make_manifold

__all__ = [
    "AdaptiveDensityField",
    "CurvatureFieldSolver",
    "QuadPatchExtractor",
    "SurfaceRelaxationEngine",
    "run_retopology",
    "make_manifold",
]
