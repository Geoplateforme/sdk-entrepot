from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.store.interface.PartialEditInterface import PartialEditInterface


class Permission(PartialEditInterface, StoreEntity):
    """Classe Python représentant l'entité des permissions."""

    _entity_name = "permission"
    _entity_title = "permission"
