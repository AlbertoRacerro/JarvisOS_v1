from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelImplementationCreateRequest(BaseModel):
    """Public model-registration contract.

    Executable source and trust-shaped fields are deliberately absent. The generic
    route can only instantiate the reviewed bundled batch-growth implementation;
    other bundled models keep their dedicated registration endpoints.
    """

    model_config = ConfigDict(extra="forbid")

    model_spec_id: str = Field(min_length=1)
    version_label: str = "batch-growth-v0"
    implementation_kind: Literal["batch_growth_v0", "calc_v0", "bluecad_l2_v0"] = "batch_growth_v0"
    notes: str | None = None
    input_contract: dict[str, Any] | None = None
