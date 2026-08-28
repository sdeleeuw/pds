from mcp.types import ToolAnnotations


READ_ONLY_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    idempotent_hint=True,
    open_world_hint=False,
)

CREATE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)

UPDATE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=True,
    open_world_hint=False,
)

DELETE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=False,
    open_world_hint=False,
)

__all__ = [
    "CREATE_ANNOTATIONS",
    "DELETE_ANNOTATIONS",
    "READ_ONLY_ANNOTATIONS",
    "UPDATE_ANNOTATIONS",
]
