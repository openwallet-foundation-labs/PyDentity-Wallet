from pydantic import Field
from typing import List, Dict, Any, Optional

from .base import CustomBaseModel


class IssuerInfo(CustomBaseModel):
    """Issuer information in W3C VC format"""
    id: str = Field(..., description="Issuer DID or identifier")
    name: str = Field(..., description="Human-readable issuer name")
    image: Optional[str] = Field(None, description="URL to issuer logo/image")


class CredentialSchema(CustomBaseModel):
    """Schema information for the credential"""
    id: str = Field(..., description="Schema identifier (URL or AnonCreds schema ID)")
    type: str = Field(..., description="Schema type (e.g., 'JsonSchema', 'AnonCredsSchema')")
    name: Optional[str] = Field(None, description="Human-readable schema name")
    version: Optional[str] = Field(None, description="Schema version")
    description: Optional[str] = Field(None, description="Schema description or version info")


class Credential(CustomBaseModel):
    """
    W3C Verifiable Credential v2 model.
    
    This represents credentials in W3C VC format, which can contain:
    - AnonCreds credentials (transformed via beautify_anoncreds)
    - Native W3C VCs
    - Other credential formats
    """
    context: List[str] = Field(
        ...,
        alias="@context",
        description="JSON-LD context URLs"
    )
    type: List[str] = Field(
        ...,
        description="Credential types (always includes 'VerifiableCredential')"
    )
    id: Optional[str] = Field(
        None,
        description="Unique credential identifier (e.g., urn:uuid:...)"
    )
    name: str = Field(
        ...,
        description="Human-readable credential name"
    )
    issuer: IssuerInfo = Field(
        ...,
        description="Issuer information"
    )
    validFrom: str = Field(
        ...,
        description="ISO 8601 timestamp when credential becomes valid"
    )
    validUntil: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when credential expires"
    )
    credentialSubject: Dict[str, Any] = Field(
        ...,
        description="Claims about the credential subject"
    )
    credentialSchema: Optional[CredentialSchema] = Field(
        None,
        description="Schema that this credential conforms to"
    )
    credentialStatus: Optional[Dict[str, Any]] = Field(
        None,
        description="Status information (e.g., revocation)"
    )
    proof: Optional[Dict[str, Any]] = Field(
        None,
        description="Cryptographic proof"
    )
    
    class Config:
        populate_by_name = True  # Allow using both 'context' and '@context'
    
    # Note: Metadata (schema_id, schema_name, cred_def_id, cred_ex_id, received_at)
    # is stored in Askar tags, not in the credential itself, to keep the W3C VC clean.


class CredentialOffer(CustomBaseModel):
    """Credential offer from issuer"""
    cred_ex_id: str = Field(..., description="Credential exchange ID")
    connection_id: str = Field(..., description="Connection ID")
    schema_id: str = Field(..., description="Schema ID")
    schema_name: Optional[str] = Field(None, description="Schema name")
    cred_def_id: str = Field(..., description="Credential definition ID")
    issuer_name: Optional[str] = Field(None, description="Issuer name")
    credential_preview: Optional[Dict[str, Any]] = Field(
        None,
        description="Preview of credential attributes"
    )
    state: str = Field(..., description="Offer state")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class CredentialRequest(CustomBaseModel):
    """Credential request to issuer"""
    cred_ex_id: str = Field(..., description="Credential exchange ID")
    connection_id: str = Field(..., description="Connection ID")
    state: str = Field(..., description="Request state")

