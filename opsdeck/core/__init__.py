"""Core module for OpsDeck."""

from opsdeck.core.admin import OpsDeck
from opsdeck.core.registry import AdminRegistry, ModelConfig
from opsdeck.core.security import URLSigner, CSPMiddleware
from opsdeck.core.integrator import SchemaWalker, FieldDefinition
from opsdeck.core.views import (
    AdminAction,
    DashboardCard,
    DetailPanel,
    ModelAdmin,
)

__all__ = [
    "OpsDeck",
    "AdminRegistry",
    "ModelConfig",
    "URLSigner",
    "CSPMiddleware",
    "SchemaWalker",
    "FieldDefinition",
    "ModelAdmin",
    "AdminAction",
    "DetailPanel",
    "DashboardCard",
]
