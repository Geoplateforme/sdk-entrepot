import time
from sdk_entrepot_gpf.io.Errors import NotFoundError
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.store.interface.PartialEditInterface import PartialEditInterface
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class Offering(PartialEditInterface, StoreEntity):
    """Classe Python représentant l'entité Offering (offre)."""

    _entity_name = "offering"
    _entity_title = "offre"

    STATUS_PUBLISHING = "PUBLISHING"
    STATUS_MODIFYING = "MODIFYING"
    STATUS_PUBLISHED = "PUBLISHED"
    STATUS_UNPUBLISHING = "UNPUBLISHING"
    STATUS_UNSTABLE = "UNSTABLE"

    VISIBILITY_PRIVATE = "PRIVATE"
    VISIBILITY_REFERENCED = "REFERENCED"
    VISIBILITY_PUBLIC = "PUBLIC"

    def api_delete(self) -> None:
        # on effectue la suppression normale
        super().api_delete()
        # attente que la suppression soit faite
        try:
            while True:
                # mise à jour jusqu'à avoir 404
                self.api_update()
                time.sleep(1)

        except NotFoundError:
            # on a un 404 donc l'offre est bien supprimée
            return

    def api_synchronize(self) -> None:
        """répercuter des modifications sur la configuration ou les données stockées utilisées au niveau des services de diffusion"""
        ApiRequester().route_request(
            f"{self._entity_name}_synchronize",
            method=ApiRequester.PUT,
            route_params={self._entity_name: self.id, "datastore": self.datastore},
        )

        # Mise à jour du stockage local (_store_api_dict)
        self.api_update()
