from abc import ABC, abstractmethod
from typing import List
from src.core.models import ActivityEvent, CollectionMeta


class NFTDataProvider(ABC):
    """Abstract base class for fetching NFT activity and metadata."""

    @abstractmethod
    async def get_collection_metadata(
        self, contract_address: str, chain: str
    ) -> CollectionMeta:
        """Fetch collection name, logo, floor price, etc."""
        pass

    @abstractmethod
    async def get_user_activity(
        self, wallet_address: str, contract_address: str, chain: str
    ) -> List[ActivityEvent]:
        """Fetch user's transaction/activity history for the NFT contract."""
        pass
