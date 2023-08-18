from ignf_gpf_sdk.store.StoreEntity import StoreEntity
from ignf_gpf_sdk.store.interface.TagInterface import TagInterface
from ignf_gpf_sdk.store.interface.EventInterface import EventInterface
from ignf_gpf_sdk.store.interface.CommentInterface import CommentInterface
from ignf_gpf_sdk.store.interface.SharingInterface import SharingInterface
from ignf_gpf_sdk.store.interface.PartialEditInterface import PartialEditInterface


class StoredData(TagInterface, CommentInterface, SharingInterface, EventInterface, PartialEditInterface, StoreEntity):
    """Classe Python représentant l'entité StoredData (donnée stockée)."""

    _entity_name = "stored_data"
    _entity_title = "donnée stockée"
