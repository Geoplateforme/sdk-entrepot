from abc import ABC, abstractmethod
from typing import Any


class AbstractResolver(ABC):
    """Classe abstraite permettant de résoudre le paramétrage des fichiers d'action.

    Vous pouvez créer vos propres classe de résolution en les héritant de
    celle-ci et en les ajoutant au GlobalResolver.

    Attributes:
        __name (str): nom de code du resolver
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self.__name: str = name

    @abstractmethod
    def resolve(self, string_to_solve: str, **kwargs: Any) -> str:
        """Résout la chaîne à traiter et retourne la chaîne obtenue.

        Args:
            string_to_solve (str): chaîne à résoudre
            kwargs (Any): paramètres supplémentaires.

        Returns:
            chaîne résolue
        """

    @property
    def name(self) -> str:
        return self.__name
