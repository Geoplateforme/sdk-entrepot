from typing import Any, Dict, List, Optional, Type
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester

from sdk_entrepot_gpf.store.StoreEntity import StoreEntity, T
from sdk_entrepot_gpf.store.Errors import StoreEntityError


class Access(StoreEntity):
    """Classe Python représentant l'entité Access (point de montage)."""

    _entity_name = "Access"
    _entity_title = "point de montage"

    @classmethod
    def api_list(cls: Type[T], infos_filter: Optional[Dict[str, str]] = None, tags_filter: Optional[Dict[str, str]] = None, page: Optional[int] = None, datastore: Optional[str] = None) -> List[T]:
        """Liste les points de montage de l'API respectant les paramètres donnés.

        Args:
            infos_filter: Filtres sur les attributs sous la forme `{"nom_attribut": "valeur_attribut"}`
            tags_filter: Filtres sur les tags sous la forme `{"nom_tag": "valeur_tag"}`
            page: Numéro page à récupérer, toutes si None.
            datastore: Identifiant du datastore

        Returns:
            List[T]: liste des entités retournées
        """
        # Gestion des paramètres nuls
        infos_filter = infos_filter if infos_filter is not None else {}
        tags_filter = tags_filter if tags_filter is not None else {}

        # Requête
        o_response = ApiRequester().route_request("datastore_get", route_params={"datastore": datastore})

        # Liste pour stocker les Accesss correspondants
        l_Accesss: List[T] = []

        # Pour chaque Accesss en dictionnaire
        for d_Access in o_response.json()["Accesss"]:
            # On suppose qu'il est ok
            b_ok = True
            # On vérifie s'il respecte les critère d'attributs
            for k, v in infos_filter.items():
                if str(d_Access["Access"].get(k)) != str(v):
                    b_ok = False
                    break
            # S'il est ok au final, on l'ajoute
            if b_ok:
                l_Accesss.append(cls(d_Access["Access"]))
        # A la fin, on renvoie la liste
        return l_Accesss

    def api_update(self) -> None:
        return None

    @classmethod
    def api_get(cls: Type[T], data: Optional[Dict[str, Any]], route_params: Optional[Dict[str, Any]] = None) -> T:
        """Crée une nouvelle entité dans l'API.

        Args:
            data: Données nécessaires pour la création.
            route_params: Paramètres de résolution de la route.

        Returns:
            (StoreEntity): Entité créée
        """
        raise StoreEntityError("Impossible de créer un Access")

    @classmethod
    def api_create(cls: Type[T], id_: str, datastore: Optional[str] = None) -> T:
        """Récupère une entité depuis l'API.

        Args:
            id_: Identifiant de l'entité
            datastore: Identifiant du datastore

        Returns:
            (StoreEntity): L'entité instanciée correspondante
        """
        l_Accesss = cls.api_list(datastore=datastore)
        for o_Access in l_Accesss:
            if o_Access["_id"] == id_:
                return o_Access
        raise StoreEntityError(f"le Access {id_} est introuvable")

    def api_delete(self) -> None:
        """Supprime l'entité de l'API."""
        raise StoreEntityError("Impossible de supprimer un Access")
