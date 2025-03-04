from typing import List
from sdk_entrepot_gpf.store.Errors import StoreEntityError
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class LogsInterface(StoreEntity):
    """Interface de StoreEntity pour gérer les logs (logs)."""

    def api_logs(self) -> str:
        """Récupère les logs de cette entité sur l'API.

        Returns:
            str: les logs récupérés
        """
        # Génération du nom de la route
        s_route = f"{self._entity_name}_logs"

        # Numéro de la page
        i_page = 1
        # Flag indiquant s'il faut requêter la prochaine page
        b_next_page = True
        # nombre de ligne
        i_limit = 2000
        # stockage de la liste des logs
        l_logs: List[str] = []

        # on veut toutes les pages
        while b_next_page:
            # On liste les entités à la bonne page
            o_response = ApiRequester().route_request(
                s_route,
                route_params={"datastore": self.datastore, self._entity_name: self.id},
                params={"page": i_page, "limit": i_limit},
            )
            # On les ajoute à la liste
            l_logs += o_response.json()
            # On regarde le Content-Range de la réponse pour savoir si on doit refaire une requête pour récupérer la fin
            b_next_page = ApiRequester.range_next_page(o_response.headers.get("Content-Range"), len(l_logs))
            # On passe à la page suivante
            i_page += 1

        # Les logs sont une liste de string, on concatène tout
        return "\n".join(l_logs)

    def api_logs_filter(self, substring: str) -> List[str]:
        """Récupère les logs de cette entité en renvoyant les lignes contenant la substring passée en paramètre.

        Args:
            substring: filtres sur les lignes de logs

        Return:
            List[str]: listes des lignes renvoyées
        """
        s_route = f"{self._entity_name}_logs"

        # Numéro de la page
        i_page = 1
        # Flag indiquant s'il faut requêter la prochaine page
        b_next_page = True
        # nombre de ligne
        i_limit = 2000
        # stockage de la liste des logs
        l_logs: List[str] = []

        # on veut toutes les pages
        while b_next_page:
            # On liste les entités à la bonne page
            o_response = ApiRequester().route_request(
                s_route,
                route_params={"datastore": self.datastore, self._entity_name: self.id},
                params={"page": i_page, "limit": i_limit},
            )
            # On les ajoute à la liste
            l_logs += o_response.json()
            # On regarde le Content-Range de la réponse pour savoir si on doit refaire une requête pour récupérer la fin
            b_next_page = ApiRequester.range_next_page(o_response.headers.get("Content-Range"), len(l_logs))
            # On passe à la page suivante
            i_page += 1
        return [s_line for s_line in l_logs if substring in s_line]

    def api_logs_advanced(self, page: int = 1, line_per_page: int = 1000) -> dict[str, any]:
        """
            Récupère les logs de l'entité a la page souhaité
        Returns:
            dict[str, any]: contiendra la logs: List[str] qui sera la liste des logs, last_page: bool si on est sur la dernière page,
                                total_page: int qui sera le nombre de page
        """
        d_response = dict()
        s_route = f"{self._entity_name}_logs"
        # on récupère la page souhaitée
        o_response = ApiRequester().route_request(
            s_route,
            route_params={"datastore": self.datastore, self._entity_name: self.id},
            params={"page": page, "limit": line_per_page},
        )
        # On récupère le nombre de page en fonction du nombre de ligne par page.
        i_total_page = ApiRequester.range_total_page(o_response.headers.get("Content-Range"), line_per_page)
        if page > i_total_page:
            raise StoreEntityError(f"La première page est en dehors des limites {i_total_page} avec comme paramètre {page} et {line_per_page}")
        d_response["total_page"] = i_total_page
        if page == i_total_page:
            d_response["last_page"] = True
        else:
            d_response["last_page"] = False

        # On les ajoute à la liste
        d_response["logs"] = o_response.json()

        return d_response
