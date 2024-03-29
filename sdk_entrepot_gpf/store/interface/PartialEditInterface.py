from typing import Any, Dict
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class PartialEditInterface(StoreEntity):
    """Interface de StoreEntity pour gérer l'édition partielle de l'entité."""

    def api_partial_edit(self, data_edit: Dict[str, str]) -> None:
        """Modifie partiellement l'entité sur l'API (PATCH).

        Args:
            data_edit (Dict[str, str]): nouvelles valeurs pour les propriétés à modifier
        """
        # Requête
        ApiRequester().route_request(
            f"{self._entity_name}_partial_edit",
            data=data_edit,
            method=ApiRequester.PATCH,
            route_params={self._entity_name: self.id, "datastore": self.datastore},
        )

        # Mise à jour du stockage local (_store_api_dict)
        self.api_update()

    def edit(self, data_edit: Dict[str, Any]) -> None:
        """Mise à jour partiel de l'entité

        Args:
            data_edit (Dict[str, Any]): nouvelles valeurs de propriétés
        """
        self.api_partial_edit(data_edit)
