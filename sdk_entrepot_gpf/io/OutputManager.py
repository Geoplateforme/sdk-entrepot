import logging
from typing import Dict, Optional

from sdk_entrepot_gpf.pattern.Singleton import Singleton
from sdk_entrepot_gpf.io.Color import Color


class OutputManager(metaclass=Singleton):
    """Classe de gestion du log."""

    def __init__(self, file_logger: Optional[str] = None, pattern_formater: Optional[str] = None) -> None:
        """La classe est instanciée à partir d'un fichier de log et d'un modèle de format de log.

        Args:
            file_logger (Optional[str], optional): Chemin vers le fichier de log ou `None` si on ne veux pas de fichier de log.
            pattern_formater (Optional[str], optional): Modèle de format du log (cf doc
                [logging](https://docs.python.org/fr/3/library/logging.html#logging.Formatter)) ou `None` si on veut le format par défaut.
        """
        # initialisation du loger
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.INFO)

        # création formateur
        o_formatter = logging.Formatter(pattern_formater)

        # ajout handler console : affichage des logs dans la console
        o_ch = logging.StreamHandler()
        o_ch.setLevel(level=logging.DEBUG)
        o_ch.setFormatter(o_formatter)
        self.__logger.addHandler(o_ch)

        # ajout handler fichier : écriture des logs dans un fichier
        if file_logger:
            o_fh = logging.FileHandler(file_logger)
            o_fh.setLevel(level=logging.DEBUG)
            o_fh.setFormatter(o_formatter)
            self.__logger.addHandler(o_fh)

    def debug(self, message: str) -> None:
        """Ajout d'un message de type debug
        Args:
            message (str): message de type debug à journaliser
        """
        self.__logger.debug("%sDEBUG - %s%s", Color.GREY, message, Color.END)

    def info(self, message: str, green_colored: bool = False) -> None:
        """Ajout d'un message de type info

        Args:
            message (str): message de type info à journaliser
            green_colored (bool, optional): indique si le message doit être écrit en vert (par défaut False)
        """
        if green_colored is False:
            self.__logger.info("INFO - %s", message)
        else:
            self.__logger.info("%sINFO - %s%s", Color.GREEN, message, Color.END)

    def warning(self, message: str, yellow_colored: bool = True) -> None:
        """Ajout d'un message de type warning
        Args:
            message (str): message de type warning à journaliser
            yellow_colored (bool, optional): indique si le message doit être écrit en jaune (par défaut True)
        """
        if yellow_colored is False:
            self.__logger.warning("ALERTE - %s", message)
        else:
            self.__logger.warning("%sALERTE - %s%s", Color.YELLOW, message, Color.END)

    def error(self, message: str, red_colored: bool = True) -> None:
        """Ajout d'un message de type erreur
        Args:
            message (str): message de type erreur à journaliser
            red_colored (bool, optional): indique si le message doit être écrit en rouge (par défaut False)
        """
        if red_colored is False:
            self.__logger.error("ERREUR - %s", message)
        else:
            self.__logger.error("%sERREUR - %s%s", Color.RED, message, Color.END)

    def critical(self, message: str, red_colored: bool = True) -> None:
        """Ajout d'un message de type critique (apparaît en rouge dans la console)
        Args:
            message (str): message de type critique à journaliser
            red_colored (bool, optional): indique si le message doit être écrit en rouge (par défaut True)
        """
        if red_colored is False:
            self.__logger.critical("ERREUR FATALE - %s", message)
        else:
            self.__logger.critical("%sERREUR FATALE - %s%s", Color.RED, message, Color.END)

    def set_log_level(self, level: str) -> None:
        """Défini le niveau de log du logger.

        Args:
            level (str): niveau de log (DEBUG, INFO, WARNING, ERROR ou CRITICAL)
        """
        d_level: Dict[str, int] = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        if level in d_level:
            self.__logger.setLevel(d_level[level])
