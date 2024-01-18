import time
from typing import Any, Dict, Optional

from sdk_entrepot_gpf.Errors import GpfSdkError
from sdk_entrepot_gpf.io.Errors import NotFoundError
from sdk_entrepot_gpf.store.Offering import Offering
from sdk_entrepot_gpf.workflow.Errors import StepActionError
from sdk_entrepot_gpf.workflow.action.ActionAbstract import ActionAbstract
from sdk_entrepot_gpf.io.Config import Config


class SynchronizeOfferingAction(ActionAbstract):
    """Classe dédiée à la création des Offering.

    Attributes:
        __workflow_context (str): nom du contexte du workflow
        __definition_dict (Dict[str, Any]): définition de l'action
        __parent_action (Optional["Action"]): action parente
        __offering (Optional[Offering]): représentation Python de la Offering créée
    """

    def __init__(self, workflow_context: str, definition_dict: Dict[str, Any], parent_action: Optional["ActionAbstract"] = None) -> None:
        super().__init__(workflow_context, definition_dict, parent_action)
        # Autres attributs
        self.__offering: Optional[Offering] = None

    def run(self, datastore: Optional[str] = None) -> None:
        Config().om.info("Synchronisation d'une offre...")
        # récupération de l'offre
        try:
            self.__offering = Offering.api_get(self.definition_dict["url_parameters"]["offering"], datastore)
        except NotFoundError as e:
            # gestion du 404 not found
            raise GpfSdkError(f"Impossible de trouver l'offre : {self.definition_dict['url_parameters']['offering']}.") from e

        # lancement de la mise à jour de l'offering
        self.offering.api_synchronize()
        # Affichage
        o_offering = self.offering

        # Récupération des liens
        if len(o_offering["urls"]) > 0 and isinstance(o_offering["urls"][0], dict):
            # si les url sont récupérées sous forme de dict on affiche l'url uniquement
            s_urls = "\n   - ".join([d_url["url"] for d_url in o_offering["urls"]])
        else:
            # si les url sont récupérées sous forme de liste
            s_urls = "\n   - ".join(o_offering["urls"])
        Config().om.info(f"Offre synchroniser : {o_offering}\n   - {s_urls}", green_colored=True)
        # vérification du status.
        Config().om.info("vérification du statut ...")
        while True:
            o_offering.api_update()
            s_status = o_offering["status"]
            if s_status == Offering.STATUS_PUBLISHED:
                Config().om.info("Synchronisation d'une offre : terminé")
                break
            if s_status == Offering.STATUS_UNSTABLE:
                raise StepActionError("Synchronisation d'une offre : terminé en erreur.")
            # on fixe à 1 seconde, normalement quasiment instantané
            Config().om.debug(f"Status : '{s_status}', on attend ...")
            time.sleep(1)

    @property
    def offering(self) -> Optional[Offering]:
        return self.__offering
