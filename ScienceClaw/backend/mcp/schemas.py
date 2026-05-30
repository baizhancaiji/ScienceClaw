import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


AuthMode = Literal["none", "bearer", "headers"]
VerifyStatus = Literal["unknown", "healthy", "error"]

_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


class MCPHeaderSecret(BaseModel):
    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def validate_header_name(cls, value: str) -> str:
        name = value.strip()
        if not name or not _HEADER_NAME_RE.fullmatch(name):
            raise ValueError("Invalid header name")
        return name


class MCPMaskedHeader(BaseModel):
    name: str
    masked_value: str


class CreateMCPServerRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    endpoint_url: str
    auth_mode: AuthMode = "none"
    bearer_token: str | None = None
    headers: list[MCPHeaderSecret] = Field(default_factory=list)
    enabled: bool = True
    verify_now: bool = False

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise ValueError("name must contain at least 2 characters")
        return name

    @field_validator("endpoint_url")
    @classmethod
    def validate_https_endpoint(cls, value: str) -> str:
        endpoint_url = value.strip()
        if not endpoint_url.startswith("https://"):
            raise ValueError("endpoint_url must start with https://")
        return endpoint_url

    @model_validator(mode="after")
    def validate_auth_config(self):
        if self.auth_mode == "bearer" and not (self.bearer_token or "").strip():
            raise ValueError("bearer auth requires bearer_token")
        if self.auth_mode == "headers" and not self.headers:
            raise ValueError("headers auth requires at least one header")
        return self


class UpdateMCPServerRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=64)
    endpoint_url: str | None = None
    auth_mode: AuthMode | None = None
    bearer_token: str | None = None
    headers: list[MCPHeaderSecret] | None = None
    enabled: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if len(name) < 2:
            raise ValueError("name must contain at least 2 characters")
        return name

    @field_validator("endpoint_url")
    @classmethod
    def validate_https_endpoint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        endpoint_url = value.strip()
        if not endpoint_url.startswith("https://"):
            raise ValueError("endpoint_url must start with https://")
        return endpoint_url

    @model_validator(mode="after")
    def validate_auth_config(self):
        if (
            self.auth_mode == "bearer"
            and self.bearer_token is not None
            and not self.bearer_token.strip()
        ):
            raise ValueError("empty bearer_token does not update an existing secret")
        if self.auth_mode == "headers" and self.headers is not None and not self.headers:
            raise ValueError("headers auth requires at least one header")
        return self


class ToggleMCPServerRequest(BaseModel):
    enabled: bool


class MCPServerListItem(BaseModel):
    id: str
    name: str
    slug: str
    transport: Literal["https"] = "https"
    endpoint_url: str
    auth_mode: AuthMode
    enabled: bool
    verify_status: VerifyStatus = "unknown"
    verify_error: str = ""
    tool_count: int = 0
    last_verified_at: int | None = None
    last_synced_at: int | None = None
    has_bearer_token: bool = False
    masked_headers: list[MCPMaskedHeader] = Field(default_factory=list)


class MCPServerDetailItem(MCPServerListItem):
    created_at: int | None = None
    updated_at: int | None = None
