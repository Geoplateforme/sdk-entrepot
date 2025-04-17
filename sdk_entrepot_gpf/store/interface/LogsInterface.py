from typing import List
from sdk_entrepot_gpf.store.Errors import StoreEntityError
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester


class LogsList:
    """Classe pour le renvoie de la fonction api_logs_filter"""

    def __init__(self, logs: List[str], first_page: int, last_page: int, total_page: int, starting_logs: bool, ending_logs: bool, entity: "LogsInterface"):
        self.logs = logs
        self.first_page = first_page
        self.last_page = last_page
        self.total_page = total_page
        self.starting_logs = starting_logs
        self.ending_logs = ending_logs
        self.entity = entity


class LogsInterface(StoreEntity):
    """Interface de StoreEntity pour gérer les logs (logs)."""

    def api_logs(self) -> str:
        """Récupère les logs de cette entité en renvoyant les lignes contenant la substring passée en paramètre.

        Return:
            str: listes des lignes renvoyées
        """
        return "\n".join(self.api_logs_filter().logs)

    def api_logs_filter(self, first_page: int = 1, last_page: int = 0, line_per_page: int = 2000, str_filter: str = "") -> LogsList:
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
        i_firstpage = first_page
        if first_page < 0:
            i_firstpage = i_total_page + first_page + 1
        elif first_page == 0:
            i_firstpage = 1
        # On initialise la dernière page
        i_lastpage = last_page
        if last_page < 0:
            i_lastpage = i_total_page + last_page + 1
        elif last_page == 0:
            i_lastpage = i_total_page
        if i_firstpage > i_lastpage:
            raise StoreEntityError(f"La dernière page doit être supérieur à la première ({i_firstpage}, {i_lastpage}).")
        i_page = i_firstpage
        # on récupère les pages souhaitées
        while i_page <= i_lastpage:
            # On liste les entités à la bonne page
            o_response = ApiRequester().route_request(
                s_route,
                route_params={"datastore": self.datastore, self._entity_name: self.id},
                params={"page": i_page, "limit": line_per_page},
            )
            # On les ajoute à la liste
            l_logs += o_response.json()
            # On passe à la page suivante
            i_page += 1
        l_result: List[str] = []
        for s_line in l_logs:
            if str_filter in s_line or str_filter == "":
                l_result.append(s_line)
        return LogsList(l_result, i_firstpage, i_lastpage, i_total_page, i_firstpage == 1, i_lastpage == i_total_page, self)
