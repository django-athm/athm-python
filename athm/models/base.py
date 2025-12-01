"""Base model for ATH Movil API models."""

from pydantic import BaseModel, ConfigDict


class ATHMovilBaseModel(BaseModel):
    """Base model with common configuration for ATH Movil API models."""

    model_config = ConfigDict(populate_by_name=True)
