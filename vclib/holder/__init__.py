"""
Identity Owner module
"""

# Add imports from `owner/src` here to expose objects under vclib.owner
from .src.holder import Holder as Holder
from .src.storage.abstract_storage_provider import (
    AbstractStorageProvider as AbstractStorageProvider,
)
from .src.storage.local_storage_provider import (
    LocalStorageProvider as LocalStorageProvider,
)
from .src.web_holder import WebHolder as WebHolder
