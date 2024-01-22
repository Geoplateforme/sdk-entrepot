from typing import List, Optional

from sdk_entrepot_gpf.__main__ import Main
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from sdk_entrepot_gpf.workflow.action.ActionAbstract import ActionAbstract
from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.io.Errors import NotFoundError
from sdk_entrepot_gpf import store


class DeleteAction(ActionAbstract):
    """Classe dédiée à la création des Offering.

    Attributes:
        __workflow_context (str): nom du contexte du workflow
        __definition_dict (Dict[str, Any]): définition de l'action
        __parent_action (Optional["Action"]): action parente
    """

    def run(self, datastore: Optional[str] = None) -> None:
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

        Config().om.info("Suppression...")
        if "entity_type" not in self.definition_dict:
            raise Exception("La valeur entity_type est obligatoire pour cette action")
        if self.definition_dict["entity_type"] not in Main.DELETABLE_TYPES:
            raise Exception(f"Type {self.definition_dict['entity_type']} non reconnu. Types valides : {', '.join(Main.DELETABLE_TYPES)}")
        # Recherche de la/ les entité à supprimé
        l_entities = []
        if self.definition_dict.get("entity_id"):
            ## si id => on recherche directement
            try:
                l_entities.append(store.TYPE__ENTITY[self.definition_dict["entity_type"]].api_get(self.definition_dict["entity_id"], datastore))
            except NotFoundError as e:
                if not self.definition_dict.get("not_found_ok"):
                    raise e
        elif "filter_infos" in self.definition_dict or "filter_tags" in self.definition_dict:
            ## par liste des éléments
            l_entities = store.TYPE__ENTITY[self.definition_dict["entity_type"]].api_list(self.definition_dict.get("filter_infos"), self.definition_dict.get("filter_infos"), datastore=datastore)

        if len(l_entities) == 0 and not self.definition_dict.get("not_found_ok"):
            raise Exception("Aucune entité trouvé pour la suppression")
        if len(l_entities) > 1:
            if self.definition_dict.get("if_multi") == "error":
                # On sort en erreur
                raise Exception("Aucune entité trouvé pour la suppression")
            elif self.definition_dict.get("if_multi") == "first":
                # on ne supprime que le 1er élément trouvé
                l_entities = [l_entities[0]]
            # on les supprimera tous

        # suppression
        if self.definition_dict.get("cascade"):
            Config().om.info("Suppression en cascade, recherche des entités à supprimer ...")
            l_entities_cascade = []
            ## suppression des entités en cascades
            for o_entity in l_entities:
                l_entities_cascade += o_entity.get_liste_deletable_cascade()
            l_entities = l_entities_cascade
        ## suppression
        StoreEntity.delete_liste_entities(l_entities, question_before_delete)
