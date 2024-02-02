from typing import Any

from sdk_entrepot_gpf.workflow.resolver.AbstractResolver import AbstractResolver


class DumbResolver(AbstractResolver):
    """Classe permettant de résoudre en renvoyant la clef.

    Attributes:
        __name (str): nom de code du resolver
        __key_value (Dict[str, Any]): liste des paramètres à résoudre
    """

    def resolve(self, string_to_solve: str, **kwargs: Any) -> str:
        return string_to_solve
