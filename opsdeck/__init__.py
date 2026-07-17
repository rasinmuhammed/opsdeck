"""OpsDeck public package exports."""

from opsdeck.core.admin import OpsDeck
from opsdeck.core.registry import AdminRegistry, ModelConfig
from opsdeck.core.security import URLSigner, CSPMiddleware
from opsdeck.core.views import (
    AdminAction,
    DashboardCard,
    DetailPanel,
    ModelAdmin,
)

__version__ = "2.0.1"

__all__ = [
    "OpsDeck",
    "AdminRegistry",
    "ModelConfig",
    "ModelAdmin",
    "AdminAction",
    "DetailPanel",
    "DashboardCard",
    "URLSigner",
    "CSPMiddleware",
]


def __getattr__(name):
    if name == "MatrixAdmin":
        import warnings

        warnings.warn(
            "MatrixAdmin has been renamed to OpsDeck. "
            "Import it as `from opsdeck import OpsDeck`. "
            "The MatrixAdmin alias will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        return OpsDeck
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
