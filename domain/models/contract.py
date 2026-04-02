"""
Contract domain model.

Represents a legal contract with its metadata and extracted content.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Contract:
    """
    Domain model representing a legal contract.

    Attributes:
        id: Unique identifier for the contract
        title: Contract title or name
        file_path: Path to the original PDF file
        full_text: Complete extracted text from the contract
        upload_date: Timestamp when the contract was uploaded
        metadata: Additional metadata (page count, file size, etc.)
    """
    id: str
    title: str
    file_path: Path
    full_text: str
    upload_date: datetime = field(default_factory=datetime.now)
    metadata: Optional[dict] = field(default_factory=dict)

    def __post_init__(self):
        """Validate contract data after initialization."""
        if not self.full_text or len(self.full_text.strip()) == 0:
            raise ValueError("Contract text cannot be empty")

        if not self.file_path.exists():
            raise FileNotFoundError(f"Contract file not found: {self.file_path}")

    def get_summary(self, max_length: int = 500) -> str:
        """
        Get a truncated summary of the contract text.

        Args:
            max_length: Maximum length of the summary in characters.

        Returns:
            Truncated contract text.
        """
        return self.full_text[:max_length] + "..." if len(self.full_text) > max_length else self.full_text