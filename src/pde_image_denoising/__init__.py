"""PDE-based image denoising for a reproducible teaching project."""

from .heat import heat_diffusion, heat_trajectory
from .perona_malik import perona_malik_diffusion, perona_malik_trajectory

__all__ = [
    "heat_diffusion",
    "heat_trajectory",
    "perona_malik_diffusion",
    "perona_malik_trajectory",
]

__version__ = "0.0.0"
