from typing import List
from sdk_entrepot_gpf.store.Errors import StoreEntityError
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class LogsInterface(StoreEntity):
    """Interface de StoreEntity pour gérer les logs (logs)."""

    def api_logs(self) -> str:
        """Récupère les logs de cette entité en renvoyant les lignes contenant la substring passée en paramètre.

        Return:
            str: listes des lignes renvoyées
        """
        return "\n".join(self.api_logs_filter())

    def api_logs_filter(  # pylint:disable=too-many-branches
        self,
        first_page: int = 1,
        last_page: int = 0,
        line_per_page: int = 2000,
        str_filter: str = "",
    ) -> List[str]:
        """Récupère les logs de l'entité en fonction des différents filtres

        Returns:
            List[str]: les logs récupérés.
        """
        s_route = f"{self._entity_name}_logs"
        # stockage de la liste des logs
        l_logs: List[str] = []
        if line_per_page < 1:
            raise StoreEntityError(f"Le nombre de lignes par page ({line_per_page}) doit être positif.")
        o_response = ApiRequester().route_request(
            s_route,
            route_params={"datastore": self.datastore, self._entity_name: self.id},
            params={"page": 1, "limit": line_per_page},
        )
        # On récupère le nombre de page en fonction du nombre de ligne par page.
        i_total_page = ApiRequester.range_total_page(o_response.headers.get("Content-Range"), line_per_page)
        if abs(first_page) > i_total_page:
            raise StoreEntityError(f"La première page demandée ({first_page}) est en dehors des limites ({i_total_page}).")
        if abs(last_page) > i_total_page:
            raise StoreEntityError(f"La dernière page demandée ({last_page}) est en dehors des limites ({i_total_page}).")
        # On initialise la première page
        if first_page > 0:
            i_firstpage = first_page
        elif first_page < 0:
            i_firstpage = i_total_page + first_page + 1
        else:
            i_firstpage = 1
        # On initialise la dernière page
        if last_page > 0:
            i_lastpage = last_page
        elif last_page < 0:
            i_lastpage = i_total_page + last_page + 1
        else:
            i_lastpage = i_total_page
        if i_firstpage > i_lastpage:
            raise StoreEntityError(f"La dernière page doit être supérieure à la première ({i_firstpage}, {i_lastpage}).")

        # on récupère les pages souhaitées
        while i_firstpage <= i_lastpage:
            # On liste les entités à la bonne page
            o_response = ApiRequester().route_request(
                s_route,
                route_params={"datastore": self.datastore, self._entity_name: self.id},
                params={"page": i_firstpage, "limit": line_per_page},
            )
            # On les ajoute à la liste
            l_logs += o_response.json()
            # On passe à la page suivante
            i_firstpage += 1
        l_result: List[str] = []
        for s_line in l_logs:
            if str_filter in s_line or str_filter == "":
                l_result.append(s_line)
        return l_result
