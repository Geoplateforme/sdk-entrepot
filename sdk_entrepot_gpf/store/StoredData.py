from typing import Optional, List, Callable

from sdk_entrepot_gpf.store.Configuration import Configuration
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.store.interface.TagInterface import TagInterface
from sdk_entrepot_gpf.store.interface.EventInterface import EventInterface
from sdk_entrepot_gpf.store.interface.CommentInterface import CommentInterface
from sdk_entrepot_gpf.store.interface.SharingInterface import SharingInterface
from sdk_entrepot_gpf.store.interface.PartialEditInterface import PartialEditInterface


class StoredData(TagInterface, CommentInterface, SharingInterface, EventInterface, PartialEditInterface, StoreEntity):
    """Classe Python représentant l'entité StoredData (donnée stockée)."""

    _entity_name = "stored_data"
    _entity_title = "donnée stockée"

    STATUS_CREATED = "CREATED"
    STATUS_GENERATING = "GENERATING"
    STATUS_MODIFYING = "MODIFYING"
    STATUS_GENERATED = "GENERATED"
    STATUS_DELETED = "DELETED"
    STATUS_UNSTABLE = "UNSTABLE"

    def delete_cascade(self, before_delete: Optional[Callable[[List["StoreEntity"]], List["StoreEntity"]]] = None) -> None:
        """Suppression de la donnée stockée avec suppression en cascade des configuration liées et des offres liées à chaque configuration.

        Args:
            before_delete (Optional[Callable[[List[StoreEntity]], List[StoreEntity]]], optional): fonction à lancer avant la suppression (entrée : liste des entités à supprimer,
                sortie : liste définitive des entités à supprimer). Defaults to None.
        """
        # suppression d'une stored_data : offering et configuration liées puis la stored_data
        l_entities: List[StoreEntity] = []

        # liste des configurations
        l_configuration = Configuration.api_list({"stored_data": self.id})
        for o_configuration in l_configuration:
            # pour chaque configuration on récupère les offerings
            l_offering = o_configuration.api_list_offerings()
            l_entities += l_offering
            l_entities.append(o_configuration)
        # ajout de la stored_data
        l_entities.append(self)

        # suppression
        self.delete_liste_entities(l_entities, before_delete)
