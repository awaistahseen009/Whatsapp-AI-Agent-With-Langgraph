from pydantic import BaseModel, Field


class DocumentUploadMeta(BaseModel):
    doc_type: str = Field(
        description="Type of document: property_listing, area_guide, policy, faq, developer_profile, legal"
    )
