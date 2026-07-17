"""Deprecated shim: fastapi-matrix-admin is now published as ``opsdeck``.

This package re-exports the opsdeck API under the old import path so
existing code keeps working. Migrate imports to ``opsdeck`` — this shim
will not receive updates beyond keeping the dependency pin current.
"""

import warnings

from opsdeck import *  # noqa: F401,F403
from opsdeck import OpsDeck, __all__ as _opsdeck_all

# Old name for the main class.
MatrixAdmin = OpsDeck

__all__ = list(_opsdeck_all) + ["MatrixAdmin"]

warnings.warn(
    "fastapi-matrix-admin has been renamed to opsdeck. "
    "Install with `pip install opsdeck` and import with "
    "`from opsdeck import OpsDeck`.",
    DeprecationWarning,
    stacklevel=2,
)
