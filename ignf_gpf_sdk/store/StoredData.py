from typing import Optional, List, Callable

from ignf_gpf_sdk.store.Configuration import Configuration
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

    STATUS_CREATED = "CREATED"
    STATUS_GENERATING = "GENERATING"
    STATUS_MODIFYING = "MODIFYING"
    STATUS_GENERATED = "GENERATED"
    STATUS_DELETED = "DELETED"
    STATUS_UNSTABLE = "UNSTABLE"

    def delete_cascade(self, before_delete: Optional[Callable[[List["StoreEntity"]], List["StoreEntity"]]] = None) -> None:
        """suppression en cascade des offres : uniquement les offres

        Args:
            before_delete (Optional[Callable[[List[StoreEntity]], List[StoreEntity]]], optional): fonction à lancé avant la suppression entrée liste des entités à supprimé,
                sortie liste définitive des entités à supprimer. Defaults to None.
        """
        # suppression d'une stored_data : uniquement l'upload, configuration et stored_data
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
