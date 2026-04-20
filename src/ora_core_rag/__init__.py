"""ORA_CORE_RAG public Python package."""

from .arch_persona import ArchPersonaError, build_arch_persona_activation, load_activation_payload
from .governor import GovernorConfig, GovernorError, RAGGovernor
from .index import ORACoreIndex
from .neroflux import NerofluxFanoutRegulator
from .registry import RAGRegistry, RegistryError
from .route_gate import ClientRouteGate, RouteGateError

__all__ = [
    "ArchPersonaError",
    "build_arch_persona_activation",
    "load_activation_payload",
    "GovernorConfig",
    "GovernorError",
    "RAGGovernor",
    "ORACoreIndex",
    "NerofluxFanoutRegulator",
    "RAGRegistry",
    "RegistryError",
    "ClientRouteGate",
    "RouteGateError",
]
__version__ = "0.4.0"
