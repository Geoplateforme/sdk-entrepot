"""SDK Python pour simplifier l'utilisation de l'API Entrepôt Géoplateforme."""

import configparser
import io
import sys
import argparse
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union
import shutil

import sdk_entrepot_gpf
from sdk_entrepot_gpf.Errors import GpfSdkError
from sdk_entrepot_gpf.auth.Authentifier import Authentifier
from sdk_entrepot_gpf.helper.JsonHelper import JsonHelper
from sdk_entrepot_gpf.helper.PrintLogHelper import PrintLogHelper
from sdk_entrepot_gpf.io.Color import Color
from sdk_entrepot_gpf.io.Errors import ConflictError
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.workflow.Workflow import Workflow
from sdk_entrepot_gpf.workflow.resolver.GlobalResolver import GlobalResolver
from sdk_entrepot_gpf.workflow.resolver.StoreEntityResolver import StoreEntityResolver
from sdk_entrepot_gpf.workflow.action.UploadAction import UploadAction
from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.io.DescriptorFileReader import DescriptorFileReader
from sdk_entrepot_gpf import store
from sdk_entrepot_gpf.store.Offering import Offering
from sdk_entrepot_gpf.store.Configuration import Configuration
from sdk_entrepot_gpf.store.StoredData import StoredData
from sdk_entrepot_gpf.store.Upload import Upload
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.store.ProcessingExecution import ProcessingExecution
from sdk_entrepot_gpf.store.Datastore import Datastore
from sdk_entrepot_gpf.workflow.resolver.UserResolver import UserResolver


class Main:
    """Classe d'entrée pour utiliser la lib comme binaire."""

    DELETABLE_TYPES = [Upload.entity_name(), StoredData.entity_name(), Configuration.entity_name(), Offering.entity_name()]

    def __init__(self) -> None:
        """Constructeur."""
        # Résolution des paramètres utilisateurs
        self.o_args = Main.parse_args()
        self.datastore: Optional[str] = None

        # Résolution de la config
        if not Path(self.o_args.config).exists():
            raise GpfSdkError(f"Le fichier de configuration précisé ({self.o_args.config}) n'existe pas.")
        Config().read(self.o_args.config)

        # Si debug on monte la config
        if self.o_args.debug:
            Config().om.set_log_level("DEBUG")

        # Résolution du datastore
        self.datastore = self.__datastore()

        # Exécution de l'action demandée
        if self.o_args.task == "auth":
            self.auth()
        elif self.o_args.task == "me":
            self.me_()
        elif self.o_args.task == "config":
            self.config()
        elif self.o_args.task == "upload":
            self.upload()
        elif self.o_args.task == "dataset":
            self.dataset()
        elif self.o_args.task == "workflow":
            self.workflow()
        elif self.o_args.task == "delete":
            self.delete()

    @staticmethod
    def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
        """Parse les paramètres utilisateurs.

        Args:
            args (Optional[Sequence[str]], optional): paramètres à parser, si None sys.argv utilisé.

        Returns:
            argparse.Namespace: paramètres
        """
        # Parsing des paramètres
        o_parser = argparse.ArgumentParser(prog="sdk_entrepot_gpf", description="Exécutable pour interagir avec l'API Entrepôt de la Géoplateforme.")
        o_parser.add_argument("--ini", dest="config", default="config.ini", help="Chemin vers le fichier de config à utiliser (config.ini par défaut)")
        o_parser.add_argument("--version", action="version", version=f"%(prog)s v{sdk_entrepot_gpf.__version__}")
        o_parser.add_argument("--debug", dest="debug", required=False, default=False, action="store_true", help="Passe l'appli en mode debug (plus de messages affichés)")
        o_parser.add_argument("--datastore", "-d", dest="datastore", required=False, default=None, help="Identifiant du datastore à utiliser")
        o_sub_parsers = o_parser.add_subparsers(dest="task", metavar="TASK", required=True, help="Tâche à effectuer")

        # Parser pour auth
        o_sub_parser = o_sub_parsers.add_parser("auth", help="Authentification")
        o_sub_parser.add_argument("--show", type=str, choices=["token", "header"], default=None, help="Donnée à renvoyer")

        # Parser pour me
        o_sub_parser = o_sub_parsers.add_parser("me", help="Mes informations")

        # Parser pour config
        o_sub_parser = o_sub_parsers.add_parser("config", help="Configuration")
        o_sub_parser.add_argument("--file", "-f", type=str, default=None, help="Chemin du fichier où sauvegarder la configuration (si null, la configuration est affichée)")
        o_sub_parser.add_argument("--section", "-s", type=str, default=None, help="Se limiter à une section")
        o_sub_parser.add_argument("--option", "-o", type=str, default=None, help="Se limiter à une option (la section doit être renseignée)")

        # Parser pour upload
        s_epilog_upload = """Trois types de lancement :
        * création / mise à jour de livraison : `--file FILE [--behavior BEHAVIOR]`
        * détail d'une livraison, optionnel ouverture ou fermeture : `--id ID [--open | --close]`
        * liste des livraisons, optionnel filtre sur l'info et tags : `[--infos INFOS] [--tags TAGS]`
        """
        o_sub_parser = o_sub_parsers.add_parser("upload", help="Livraisons", epilog=s_epilog_upload, formatter_class=argparse.RawTextHelpFormatter)
        o_sub_parser.add_argument("--file", "-f", type=str, default=None, help="Chemin vers le fichier descriptor dont on veut effectuer la livraison)")
        o_sub_parser.add_argument("--behavior", "-b", choices=UploadAction.BEHAVIORS, default=None, help="Action à effectuer si la livraison existe déjà (uniquement avec -f)")
        o_sub_parser.add_argument("--id", type=str, default=None, help="Affiche la livraison demandée")
        o_exclusive = o_sub_parser.add_mutually_exclusive_group()
        o_exclusive.add_argument("--open", action="store_true", default=False, help="Rouvrir une livraison fermée (uniquement avec --id)")
        o_exclusive.add_argument("--close", action="store_true", default=False, help="Fermer une livraison ouverte (uniquement avec --id)")
        o_sub_parser.add_argument("--infos", "-i", type=str, default=None, help="Filtrer les livraisons selon les infos")
        o_sub_parser.add_argument("--tags", "-t", type=str, default=None, help="Filtrer les livraisons selon les tags")

        # Parser pour dataset
        o_sub_parser = o_sub_parsers.add_parser("dataset", help="Jeux de données")
        o_sub_parser.add_argument("--name", "-n", type=str, default=None, help="Nom du dataset à extraire")
        o_sub_parser.add_argument("--folder", "-f", type=str, default=None, help="Dossier où enregistrer le dataset")

        # Parser pour workflow
        s_epilog_workflow = """Quatre types de lancement :
        * liste des exemples de workflow disponibles : `` (aucun arguments)
        * Récupération d'un workflow exemple : `--name NAME`
        * Vérification de la structure du ficher workflow et affichage des étapes : `--file FILE`
        * Lancement l'une étape d'un workflow: `--file FILE --step STEP [--behavior BEHAVIOR]`
        """
        o_sub_parser = o_sub_parsers.add_parser("workflow", help="Workflow", epilog=s_epilog_workflow, formatter_class=argparse.RawTextHelpFormatter)
        o_sub_parser.add_argument("--file", "-f", type=str, default=None, help="Chemin du fichier à utiliser OU chemin où extraire le dataset")
        o_sub_parser.add_argument("--name", "-n", type=str, default=None, help="Nom du workflow à extraire")
        o_sub_parser.add_argument("--step", "-s", type=str, default=None, help="Étape du workflow à lancer")
        o_sub_parser.add_argument("--behavior", "-b", type=str, default=None, help="Action à effectuer si l'exécution de traitement existe déjà")
        o_sub_parser.add_argument("--tag", "-t", type=str, nargs=2, action="append", metavar=("Clef", "Valeur"), default=[], help="Tag à ajouter aux actions (plusieurs tags possible)")
        o_sub_parser.add_argument(
            "--comment",
            "-c",
            type=str,
            default=[],
            action="append",
            metavar='"Le commentaire"',
            help="Commentaire à ajouter aux actions (plusieurs commentaires possible, mettre le commentaire entre guillemets)",
        )

        # Parser pour delete
        o_sub_parser = o_sub_parsers.add_parser("delete", help="Delete")
        o_sub_parser.add_argument("--type", choices=Main.DELETABLE_TYPES, required=True, help="Type de l'entité à supprimer")
        o_sub_parser.add_argument("--id", type=str, required=True, help="Identifiant de l'entité à supprimer")
        o_sub_parser.add_argument("--cascade", action="store_true", help="Action à effectuer si l'exécution de traitement existe déjà")
        o_sub_parser.add_argument("--force", action="store_true", help="Mode forcé, les suppressions sont faites sans aucune interaction")

        return o_parser.parse_args(args)

    def __datastore(self) -> Optional[str]:
        """Fonction pour récupérer l'id du datastore indiqué si l'utilisateur a indiqué son nom.

        Returns:
            Optional[str]: id du datastore
        """
        # On regarde si le datastore est donné
        if self.o_args.datastore:
            return Datastore.get_id(self.o_args.datastore)
        # Sinon en renvoi None
        return None

    def auth(self) -> None:
        """Authentifie l'utilisateur et retourne les informations de connexion demandées.
        Si aucune information est demandée, confirme juste la bonne authentification.
        """
        s_token = Authentifier().get_access_token_string()
        if self.o_args.show == "token":
            print(s_token)
        elif self.o_args.show == "header":
            print(Authentifier().get_http_header())
        else:
            print("Authentification réussie.")

    def me_(self) -> None:
        """Affiche les informations de l'utilisateur connecté."""
        # Requêtage
        o_response = ApiRequester().route_request("me_get")
        # Formatage
        d_info = o_response.json()
        # Info de base
        l_texts = [
            "Vos informations :",
            f"  * email : {d_info['email']}",
            f"  * nom : {d_info.get('first_name')} {d_info.get('last_name')}",
            f"  * votre id : {d_info['_id']}",
        ]
        # Gestion des communautés
        if not d_info["communities_member"]:
            l_texts.append("Vous n'êtes membre d'aucune communauté.")
        else:
            l_cm = d_info["communities_member"]
            l_texts.append("")
            l_texts.append(f"Vous êtes membre de {len(l_cm)} communauté(s) :")
            for d_cm in l_cm:
                d_community = d_cm["community"]
                if isinstance(d_cm["rights"], dict):
                    l_rights = [k.replace("_rights", "") for k, v in d_cm["rights"].items() if v is True]
                else:
                    l_rights = d_cm["rights"]
                s_rights = ", ".join(l_rights)
                l_texts.append("")
                l_texts.append(f"  * communauté « {d_community['name']} » :")
                l_texts.append(f"      - id de la communauté : {d_community['_id']}")
                l_texts.append(f"      - id du datastore : {d_community.get('datastore')}")
                l_texts.append(f"      - nom technique : {d_community['technical_name']}")
                l_texts.append(f"      - droits : {s_rights}")
        # Affichage
        print("\n".join(l_texts))

    def config(self) -> None:
        """Fonction pour afficher ou sauvegarder la configuration :
        * si une section (voire une option) est demandée, on affiche ce qui est demandé
        * sinon :
            * si un fichier est précisé on y enregistre toute la config
            * sinon on affiche toute la config
        """
        o_parser = Config().get_parser()

        # Juste une section ou toute la config ?
        if self.o_args.section is not None:
            # Juste une section
            if self.o_args.option is not None:
                # On nous demande une section.option
                try:
                    print(o_parser.get(self.o_args.section, self.o_args.option))
                except configparser.NoSectionError as e_no_section_error:
                    raise GpfSdkError(f"La section '{self.o_args.section}' n'existe pas dans la configuration.") from e_no_section_error
                except configparser.NoOptionError as e_no_option_error:
                    raise GpfSdkError(f"L'option '{self.o_args.option}' n'existe pas dans la section '{self.o_args.section}'.") from e_no_option_error
            else:
                # On nous demande toute une section
                try:
                    # On crée un nouveau parser
                    o_parser2 = configparser.ConfigParser()
                    # On y met la section demandée
                    o_parser2[self.o_args.section] = o_parser[self.o_args.section]
                    # On affiche tout ça
                    with io.StringIO() as o_string_io:
                        o_parser2.write(o_string_io)
                        o_string_io.seek(0)
                        print(o_string_io.read()[:-1])
                except KeyError as e_key_error:
                    raise GpfSdkError(f"La section '{self.o_args.section}' n'existe pas dans la configuration.") from e_key_error
        else:
            # On nous demande toute la config
            if self.o_args.file is not None:
                # On sauvegarde la donnée
                try:
                    with open(self.o_args.file, mode="w", encoding="UTF-8") as f_ini:
                        o_parser.write(f_ini)
                except PermissionError as e_permission_error:
                    raise GpfSdkError(f"Impossible d'écrire le fichier {self.o_args.file} : non autorisé") from e_permission_error
            else:
                # Sinon on l'affiche
                with io.StringIO() as o_string_io:
                    o_parser.write(o_string_io)
                    o_string_io.seek(0)
                    print(o_string_io.read()[:-1])

    @staticmethod
    def __monitoring_upload(upload: Upload, message_ok: str, message_ko: str, callback: Optional[Callable[[str], None]] = None, ctrl_c_action: Optional[Callable[[], bool]] = None) -> bool:
        """Monitoring de l'upload et affichage état de sortie

        Args:
            upload (Upload): upload à monitorer
            message_ok (str): message si les vérifications sont ok
            message_ko (str): message si les vérifications sont en erreur
            callback (Optional[Callable[[str], None]], optional): fonction de callback à exécuter avec le message de suivi.
            ctrl_c_action (Optional[Callable[[], bool]], optional): gestion du ctrl-C
        Returns:
            bool: True si toutes les vérifications sont ok, sinon False
        """
        b_res = UploadAction.monitor_until_end(upload, callback, ctrl_c_action)
        if b_res:
            Config().om.info(message_ok.format(upload=upload), green_colored=True)
        else:
            Config().om.error(message_ko.format(upload=upload))
        return b_res

    @staticmethod
    def upload_from_descriptor_file(file: Union[Path, str], behavior: Optional[str] = None, datastore: Optional[str] = None) -> Dict[str, Any]:
        """réalisation des livraison décrite par le fichier

        Args:
            file (Union[Path, str]): chemin du ficher descripteur de livraison
            behavior (Optional[str]): comportement dans le cas où une livraison de même nom existe, comportment par défaut su None
            datastore (Optional[str]): datastore à utilisé, datastore par défaut si None

        Returns:
            Dict[str, Any]: dictionnaire avec le résultat des livraisons :
                "ok" : liste des livraisons sans problèmes,
                "upload_fail": dictionnaire nom livraison : erreur remonté lors de la livraison
                "check_fail": liste des livraisons dont les vérification ont échouée
        """
        o_dfu = DescriptorFileReader(Path(file))
        s_behavior = str(behavior).upper() if behavior is not None else None

        l_uploads: List[Upload] = []  # liste des uploads lancées
        d_upload_fail: Dict[str, Exception] = {}  # dictionnaire upload : erreur des uploads qui ont fail
        l_check_ko: List[Upload] = []  # liste des uploads dont les vérifications plantes

        # on fait toutes les livraisons
        Config().om.info(f"LIVRAISONS : ({len(o_dfu.datasets)})", green_colored=True)
        for o_dataset in o_dfu.datasets:
            s_nom = o_dataset.upload_infos["name"]
            Config().om.info(f"{Color.BLUE} * {s_nom}{Color.END}")
            try:
                o_ua = UploadAction(o_dataset, behavior=s_behavior)
                o_upload = o_ua.run(datastore)
                l_uploads.append(o_upload)
            except Exception as e:
                s_nom = o_dataset.upload_infos["name"]
                d_upload_fail[s_nom] = e
                Config().om.error(f"livraison {s_nom} : {e}")

        # vérification des livraisons
        Config().om.info("Fin des livraisons.", green_colored=True)
        Config().om.info("Suivi des vérifications :", green_colored=True)
        l_check_ko = []
        l_check_ok = []
        for o_upload in l_uploads:
            Config().om.info(f"{Color.BLUE} * {o_upload}{Color.END}")
            b_res = Main.__monitoring_upload(o_upload, "Livraison {upload} créée avec succès.", "Livraison {upload} créée en erreur !", print)
            if b_res:
                l_check_ok.append(o_upload)
            else:
                l_check_ko.append(o_upload)
        Config().om.info("Fin des vérifications.", green_colored=True)

        return {
            "ok": l_check_ok,
            "upload_fail": d_upload_fail,
            "check_fail": l_check_ko,
        }

    @staticmethod
    def open_upload(upload: Upload) -> None:
        """réouverture d'une livraison

        Args:
            upload (Upload): livraison à ouvrir

        Raises:
            GpfSdkError: impossible d'ouvrir la livraison
        """
        if upload.is_open():
            Config().om.warning(f"La livraison {upload} est déjà ouverte.")
            return
        if upload["status"] in [Upload.STATUS_CLOSED, Upload.STATUS_UNSTABLE]:
            upload.api_open()
            Config().om.info(f"La livraison {upload} viens d'être rouverte.", green_colored=True)
            return
        raise GpfSdkError(f"La livraison {upload} n'est pas dans un état permettant de d'ouvrir la livraison ({upload['status']}).")

    @staticmethod
    def close_upload(upload: Upload) -> None:
        """fermeture d'une livraison

        Args:
            upload (Upload): livraison à fermé

        Raises:
            GpfSdkError: impossible de fermer la livraison
        """
        # si ouverte : on ferme puis monitoring
        if upload.is_open():
            # fermeture de l'upload
            upload.api_close()
            Config().om.info(f"La livraison {upload} viens d'être Fermée.", green_colored=True)
            # monitoring des tests :
            Main.__monitoring_upload(upload, "Livraison {upload} fermée avec succès.", "Livraison {upload} fermée en erreur !", print)
            return
        # si STATUS_CHECKING : monitoring
        if upload["status"] == Upload.STATUS_CHECKING:
            Config().om.info(f"La livraison {upload} est fermé, les tests sont en cours.")
            Main.__monitoring_upload(upload, "Livraison {upload} fermée avec succès.", "Livraison {upload} fermée en erreur !", print)
            return
        # si ferme OK ou KO : warning
        if upload["status"] in [Upload.STATUS_CLOSED, Upload.STATUS_UNSTABLE]:
            Config().om.warning(f"La livraison {upload} est déjà fermée, status : {upload['status']}")
            return
        # autre : action impossible
        raise GpfSdkError(f"La livraison {upload} n'est pas dans un état permettant de fermer la livraison ({upload['status']}).")

    def upload(self) -> None:
        """Création/Gestion des Livraison (Upload).
        Si un fichier descriptor est précisé, on effectue la livraison.
        Si un id est précisé, on affiche la livraison.
        Sinon on liste les Livraisons avec éventuellement des filtres.
        """
        if self.o_args.file is not None:
            # on livre les données selon le ficher descripteur donné
            d_res = self.upload_from_descriptor_file(self.o_args.file, self.o_args.behavior, self.o_args.datastore)
            # Affichage du bilan
            Config().om.info("-" * 100)
            if d_res["upload_fail"] or d_res["check_fail"]:
                Config().om.info("RÉCAPITULATIF DES PROBLÈMES :", green_colored=True)
                if d_res["upload_fail"]:
                    Config().om.error(f"{len(d_res['upload_fail'])} livraisons échoués :\n" + "\n".join([f" * {s_nom} : {e_error}" for s_nom, e_error in d_res["upload_fail"].items()]))
                if d_res["check_fail"]:
                    Config().om.error(f"{len(d_res['check_fail'])} vérifications de livraisons échoués :\n" + "\n".join([f" * {o_upload}" for o_upload in d_res["check_fail"]]))
                Config().om.error(
                    f"BILAN : {len(d_res['ok'])} livraisons effectué sans erreur, {len(d_res['upload_fail'])} livraisons échouées, {len(d_res['check_fail'])} vérifications de livraisons échouées"
                )
                sys.exit(1)
            else:
                Config().om.info(f"BILAN : les {len(d_res['ok'])} livraisons se sont bien passées", green_colored=True)

        elif self.o_args.id is not None:
            o_upload = Upload.api_get(self.o_args.id, datastore=self.datastore)
            if self.o_args.open:
                self.open_upload(o_upload)
            elif self.o_args.close:
                self.close_upload(o_upload)
            else:
                # affichage
                Config().om.info(o_upload.to_json(indent=3))
        else:
            d_infos_filter = StoreEntity.filter_dict_from_str(self.o_args.infos)
            d_tags_filter = StoreEntity.filter_dict_from_str(self.o_args.tags)
            l_uploads = Upload.api_list(infos_filter=d_infos_filter, tags_filter=d_tags_filter, datastore=self.datastore)
            for o_upload in l_uploads:
                Config().om.info(f"{o_upload}")

    def dataset(self) -> None:
        """Liste les jeux de données d'exemple proposés et, si demandé par l'utilisateur, en export un."""
        p_root = Config.data_dir_path / "datasets"
        if self.o_args.name is not None:
            s_dataset = str(self.o_args.name)
            print(f"Exportation du jeu de donnée '{s_dataset}'...")
            p_from = p_root / s_dataset
            if p_from.exists():
                p_output = Path(self.o_args.folder) if self.o_args.folder is not None else Path(s_dataset)
                if p_output.exists():
                    p_output = p_output / s_dataset
                print(f"Chemin de sortie : {p_output}")
                # Copie du répertoire
                shutil.copytree(p_from, p_output)
                print("Exportation terminée.")
            else:
                raise GpfSdkError(f"Jeu de données '{s_dataset}' introuvable.")
        else:
            l_children: List[str] = []
            for p_child in p_root.iterdir():
                if p_child.is_dir():
                    l_children.append(p_child.name)
            print("Jeux de données disponibles :\n   * {}".format("\n   * ".join(l_children)))

    @staticmethod
    def ctrl_c_action() -> bool:
        """fonction callback pour la gestion du ctrl-C
        Renvoie un booléen d'arrêt de traitement. Si True, on doit arrêter le traitement.
        """
        # issues/9 :
        # sortie => sortie du monitoring, ne pas arrêter le traitement
        # stopper l’exécution de traitement => stopper le traitement (et donc le monitoring) [par défaut] (raise une erreur d'interruption volontaire)
        # ignorer / "erreur de manipulation" => reprendre le suivi
        s_reponse = "rien"
        while s_reponse not in ["a", "s", "c", ""]:
            Config().om.info(
                "Vous avez taper ctrl-C. Que souhaitez-vous faire ?\n\
                                \t* 'a' : pour sortir et <Arrêter> le traitement [par défaut]\n\
                                \t* 's' : pour sortir <Sans arrêter> le traitement\n\
                                \t* 'c' : pour annuler et <Continuer> le traitement"
            )
            s_reponse = input().lower()

        if s_reponse == "s":
            Config().om.info("\t 's' : sortir <Sans arrêter> le traitement")
            sys.exit(0)

        if s_reponse == "c":
            Config().om.info("\t 'c' : annuler et <Continuer> le traitement")
            return False

        # on arrête le traitement
        Config().om.info("\t 'a' : sortir et <Arrêter> le traitement [par défaut]")
        return True

    def workflow(self) -> None:
        """Vérifie ou exécute un workflow."""
        p_root = Config.data_dir_path / "workflows"
        # Si demandé, on exporte un workflow d'exemple
        if self.o_args.name is not None:
            s_workflow = str(self.o_args.name)
            print(f"Exportation du workflow '{s_workflow}'...")
            p_from = p_root / s_workflow
            if p_from.exists():
                p_output = Path(self.o_args.file) if self.o_args.file is not None else Path(s_workflow)
                if p_output.exists() and p_output.is_dir():
                    p_output = p_output / s_workflow
                print(f"Chemin de sortie : {p_output}")
                # Copie du répertoire
                shutil.copyfile(p_from, p_output)
                print("Exportation terminée.")
            else:
                raise GpfSdkError(f"Workflow '{s_workflow}' introuvable.")
        elif self.o_args.file is not None:
            # Ouverture du fichier
            p_workflow = Path(self.o_args.file).absolute()
            Config().om.info(f"Ouverture du workflow {p_workflow}...")
            o_workflow = Workflow(p_workflow.stem, JsonHelper.load(p_workflow))
            # Y'a-t-il une étape d'indiquée
            if self.o_args.step is None:
                # Si pas d'étape indiquée, on valide le workflow
                Config().om.info("Validation du workflow...")
                l_errors = o_workflow.validate()
                if l_errors:
                    s_errors = "\n   * ".join(l_errors)
                    Config().om.error(f"{len(l_errors)} erreurs ont été trouvées dans le workflow.")
                    Config().om.info(f"Liste des erreurs :\n   * {s_errors}")
                    raise GpfSdkError("Workflow invalide.")
                Config().om.info("Le workflow est valide.", green_colored=True)

                # Affichage des étapes disponibles et des parents
                Config().om.info("Liste des étapes disponibles et de leurs parents :", green_colored=True)
                l_steps = o_workflow.get_all_steps()
                for s_step in l_steps:
                    Config().om.info(f"   * {s_step}")

            else:
                # Sinon, on définit des résolveurs
                GlobalResolver().add_resolver(StoreEntityResolver("store_entity"))
                GlobalResolver().add_resolver(UserResolver("user"))
                # le comportement
                s_behavior = str(self.o_args.behavior).upper() if self.o_args.behavior is not None else None
                # on reset l'afficheur de log
                PrintLogHelper.reset()

                # et on lance l'étape en précisant l'afficheur de log et le comportement
                def callback_run_step(processing_execution: ProcessingExecution) -> None:
                    """fonction callback pour l'affichage des logs lors du suivi d'un traitement

                    Args:
                        processing_execution (ProcessingExecution): processing exécution en cours
                    """
                    try:
                        PrintLogHelper.print(processing_execution.api_logs())
                    except Exception:
                        PrintLogHelper.print("Logs indisponibles pour le moment...")

                # on lance le monitoring de l'étape en précisant la gestion du ctrl-C
                d_tags = {l_el[0]: l_el[1] for l_el in self.o_args.tag}
                o_workflow.run_step(self.o_args.step, callback_run_step, self.ctrl_c_action, behavior=s_behavior, datastore=self.datastore, comments=self.o_args.comment, tags=d_tags)

        else:
            l_children: List[str] = []
            for p_child in p_root.iterdir():
                if p_child.is_file():
                    l_children.append(p_child.name)
            print("Jeux de données disponibles :\n   * {}".format("\n   * ".join(l_children)))

    def delete(self) -> None:
        """suppression d'une entité par son type et son id"""

        def question_before_delete(l_delete: List[StoreEntity]) -> List[StoreEntity]:
            Config().om.info("suppression de :")
            for o_entity in l_delete:
                Config().om.info(str(o_entity), green_colored=True)
            Config().om.info("Voulez-vous effectué la suppression ? (oui/NON)")
            s_rep = input()
            # si la réponse ne correspond pas à oui on sort
            if s_rep.lower() not in ["oui", "o", "yes", "y"]:
                Config().om.info("La suppression est annulée.")
                return []
            return l_delete

        def print_before_delete(l_delete: List[StoreEntity]) -> List[StoreEntity]:
            Config().om.info("suppression de :")
            for o_entity in l_delete:
                Config().om.info(str(o_entity), green_colored=True)
            return l_delete

        if self.o_args.type in Main.DELETABLE_TYPES:
            # récupération de l'entité de base
            o_entity = store.TYPE__ENTITY[self.o_args.type].api_get(self.o_args.id)
        else:
            raise GpfSdkError(f"Type {self.o_args.type} non reconnu. Types valides : {', '.join(Main.DELETABLE_TYPES)}")

        # choix de la fonction exécuté avant la suppression
        ## force : juste affichage
        ## sinon : question d'acceptation de la suppression
        f_delete = print_before_delete if self.o_args.force else question_before_delete

        # suppression
        if self.o_args.cascade:
            o_entity.delete_cascade(f_delete)
        else:
            StoreEntity.delete_liste_entities([o_entity], f_delete)


if __name__ == "__main__":
    try:
        Main()
        sys.exit(0)
    except GpfSdkError as e_gpf_api_error:
        Config().om.critical(e_gpf_api_error.message)
    except ConflictError:
        # gestion "globale" des ConflictError (ConfigurationAction et OfferingAction
        # possèdent chacune leur propre gestion)
        Config().om.critical("La requête envoyée à l'Entrepôt génère un conflit. N'avez-vous pas déjà effectué l'action que vous essayez de faire ?")
    except Exception as e_exception:
        Config().om.critical("Erreur non spécifiée :")
        Config().om.error(traceback.format_exc())
        Config().om.critical("Erreur non spécifiée.")
    sys.exit(1)
