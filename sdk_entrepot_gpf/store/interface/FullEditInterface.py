from typing import Dict
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class FullEditInterface(StoreEntity):
    """Interface de StoreEntity pour gérer les étiquettes (tags)."""

    def api_full_edit(self, data_edit: Dict[str, str]) -> None:
        """Modifie complètement l'entité sur l'API (PUT).

        Args:
            data_edit (Dict[str, str]): nouvelles valeurs de propriétés
        """
        # Requête
        ApiRequester().route_request(
            f"{self._entity_name}_full_edit",
            data=data_edit,
            method=ApiRequester.PUT,
            route_params={self._entity_name: self.id, "datastore": self.datastore},
        )

        # Mise à jour du stockage local (_store_api_dict)
        self.api_update()
