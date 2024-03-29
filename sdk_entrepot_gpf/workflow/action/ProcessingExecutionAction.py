import time
from typing import Any, Callable, Dict, Optional, Union

from sdk_entrepot_gpf.Errors import GpfSdkError
from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.store.ProcessingExecution import ProcessingExecution
from sdk_entrepot_gpf.store.StoredData import StoredData
from sdk_entrepot_gpf.workflow.Errors import StepActionError
from sdk_entrepot_gpf.workflow.action.ActionAbstract import ActionAbstract
from sdk_entrepot_gpf.store.Upload import Upload


class ProcessingExecutionAction(ActionAbstract):
    """Classe dédiée à la création des ProcessingExecution.

    Attributes:
        __workflow_context (str): nom du context du workflow
        __definition_dict (Dict[str, Any]): définition de l'action
        __parent_action (Optional["Action"]): action parente
        __processing_execution (Optional[ProcessingExecution]): représentation Python de l'exécution de traitement créée
        __Upload (Optional[Upload]): représentation Python de la livraison en sortie (null si donnée stockée en sortie)
        __StoredData (Optional[StoredData]): représentation Python de la donnée stockée en sortie (null si livraison en sortie)
    """

    # status possibles d'une ProcessingExecution (status délivrés par l'api)
    # STATUS_CREATED
    # STATUS_ABORTED STATUS_SUCCESS STATUS_FAILURE

    # status possibles d'une Stored data (status délivrés par l'api)
    # STATUS_CREATED
    # STATUS_UNSTABLE
    # STATUS_GENERATING STATUS_MODIFYING
    # STATUS_GENERATED

    def __init__(self, workflow_context: str, definition_dict: Dict[str, Any], parent_action: Optional["ActionAbstract"] = None, behavior: Optional[str] = None) -> None:
        super().__init__(workflow_context, definition_dict, parent_action)
        # l'exécution du traitement
        self.__processing_execution: Optional[ProcessingExecution] = None
        # les données en sortie
        self.__upload: Optional[Upload] = None
        self.__stored_data: Optional[StoredData] = None
        # comportement (écrit dans la ligne de commande par l'utilisateur), sinon celui par défaut (dans la config) qui vaut STOP
        self.__behavior: str = behavior if behavior is not None else Config().get_str("processing_execution", "behavior_if_exists")

    def run(self, datastore: Optional[str] = None) -> None:
        Config().om.info("Création d'une exécution de traitement et complétion de l'entité en sortie...")
        # Création de l'exécution du traitement (attributs processing_execution et Upload/StoredData défini)
        self.__create_processing_execution(datastore)
        # Ajout des tags sur l'Upload ou la StoredData
        self.__add_tags()
        # Ajout des commentaires sur l'Upload ou la StoredData
        self.__add_comments()
        # Lancement du traitement
        self.__launch()
        # Affichage
        o_output_entity = self.__stored_data if self.__stored_data is not None else self.__upload
        Config().om.info(f"Exécution de traitement créée et lancée ({self.processing_execution}) et entité en sortie complétée ({o_output_entity}).")
        Config().om.info("Création d'une exécution de traitement et complétion de l'entité en sortie : terminé")

    def __create_processing_execution(self, datastore: Optional[str] = None) -> None:
        """Création du ProcessingExecution sur l'API à partir des paramètres de définition de l'action.
        Récupération des attributs processing_execution et Upload/StoredData.
        """
        d_info: Optional[Dict[str, Any]] = None

        # On regarde si cette Exécution de Traitement implique la création d'une nouvelle entité (Livraison ou Donnée Stockée)
        if self.output_new_entity:
            # TODO : gérer également les Livraisons
            # On vérifie si une Donnée Stockée équivalente à celle du dictionnaire de définition (champ name) existe déjà sur la gpf
            o_stored_data = self.find_stored_data(datastore)
            # Si on a trouvé une Donnée Stockée sur la gpf :
            if o_stored_data is not None:
                # Comportement d'arrêt du programme
                if self.__behavior == self.BEHAVIOR_STOP:
                    raise GpfSdkError(f"Impossible de créer l’exécution de traitement, une donnée stockée en sortie équivalente {o_stored_data} existe déjà.")
                # Comportement de suppression des entités détectées
                if self.__behavior == self.BEHAVIOR_DELETE:
                    Config().om.warning(f"Une donnée stockée équivalente à {o_stored_data} va être supprimée puis recréée.")
                    # Suppression de la donnée stockée
                    o_stored_data.api_delete()
                    # on force à None pour que la création soit faite
                    self.__processing_execution = None
                # Comportement "on continue l'exécution"
                elif self.__behavior == self.BEHAVIOR_CONTINUE:
                    o_stored_data.api_update()
                    # on regarde si le résultat du traitement précédent est en échec
                    if o_stored_data["status"] == StoredData.STATUS_UNSTABLE:
                        raise GpfSdkError(f"Le traitement précédent a échoué sur la donnée stockée en sortie {o_stored_data}. Impossible de lancer le traitement demandé.")

                    # on est donc dans un des cas suivants :
                    # le processing_execution a été créé mais pas exécuté (StoredData.STATUS_CREATED)
                    # ou le processing execution est en cours d'exécution (StoredData.STATUS_GENERATING ou StoredData.STATUS_MODIFYING)
                    # ou le processing execution est terminé (StoredData.STATUS_GENERATED)
                    self.__stored_data = o_stored_data
                    l_proc_exec = ProcessingExecution.api_list({"output_stored_data": o_stored_data.id}, datastore=datastore)
                    if not l_proc_exec:
                        raise GpfSdkError(f"Impossible de trouver l'exécution de traitement liée à la donnée stockée {o_stored_data}")
                    # arbitrairement, on prend le premier de la liste
                    self.__processing_execution = l_proc_exec[0]
                    Config().om.info(f"La donnée stocké en sortie {o_stored_data} déjà existante, on reprend le traitement associé : {self.__processing_execution}.")
                    return
                # Comportement non reconnu
                else:
                    raise GpfSdkError(
                        f"Le comportement {self.__behavior} n'est pas reconnu ({self.BEHAVIOR_STOP}|{self.BEHAVIOR_DELETE}|{self.BEHAVIOR_CONTINUE}), l'exécution de traitement n'est pas possible."
                    )

        # A ce niveau là, si on a encore self.__processing_execution qui est None, c'est qu'on peut créer l'Exécution de Traitement sans problème
        if self.__processing_execution is None:
            # création de la ProcessingExecution
            self.__processing_execution = ProcessingExecution.api_create(self.definition_dict["body_parameters"], {"datastore": datastore})
            d_info = self.__processing_execution.get_store_properties()["output"]

        if d_info is None:
            Config().om.debug(self.__processing_execution.to_json(indent=4))
            raise GpfSdkError("Erreur à la création de l'exécution de traitement : impossible de récupérer l'entité en sortie.")

        # Récupération des entités de l'exécution de traitement
        if "upload" in d_info:
            # récupération de l'upload
            self.__upload = Upload.api_get(d_info["upload"]["_id"], datastore=datastore)
            return
        if "stored_data" in d_info:
            # récupération de la stored_data
            self.__stored_data = StoredData.api_get(d_info["stored_data"]["_id"], datastore=datastore)
            return
        raise StepActionError(f"Aucune correspondance pour {d_info.keys()}")

    def __add_tags(self) -> None:
        """Ajout des tags sur l'Upload ou la StoredData en sortie du ProcessingExecution."""
        if "tags" not in self.definition_dict or self.definition_dict["tags"] == {}:
            # cas on a pas de tag ou vide: on ne fait rien
            return
        # on ajoute les tags
        if self.upload is not None:
            Config().om.info(f"Livraison {self.upload['name']} : ajout des {len(self.definition_dict['tags'])} tags...")
            self.upload.api_add_tags(self.definition_dict["tags"])
            Config().om.info(f"Livraison {self.upload['name']} : les {len(self.definition_dict['tags'])} tags ont été ajoutés avec succès.")
        elif self.stored_data is not None:
            Config().om.info(f"Donnée stockée {self.stored_data['name']} : ajout des {len(self.definition_dict['tags'])} tags...")
            self.stored_data.api_add_tags(self.definition_dict["tags"])
            Config().om.info(f"Donnée stockée {self.stored_data['name']} : les {len(self.definition_dict['tags'])} tags ont été ajoutés avec succès.")
        else:
            # on a pas de stored_data ni de upload
            raise StepActionError("ni upload ni stored-data trouvé. Impossible d'ajouter les tags")

    def __add_comments(self) -> None:
        """Ajout des commentaires sur l'Upload ou la StoredData en sortie du ProcessingExecution."""
        if "comments" not in self.definition_dict:
            # cas on a pas de commentaires : on ne fait rien
            return
        # on ajoute les commentaires
        i_nb_ajout = 0
        if self.upload is not None:
            o_data: Union[StoredData, Upload] = self.upload
            s_type = "Livraison"
        elif self.stored_data is not None:
            o_data = self.stored_data
            s_type = "Donnée stockée"
        else:
            # on a pas de stored_data ni de upload
            raise StepActionError("ni upload ni stored-data trouvé. Impossible d'ajouter les commentaires")

        Config().om.info(f"{s_type} {o_data['name']} : ajout des {len(self.definition_dict['comments'])} commentaires...")
        l_actual_comments = [d_comment["text"] for d_comment in o_data.api_list_comments() if d_comment]
        for s_comment in self.definition_dict["comments"]:
            if s_comment not in l_actual_comments:
                o_data.api_add_comment({"text": s_comment})
                i_nb_ajout += 1
        Config().om.info(f"{s_type} {o_data['name']} : {i_nb_ajout} commentaires ont été ajoutés.")

    def __launch(self) -> None:
        """Lancement de la ProcessingExecution."""
        if self.processing_execution is None:
            raise StepActionError("Aucune exécution de traitement trouvée. Impossible de lancer le traitement")

        if self.processing_execution["status"] == ProcessingExecution.STATUS_CREATED:
            Config().om.info(f"Exécution de traitement {self.processing_execution['processing']['name']} : lancement...")
            self.processing_execution.api_launch()
            Config().om.info(f"Exécution de traitement {self.processing_execution['processing']['name']} : lancée avec succès.")
        elif self.__behavior == self.BEHAVIOR_CONTINUE:
            Config().om.info(f"Exécution de traitement {self.processing_execution['processing']['name']} : déjà lancée.")
        else:
            # processing_execution est déjà lancé ET le __behavior n'est pas en "continue", on ne devrait pas être ici :
            raise StepActionError("L'exécution de traitement est déjà lancée.")

    def find_stored_data(self, datastore: Optional[str] = None) -> Optional[StoredData]:
        """Fonction permettant de récupérer une Stored Data ressemblant à celle qui devrait être créée par
        l'exécution de traitement en fonction des filtres définis dans la Config.

        Returns:
            donnée stockée retrouvée
        """
        # Récupération des critères de filtre
        d_infos, d_tags = ActionAbstract.get_filters("processing_execution", self.definition_dict["body_parameters"]["output"]["stored_data"], self.definition_dict.get("tags", {}))
        # On peut maintenant filtrer les stored data selon ces critères
        l_stored_data = StoredData.api_list(infos_filter=d_infos, tags_filter=d_tags, datastore=datastore)
        # S'il y a un ou plusieurs stored data, on retourne le 1er :
        if l_stored_data:
            return l_stored_data[0]
        # sinon on retourne None
        return None

    def monitoring_until_end(self, callback: Optional[Callable[[ProcessingExecution], None]] = None, ctrl_c_action: Optional[Callable[[], bool]] = None) -> str:
        """Attend que la ProcessingExecution soit terminée (statut `SUCCESS`, `FAILURE` ou `ABORTED`) avant de rendre la main.

        La fonction callback indiquée est exécutée après **chaque vérification du statut** en lui passant en paramètre
        la processing execution (callback(self.processing_execution)).

        Si l'utilisateur stoppe le programme (par ctrl-C), le devenir de la ProcessingExecutionAction sera géré par la callback ctrl_c_action().

        Args:
            callback (Optional[Callable[[ProcessingExecution], None]], optional): fonction de callback à exécuter. Prend en argument le traitement (callback(processing-execution)).
            ctrl_c_action (Optional[Callable[[], bool]], optional): fonction de gestion du ctrl-C. Renvoie True si on doit stopper le traitement.

        Returns:
            str: statut final de l'exécution du traitement
        """

        def callback_not_null(o_pe: ProcessingExecution) -> None:
            """fonction pour éviter des if à chaque appel

            Args:
                o_pe (ProcessingExecution): traitement en cours
            """
            if callback is not None:
                callback(o_pe)

        # NOTE :  Ne pas utiliser self.__processing_execution mais self.processing_execution pour faciliter les tests
        i_nb_sec_between_check = Config().get_int("processing_execution", "nb_sec_between_check_updates")
        Config().om.info(f"Monitoring du traitement toutes les {i_nb_sec_between_check} secondes...")
        if self.processing_execution is None:
            raise StepActionError("Aucune processing-execution trouvée. Impossible de suivre le déroulement du traitement")

        self.processing_execution.api_update()
        s_status = self.processing_execution.get_store_properties()["status"]
        while s_status not in [ProcessingExecution.STATUS_ABORTED, ProcessingExecution.STATUS_SUCCESS, ProcessingExecution.STATUS_FAILURE]:
            try:
                # appel de la fonction affichant les logs
                callback_not_null(self.processing_execution)

                # On attend le temps demandé
                time.sleep(i_nb_sec_between_check)

                # On met à jour __processing_execution + valeur status
                self.processing_execution.api_update()
                s_status = self.processing_execution.get_store_properties()["status"]

            except KeyboardInterrupt:
                # on appelle la callback de gestion du ctrl-C
                if ctrl_c_action is None or ctrl_c_action():
                    # on doit arrêter le traitement (maj + action spécifique selon le statut)

                    # mise à jour du traitement
                    self.processing_execution.api_update()

                    # si le traitement est déjà dans un statut terminé, on ne fait rien => transmission de l'interruption
                    s_status = self.processing_execution.get_store_properties()["status"]

                    # si le traitement est terminé, on fait un dernier affichage :
                    if s_status in [ProcessingExecution.STATUS_ABORTED, ProcessingExecution.STATUS_SUCCESS, ProcessingExecution.STATUS_FAILURE]:
                        callback_not_null(self.processing_execution)
                        Config().om.warning("traitement déjà terminé.")
                        raise

                    # arrêt du traitement
                    Config().om.warning("Ctrl+C : traitement en cours d’interruption, veuillez attendre...")
                    self.processing_execution.api_abort()
                    # attente que le traitement passe dans un statut terminé
                    self.processing_execution.api_update()
                    s_status = self.processing_execution.get_store_properties()["status"]
                    while s_status not in [ProcessingExecution.STATUS_ABORTED, ProcessingExecution.STATUS_SUCCESS, ProcessingExecution.STATUS_FAILURE]:
                        # On attend 2s
                        time.sleep(2)
                        # On met à jour __processing_execution + valeur status
                        self.processing_execution.api_update()
                        s_status = self.processing_execution.get_store_properties()["status"]
                    # traitement terminé. On fait un dernier affichage :
                    callback_not_null(self.processing_execution)

                    # si statut Aborted :
                    # suppression de l'upload ou de la stored data en sortie
                    if s_status == ProcessingExecution.STATUS_ABORTED and self.output_new_entity:
                        if self.upload is not None:
                            Config().om.warning("Suppression de l'upload en cours de remplissage suite à l’interruption du programme")
                            self.upload.api_delete()
                        elif self.stored_data is not None:
                            Config().om.warning("Suppression de la stored-data en cours de remplissage suite à l'interruption du programme")
                            self.stored_data.api_delete()
                    # enfin, transmission de l'interruption
                    raise

        # Si on est sorti du while c'est que la processing execution est terminée
        ## dernier affichage
        callback_not_null(self.processing_execution)
        ## on return le status de fin
        return str(s_status)

    @property
    def processing_execution(self) -> Optional[ProcessingExecution]:
        return self.__processing_execution

    @property
    def upload(self) -> Optional[Upload]:
        return self.__upload

    @property
    def stored_data(self) -> Optional[StoredData]:
        return self.__stored_data

    @property
    def output_new_entity(self) -> bool:
        """Indique s'il y aura création d'une nouvelle entité par rapport au paramètre de création de l'exécution de traitement
        (la clé "name" et non la clé "_id" est présente dans le paramètre "output" du corps de requête).
        """
        d_output = self.definition_dict["body_parameters"]["output"]
        if "upload" in d_output:
            d_el = self.definition_dict["body_parameters"]["output"]["upload"]
        elif "stored_data" in d_output:
            d_el = self.definition_dict["body_parameters"]["output"]["stored_data"]
        else:
            return False
        return "name" in d_el

    ##############################################################
    # Fonctions de représentation
    ##############################################################
    def __str__(self) -> str:
        # Affichage à destination d'un utilisateur.
        # On affiche l'id et le nom si possible.

        # Liste pour stocker les infos à afficher
        l_infos = []
        # Ajout de l'id
        l_infos.append(f"workflow={self.workflow_context}")
        if self.processing_execution:
            l_infos.append(f"processing_execution={self.processing_execution.id}")
        return f"{self.__class__.__name__}({', '.join(l_infos)})"
