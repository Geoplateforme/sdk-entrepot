from typing import Any, Dict

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.workflow.resolver.AbstractResolver import AbstractResolver
from sdk_entrepot_gpf.workflow.resolver.Errors import ResolveUserError


class UserResolver(AbstractResolver):
    """Classe permettant de récupérer les informations sur l'utilisateur authentifié.

    La plu-value sur la classe DictRevolver est que les info de l'utilisateur sont
    directement récupérées par le constructeur de la classe (ça évite de gérer cela).

    Attributes :
        __name (str): nom de code du resolver
        __username_data (Dict[str, Any]): liste des infos de l'utilisateur authentifié
    """

    def __init__(self, name: str) -> None:
        """A l'instanciation, on récupère les infos de l'utilisateur via l'API et on les stocke.

        Args:
            name (str): nom du résolveur
        """
        super().__init__(name)
        # On récupère les infos sur l'API
        o_response = ApiRequester().route_request("user_get")
        self.__user_data: Dict[str, Any] = o_response.json()

    def resolve(self, string_to_solve: str) -> Any:
        # La chaîne à résoudre est en fait la clé, donc il suffit de renvoyer la valeur associée
        if string_to_solve in self.__user_data:
            return str(self.__user_data[string_to_solve])
        # Sinon on lève une exception
        raise ResolveUserError(self.name, string_to_solve)
