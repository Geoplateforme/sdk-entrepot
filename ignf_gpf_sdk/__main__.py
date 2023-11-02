"""SDK Python pour simplifier l'utilisation de l'API Entrepôt Géoplateforme."""

import configparser
import io
import sys
import argparse
import time
import traceback
from pathlib import Path
from typing import Callable, List, Optional, Sequence
import shutil

import ignf_gpf_sdk
from ignf_gpf_sdk.Errors import GpfSdkError
from ignf_gpf_sdk.auth.Authentifier import Authentifier
from ignf_gpf_sdk.helper.JsonHelper import JsonHelper
from ignf_gpf_sdk.helper.PrintLogHelper import PrintLogHelper
from ignf_gpf_sdk.io.Errors import ConflictError
from ignf_gpf_sdk.io.ApiRequester import ApiRequester
from ignf_gpf_sdk.workflow.Workflow import Workflow
from ignf_gpf_sdk.workflow.resolver.GlobalResolver import GlobalResolver
from ignf_gpf_sdk.workflow.resolver.StoreEntityResolver import StoreEntityResolver
from ignf_gpf_sdk.workflow.action.UploadAction import UploadAction
from ignf_gpf_sdk.io.Config import Config
from ignf_gpf_sdk.io.DescriptorFileReader import DescriptorFileReader
from ignf_gpf_sdk.store.Offering import Offering
from ignf_gpf_sdk.store.Configuration import Configuration
from ignf_gpf_sdk.store.StoredData import StoredData
from ignf_gpf_sdk.store.Upload import Upload
from ignf_gpf_sdk.store.StoreEntity import StoreEntity
from ignf_gpf_sdk.store.ProcessingExecution import ProcessingExecution
from ignf_gpf_sdk.store.Datastore import Datastore
from ignf_gpf_sdk.workflow.resolver.UserResolver import UserResolver


class Main:
    """Classe d'entrée pour utiliser la lib comme binaire."""

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
        o_parser = argparse.ArgumentParser(prog="ignf_gpf_sdk", description="Exécutable pour interagir avec l'API Entrepôt de la Géoplateforme.")
        o_parser.add_argument("--ini", dest="config", default="config.ini", help="Chemin vers le fichier de config à utiliser (config.ini par défaut)")
        o_parser.add_argument("--version", action="version", version=f"%(prog)s v{ignf_gpf_sdk.__version__}")
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
        o_sub_parser.add_argument("--option", "-o", type=str, default=None, help="Se limiter à une option (section doit être renseignée)")

        # Parser pour upload
        s_epilog_upload = """Trois types de lancement :
        * création / mise à jour de livraison : `--file FILE [--behavior BEHAVIOR]`
        * détail d'une livraison, optionnel ouverture ou fermeture : `--id ID [--open | --close]`
        * liste des livraisons, optionnel filtre sur l'info et tags : `[--infos INFOS] [--tags TAGS]`
        """
        o_sub_parser = o_sub_parsers.add_parser("upload", help="Livraisons", epilog=s_epilog_upload, formatter_class=argparse.RawTextHelpFormatter)
        o_sub_parser.add_argument("--file", "-f", type=str, default=None, help="Chemin vers le fichier descriptor dont on veut effectuer la livraison)")
        o_sub_parser.add_argument("--behavior", "-b", type=str, default=None, help="Action à effectuer si la livraison existe déjà (uniquement avec -f)")
        o_sub_parser.add_argument("--id", type=str, default=None, help="Affiche la livraison demandée")
        o_exclusive = o_sub_parser.add_mutually_exclusive_group()
        o_exclusive.add_argument("--open", action="store_true", default=False, help="Rouvrir une livraison fermée (uniquement avec --id)")
        o_exclusive.add_argument("--close", action="store_true", default=False, help="Fermer une livraison ouverte (uniquement avec --id)")
        o_sub_parser.add_argument("--infos", "-i", type=str, default=None, help="Filter les livraisons selon les infos")
        o_sub_parser.add_argument("--tags", "-t", type=str, default=None, help="Filter les livraisons selon les tags")

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

        # Parser pour delete
        o_sub_parser = o_sub_parsers.add_parser("delete", help="Delete")
        o_sub_parser.add_argument("--type", choices=["livraison", "stored_data", "configuration", "offre"], required=True, help="Type de l'entité à supprimé")
        o_sub_parser.add_argument("--id", type=str, required=True, help="identifiant de l'entité à supprimé")
        o_sub_parser.add_argument("--cascade", action="store_true", help="Action à effectuer si l'exécution de traitement existe déjà")
        o_sub_parser.add_argument("--force", action="store_true", help="Mode forcée, les suppressions sont faites sans aucune interaction")

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
        """monitoring de l'upload et affichage état de sortie

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

    def upload(self) -> None:
        """Création/Gestion des Livraison (Upload).
        Si un fichier descriptor est précisé, on effectue la livraison.
        Si un id est précisé, on affiche la livraison.
        Sinon on liste les Livraisons avec éventuellement des filtres.
        """
        if self.o_args.file is not None:
            p_file = Path(self.o_args.file)
            o_dfu = DescriptorFileReader(p_file)
            for o_dataset in o_dfu.datasets:
                s_behavior = str(self.o_args.behavior).upper() if self.o_args.behavior is not None else None
                o_ua = UploadAction(o_dataset, behavior=s_behavior)
                o_upload = o_ua.run(self.o_args.datastore)
                self.__monitoring_upload(o_upload, "Livraison {upload} créée avec succès.", "Livraison {upload} créée en erreur !", print)
        elif self.o_args.id is not None:
            o_upload = Upload.api_get(self.o_args.id, datastore=self.datastore)
            if self.o_args.open:
                if o_upload.is_open():
                    Config().om.warning(f"La livraison {o_upload} est déjà ouverte.")
                    return
                if o_upload["status"] in [Upload.STATUS_CLOSED, Upload.STATUS_UNSTABLE]:
                    o_upload.api_open()
                    Config().om.info(f"La livraison {o_upload} viens d'être rouverte.", green_colored=True)
                    return
                raise GpfSdkError(f"La livraison {o_upload} n'est pas dans un état permettant de d'ouvrir la livraison ({o_upload['status']}).")
            if self.o_args.close:
                # si ouverte : on ferme puis monitoring
                if o_upload.is_open():
                    # fermeture de l'upload
                    o_upload.api_close()
                    Config().om.info(f"La livraison {o_upload} viens d'être Fermée.", green_colored=True)
                    # monitoring des tests :
                    self.__monitoring_upload(o_upload, "Livraison {upload} fermée avec succès.", "Livraison {o_upload} fermée en erreur !", print)
                    return
                # si STATUS_CHECKING : monitoring
                if o_upload["status"] == Upload.STATUS_CHECKING:
                    Config().om.info(f"La livraison {o_upload} est fermé, les tests sont en cours.")
                    self.__monitoring_upload(o_upload, "Livraison {upload} fermée avec succès.", "Livraison {o_upload} fermée en erreur !", print)
                    return
                # si ferme OK ou KO : warning
                if o_upload["status"] in [Upload.STATUS_CLOSED, Upload.STATUS_UNSTABLE]:
                    Config().om.warning(f"La livraison {o_upload} est déjà fermée, status : {o_upload['status']}")
                    return
                # autre : action impossible
                raise GpfSdkError(f"La livraison {o_upload} n'est pas dans un état permettant de fermer la livraison ({o_upload['status']}).")

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
                o_workflow.run_step(self.o_args.step, callback_run_step, self.ctrl_c_action, behavior=s_behavior, datastore=self.datastore)
        else:
            l_children: List[str] = []
            for p_child in p_root.iterdir():
                if p_child.is_file():
                    l_children.append(p_child.name)
            print("Jeux de données disponibles :\n   * {}".format("\n   * ".join(l_children)))

    def delete(self) -> None:
        """suppression d'une entité par son type et son id"""
        l_entities: List[StoreEntity] = []
        if self.o_args.type == "livraison":
            l_entities.append(Upload.api_get(self.o_args.id))
        elif self.o_args.type == "stored_data":
            o_stored_data = StoredData.api_get(self.o_args.id)
            if self.o_args.cascade:
                # liste des configurations
                l_configuration = Configuration.api_list({"stored_data": self.o_args.id})
                for o_configuration in l_configuration:
                    # pour chaque configuration on récupère les offerings
                    l_offering = o_configuration.api_list_offerings()
                    l_entities += l_offering
                    l_entities.append(o_configuration)
            l_entities.append(o_stored_data)
        elif self.o_args.type == "configuration":
            o_configuration = Configuration.api_get(self.o_args.id)
            if self.o_args.cascade:
                l_offering = o_configuration.api_list_offerings()
                l_entities += l_offering
            l_entities.append(o_configuration)
        elif self.o_args.type == "offre":
            l_entities.append(Offering.api_get(self.o_args.id))

        # affichage élément supprimés
        Config().om.info("Suppression de :")
        for o_entity in l_entities:
            Config().om.info(str(o_entity), green_colored=True)

        # demande validation si non forcée
        if not self.o_args.force:
            Config().om.info("Voulez-vous effectué la suppression ? (oui/NON)")
            s_rep = input()
            # si la réponse ne correspond pas à oui on sort
            if s_rep.lower() not in ["oui", "o", "yes", "y"]:
                Config().om.info("La suppression est annulée.")
                return
        # suppression
        for o_entity in l_entities:
            o_entity.api_delete()
            time.sleep(1)
        Config().om.info("Suppression effectué.", green_colored=True)


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
