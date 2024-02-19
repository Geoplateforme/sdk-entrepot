from pathlib import Path
from typing import Any, Dict, List, Optional

from sdk_entrepot_gpf.helper.JsonHelper import JsonHelper
from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.Errors import GpfSdkError


class DescriptorFileReader:
    """Classe permettant de lire et de valider le fichier descripteur de téléversement de fichiers .

    Attributes:
        __descriptor_dict (Optional[Dict[Any, Any]]): Contenu du fichier descriptif
        __data (List[Dict[str, Any]]): Liste des data contenus dans le fichier descripteur de téléversement
        __parent_folder (path): Chemin du dossier parent des données
        __data_type (str): type de donnée traité
    """

    def __init__(self, descriptor_file_path: Path, data_type: str) -> None:
        """La classe est instanciée à partir du fichier descripteur de téléversement.

        Les différents chemins indiqués sont alors vérifiés et les fichiers à téléverser sont listés.

        Args:
            descriptor_file_path (Path): chemin vers le fichier descripteur de téléversement
        """
        # Définition des attributs
        self.__data_type = data_type
        self.__descriptor_dict: Optional[Dict[Any, Any]] = None
        self.__data: List[Dict[str, Any]] = []
        self.__parent_folder = descriptor_file_path.parent.absolute()
        # Ouverture du fichier descripteur de téléversement
        self.__descriptor_dict = JsonHelper.load(descriptor_file_path, file_not_found_pattern="Fichier descripteur de téléversement {json_path} non trouvé.")

        # Ouverture du schéma JSON à respecter
        p_schema_file_path = Config.conf_dir_path / Config().get_str("json_schemas", f"{data_type}_descriptor_file")
        d_schema = JsonHelper.load(p_schema_file_path, file_not_found_pattern="Schéma de fichier descriptif de téléversement {json_path} non trouvé. Contactez le support.")

        # Valide le fichier descriptif
        JsonHelper.validate_object(
            self.__descriptor_dict,
            d_schema,
            f"Fichier descriptif de téléversement {descriptor_file_path} non valide.",
            "Schéma du fichier descriptif de téléversement non valide. Contactez le support.",
        )

        # Vérification de l'existence des répertoires décrits dans le fichier
        self.__validate_pathes()
        # Vérification de l'existence des répertoires décrits dans le fichier et fabrication des chemins absolus à partir des chemins relatifs
        self.__instantiate_data()

    def __validate_pathes(self) -> None:
        """Vérifie si les répertoires existent (s'interrompt si l'un d'entre eux n'existe pas).

        Raises:
            GpfSdkError : si un répertoire décrit dans le fichier descripteur n'existe pas
        """
        # liste qui va servir à lister les dossiers en erreurs
        l_liste_file_non_valide: List[str] = []
        # On parcours la liste des datasets
        if self.__descriptor_dict is not None:
            for l_dataset in self.__descriptor_dict[self.__data_type]:
                # on parcours la liste des dossiers de chaque dataset
                if l_dataset["file"]:
                    p_file_path = self.__parent_folder / l_dataset["file"]
                    if not p_file_path.exists():
                        l_liste_file_non_valide.append(str(p_file_path))
            # si à la fin du parcours des dossiers la liste n'est pas vide, on lève une erreur:
            if l_liste_file_non_valide:
                # affiche la liste des dossiers non valides
                Config().om.error("Liste des fichiers à téléverser non existants :\n  * {}".format("\n  * ".join(l_liste_file_non_valide)))
                raise GpfSdkError("Au moins un des fichier listés dans le fichier descripteur de téléversement n'existe pas.")

    def __instantiate_data(self) -> None:
        """Instancie les datasets."""
        if self.__descriptor_dict is not None:
            self.__data = list(self.__descriptor_dict[self.__data_type])

    @property
    def data(self) -> List[Dict[str, Any]]:
        return self.__data
