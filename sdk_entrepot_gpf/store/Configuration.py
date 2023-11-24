from typing import Any, Callable, Dict, List, Optional

from sdk_entrepot_gpf.store.Offering import Offering
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.store.interface.TagInterface import TagInterface
from sdk_entrepot_gpf.store.interface.CommentInterface import CommentInterface
from sdk_entrepot_gpf.store.interface.EventInterface import EventInterface
from sdk_entrepot_gpf.store.interface.FullEditInterface import FullEditInterface
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class Configuration(TagInterface, CommentInterface, EventInterface, FullEditInterface, StoreEntity):
    """Classe Python représentant l'entité Configuration (configuration)."""

    _entity_name = "configuration"
    _entity_title = "configuration"

    STATUS_UNPUBLISHED = "UNPUBLISHED"
    STATUS_PUBLISHED = "PUBLISHED"
    STATUS_SYNCHRONIZING = "SYNCHRONIZING"

    def api_list_offerings(self) -> List[Offering]:
        """Liste les Offering liées à cette Configuration.
        Returns:
            List[Offering]: liste des Offering trouvées
        """

        # Génération du nom de la route
        s_route = f"{self._entity_name}_list_offerings"
        # Requête "get"
        o_response = ApiRequester().route_request(
            s_route,
            method=ApiRequester.GET,
            route_params={"datastore": self.datastore, self._entity_name: self.id},
        )
        # Instanciation de chaque élément renvoyé dans la liste
        l_offerings: List[Offering] = [Offering(i) for i in o_response.json()]

        return l_offerings

    def api_add_offering(self, data_offering: Dict[str, Any]) -> Offering:
        """Ajoute une Offering à cette Configuration.
        Args:
            data_offering (Dict[str, Any]): données pour la création de l'Offering
        Returns:
            Offering: représentation Python de l'Offering créée
        """
        return Offering.api_create(data_offering, route_params={self._entity_name: self.id})

    def delete_cascade(self, before_delete: Optional[Callable[[List["StoreEntity"]], List["StoreEntity"]]] = None) -> None:
        """Fonction de suppression de la Configuration en supprimant en cascade les offres liées (et uniquement les offres, pas les données stockées).

        Args:
            before_delete (Optional[Callable[[List[StoreEntity]], List[StoreEntity]]], optional): fonction à lancer avant la suppression (entrée : liste des entités à supprimer,
                sortie : liste définitive des entités à supprimer). Defaults to None.
        """
        # suppression d'une configuration : offres puis configuration
        l_entities: List[StoreEntity] = []
        l_offering = self.api_list_offerings()
        l_entities += l_offering
        l_entities.append(self)
        self.delete_liste_entities(l_entities, before_delete)
