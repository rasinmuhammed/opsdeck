"""
Pydantic CoreSchema Walker (The "Brain") for FastAPI Shadcn Admin.

This module inspects Pydantic v2 CoreSchema to generate an intermediate
FieldDefinition representation that Jinja templates can understand.

Features:
- Recursive schema parsing with depth circuit breaker
- Discriminated union detection for polymorphic forms
- Support for all Pydantic v2 field types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Type, get_origin, get_args, Union, Literal

from pydantic import BaseModel
from pydantic.fields import FieldInfo


class FieldType(str, Enum):
    """Supported field types for form rendering."""

    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    FLOAT = "float"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    EMAIL = "email"
    URL = "url"
    PASSWORD = "password"
    FILE = "file"
    IMAGE = "image"
    JSON = "json"
    RELATIONSHIP = "relationship"  # FK (many-to-one)
    MANY_TO_MANY = "many_to_many"  # M2M via secondary table
    UNION = "union"  # For discriminated unions
    NESTED = "nested"  # For nested objects
    LIST = "list"  # For list fields
    COMPLEX = "complex"  # Circuit breaker placeholder


@dataclass
class FieldDefinition:
    """
    Intermediate representation of a form field for template rendering.

    This is the output of the SchemaWalker and the input for Jinja macros.
    It contains all the information needed to render a form input.
    """

    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    title: str | None = None
    description: str | None = None
    placeholder: str | None = None

    # For select/enum fields
    options: list[dict[str, str]] = field(default_factory=list)

    # For discriminated unions
    discriminator: str | None = None
    discriminator_values: list[str] = field(default_factory=list)

    # For relationship fields (Foreign Keys)
    target_model: str | None = None

    # For nested/list fields
    children: list["FieldDefinition"] = field(default_factory=list)
    item_type: "FieldDefinition | None" = None

    # For validation
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None

    # Metadata
    readonly: bool = False
    hidden: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
            "title": self.title or self.name.replace("_", " ").title(),
        }

        if self.default is not None:
            result["default"] = self.default
        if self.description:
            result["description"] = self.description
        if self.placeholder:
            result["placeholder"] = self.placeholder
        if self.options:
            result["options"] = self.options
        if self.discriminator:
            result["discriminator"] = self.discriminator
            result["discriminator_values"] = self.discriminator_values
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        if self.item_type:
            result["item_type"] = self.item_type.to_dict()

        return result


class SchemaWalkerError(Exception):
    """Raised when schema walking fails."""

    pass


class SchemaWalker:
    """
    Recursive Pydantic v2 CoreSchema inspector.

    Walks through a Pydantic model's schema and generates FieldDefinition
    objects that can be used to render forms.

    Features:
    - Handles all standard Python types (str, int, float, bool, etc.)
    - Detects discriminated unions for polymorphic form rendering
    - Implements a circuit breaker to prevent infinite recursion
    - Supports nested objects and lists

    Usage:
        walker = SchemaWalker(max_depth=5)
        fields = walker.walk(MyModel)
        # fields is a list of FieldDefinition objects
    """

    # Maximum recursion depth before circuit breaker triggers
    DEFAULT_MAX_DEPTH = 5

    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH):
        """
        Initialize the schema walker.

        Args:
            max_depth: Maximum recursion depth (default: 5)
        """
        self.max_depth = max_depth
        self._visited: set[str] = set()

    def walk(
        self,
        model: Type[BaseModel],
        exclude: list[str] | None = None,
        include: list[str] | None = None,
    ) -> list[FieldDefinition]:
        """
        Walk a Pydantic model and generate field definitions.

        Args:
            model: The Pydantic model class to inspect
            exclude: Field names to exclude
            include: Field names to include (if set, only these are included)

        Returns:
            List of FieldDefinition objects
        """
        self._visited.clear()
        exclude = set(exclude or [])
        include = set(include) if include else None

        fields = []
        model_fields = model.model_fields

        for name, field_info in model_fields.items():
            # Apply include/exclude filters
            if name in exclude:
                continue
            if include is not None and name not in include:
                continue

            field_def = self._process_field(name, field_info, model, depth=0)
            if field_def:
                fields.append(field_def)

        return fields

    def walk_subtype(
        self,
        model: Type[BaseModel],
        parent_discriminator: str | None = None,
    ) -> list[FieldDefinition]:
        """
        Walk a subtype model for polymorphic form fragment rendering.

        This excludes the discriminator field since it's already set.

        Args:
            model: The subtype model class
            parent_discriminator: The discriminator field name to exclude

        Returns:
            List of FieldDefinition objects (excluding discriminator)
        """
        exclude = [parent_discriminator] if parent_discriminator else []
        return self.walk(model, exclude=exclude)

    def _process_field(
        self,
        name: str,
        field_info: FieldInfo,
        model: Type[BaseModel],
        depth: int,
    ) -> FieldDefinition | None:
        """
        Process a single field and return its definition.

        Args:
            name: Field name
            field_info: Pydantic FieldInfo
            model: Parent model class
            depth: Current recursion depth

        Returns:
            FieldDefinition or None if field should be skipped
        """
        # Circuit breaker check
        if depth >= self.max_depth:
            return FieldDefinition(
                name=name,
                field_type=FieldType.COMPLEX,
                required=field_info.is_required(),
                description="Complex object (click to edit)",
            )

        annotation = field_info.annotation

        # Get default value
        default = None
        if field_info.default is not None and field_info.default is not ...:
            default = field_info.default
        elif field_info.default_factory is not None:
            try:
                default = field_info.default_factory()
            except Exception:
                pass

        # Process the type annotation
        field_def = self._annotation_to_field(
            name=name,
            annotation=annotation,
            field_info=field_info,
            depth=depth,
        )

        if field_def:
            field_def.required = field_info.is_required()
            field_def.default = default
            field_def.title = field_info.title or name.replace("_", " ").title()
            field_def.description = field_info.description

            # Extract validation constraints
            if hasattr(field_info, "metadata") and field_info.metadata:
                self._extract_constraints(field_def, field_info.metadata)

        return field_def

    def _annotation_to_field(
        self,
        name: str,
        annotation: Any,
        field_info: FieldInfo,
        depth: int,
    ) -> FieldDefinition:
        """
        Convert a type annotation to a FieldDefinition.

        Args:
            name: Field name
            annotation: The type annotation
            field_info: Pydantic FieldInfo
            depth: Current recursion depth

        Returns:
            FieldDefinition for the type
        """
        origin = get_origin(annotation)
        args = get_args(annotation)

        # Handle None/Optional
        if annotation is type(None):
            return FieldDefinition(name=name, field_type=FieldType.TEXT, required=False)

        # Handle Union types (including Optional)
        if origin is Union:
            return self._handle_union(name, args, field_info, depth)

        # Handle Literal types (for discriminators)
        if origin is Literal:
            return self._handle_literal(name, args)

        # Handle List types
        if origin is list:
            return self._handle_list(name, args, depth)

        # Handle Dict types
        if origin is dict:
            return FieldDefinition(name=name, field_type=FieldType.JSON)

        # Handle basic types
        return self._handle_basic_type(name, annotation, depth)

    def _handle_union(
        self,
        name: str,
        args: tuple,
        field_info: FieldInfo,
        depth: int,
    ) -> FieldDefinition:
        """
        Handle Union types, including discriminated unions.

        Args:
            name: Field name
            args: Union type arguments
            field_info: Pydantic FieldInfo
            depth: Current recursion depth

        Returns:
            FieldDefinition for the union
        """
        # Filter out None types
        non_none_args = [a for a in args if a is not type(None)]

        # If only one non-None type, it's Optional[T]
        if len(non_none_args) == 1:
            field_def = self._annotation_to_field(
                name=name,
                annotation=non_none_args[0],
                field_info=field_info,
                depth=depth,
            )
            field_def.required = False
            return field_def

        # Check for discriminated union
        discriminator = getattr(field_info, "discriminator", None)

        if discriminator:
            # This is a discriminated union
            discriminator_values = []
            for arg in non_none_args:
                if hasattr(arg, "model_fields"):
                    disc_field = arg.model_fields.get(discriminator)
                    if disc_field and get_origin(disc_field.annotation) is Literal:
                        literal_args = get_args(disc_field.annotation)
                        if literal_args:
                            discriminator_values.append(str(literal_args[0]))

            return FieldDefinition(
                name=name,
                field_type=FieldType.UNION,
                discriminator=discriminator,
                discriminator_values=discriminator_values,
            )

        # Regular union without discriminator - treat as select
        options = []
        for arg in non_none_args:
            type_name = getattr(arg, "__name__", str(arg))
            options.append({"value": type_name, "label": type_name})

        return FieldDefinition(
            name=name,
            field_type=FieldType.SELECT,
            options=options,
        )

    def _handle_literal(self, name: str, args: tuple) -> FieldDefinition:
        """
        Handle Literal types (for enum-like fields).

        Args:
            name: Field name
            args: Literal arguments

        Returns:
            FieldDefinition for the literal
        """
        if len(args) == 1:
            # Single literal value - likely a discriminator field
            return FieldDefinition(
                name=name,
                field_type=FieldType.TEXT,
                default=args[0],
                readonly=True,
            )

        # Multiple literal values - render as select
        options = [{"value": str(a), "label": str(a)} for a in args]
        return FieldDefinition(
            name=name,
            field_type=FieldType.SELECT,
            options=options,
        )

    def _handle_list(
        self,
        name: str,
        args: tuple,
        depth: int,
    ) -> FieldDefinition:
        """
        Handle List types.

        Args:
            name: Field name
            args: List type arguments
            depth: Current recursion depth

        Returns:
            FieldDefinition for the list
        """
        field_def = FieldDefinition(name=name, field_type=FieldType.LIST)

        if args:
            from pydantic.fields import FieldInfo as FI

            item_field = self._annotation_to_field(
                name=f"{name}_item",
                annotation=args[0],
                field_info=FI(),
                depth=depth + 1,
            )
            field_def.item_type = item_field

        return field_def

    def _handle_basic_type(
        self,
        name: str,
        annotation: Any,
        depth: int,
    ) -> FieldDefinition:
        """
        Handle basic Python types.

        Args:
            name: Field name
            annotation: Type annotation
            depth: Current recursion depth

        Returns:
            FieldDefinition for the type
        """
        # String types
        if annotation is str:
            return FieldDefinition(name=name, field_type=FieldType.TEXT)

        # Numeric types
        if annotation is int:
            return FieldDefinition(name=name, field_type=FieldType.NUMBER)

        if annotation is float:
            return FieldDefinition(name=name, field_type=FieldType.FLOAT)

        # Boolean
        if annotation is bool:
            return FieldDefinition(name=name, field_type=FieldType.BOOLEAN)

        # Enum types
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            options = [{"value": e.value, "label": e.name} for e in annotation]
            return FieldDefinition(
                name=name,
                field_type=FieldType.SELECT,
                options=options,
            )

        # Pydantic models (nested)
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            # Check for circular reference
            model_name = annotation.__name__
            if model_name in self._visited:
                return FieldDefinition(
                    name=name,
                    field_type=FieldType.COMPLEX,
                    description=f"Circular reference to {model_name}",
                )

            self._visited.add(model_name)

            children = []
            for child_name, child_info in annotation.model_fields.items():
                child_def = self._process_field(
                    child_name,
                    child_info,
                    annotation,
                    depth + 1,
                )
                if child_def:
                    children.append(child_def)

            self._visited.discard(model_name)

            return FieldDefinition(
                name=name,
                field_type=FieldType.NESTED,
                children=children,
            )

        # Check for special string types (email, URL, etc.)
        annotation_name = getattr(annotation, "__name__", "").lower()
        if "email" in annotation_name:
            return FieldDefinition(name=name, field_type=FieldType.EMAIL)
        if "url" in annotation_name or "httpurl" in annotation_name:
            return FieldDefinition(name=name, field_type=FieldType.URL)

        # Fallback to text
        return FieldDefinition(name=name, field_type=FieldType.TEXT)

    def _extract_constraints(
        self,
        field_def: FieldDefinition,
        metadata: list[Any],
    ) -> None:
        """
        Extract validation constraints from field metadata.

        Args:
            field_def: The field definition to update
            metadata: List of metadata objects
        """
        for m in metadata:
            # Handle annotated constraints
            if hasattr(m, "min_length"):
                field_def.min_length = m.min_length
            if hasattr(m, "max_length"):
                field_def.max_length = m.max_length
            if hasattr(m, "ge"):
                field_def.min_value = m.ge
            if hasattr(m, "le"):
                field_def.max_value = m.le
            if hasattr(m, "gt"):
                field_def.min_value = m.gt
            if hasattr(m, "lt"):
                field_def.max_value = m.lt
            if hasattr(m, "pattern"):
                field_def.pattern = m.pattern


def walk_model(
    model: Type[BaseModel],
    max_depth: int = 5,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
) -> list[FieldDefinition]:
    """
    Convenience function to walk a model.

    Args:
        model: The Pydantic model to walk
        max_depth: Maximum recursion depth
        exclude: Fields to exclude
        include: Fields to include

    Returns:
        List of FieldDefinition objects
    """
    walker = SchemaWalker(max_depth=max_depth)
    return walker.walk(model, exclude=exclude, include=include)
