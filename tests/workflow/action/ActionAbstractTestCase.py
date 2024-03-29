import json
from typing import Optional
from unittest.mock import patch, MagicMock
from sdk_entrepot_gpf.io.Config import Config

from sdk_entrepot_gpf.workflow.action.ActionAbstract import ActionAbstract
from sdk_entrepot_gpf.workflow.resolver.GlobalResolver import GlobalResolver
from tests.GpfTestCase import GpfTestCase


# classe temporaire pour les test : ActionAbstract est abstraite
class ConcreteAction(ActionAbstract):
    def run(self, datastore: Optional[str] = None) -> None:
        pass


class ActionAbstractTestCase(GpfTestCase):
    """Tests ActionAbstract class.

    cmd : python3 -m unittest -b tests.workflow.action.ActionAbstractTestCase
    """

    def test_workflow_context(self) -> None:
        """test de workflow_context"""
        d_definition = {"test": "val"}
        o_action = ConcreteAction("nom", d_definition, None)
        assert "nom" == o_action.workflow_context

    def test_definition_dict(self) -> None:
        """test de definition_dict"""
        d_definition = {"test": "val"}
        o_action = ConcreteAction("nom", d_definition, None)
        assert d_definition == o_action.definition_dict

    def test_parent_action(self) -> None:
        """test de parent_action"""
        d_definition = {"test": "val"}
        o_action = ConcreteAction("nom", d_definition, None)
        assert o_action.parent_action is None
        o_mock_parent = MagicMock()
        o_action = ConcreteAction("nom", d_definition, o_mock_parent)
        assert o_mock_parent == o_action.parent_action

    def test_resolve(self) -> None:
        """test de resolve"""
        d_definition = {"test": "val"}
        d_resolved_dico = {"resolved": "val"}
        # on mock GlobalResolver
        with patch.object(GlobalResolver, "resolve", return_value=str(json.dumps(d_resolved_dico))) as o_mock_resolve:
            o_action = ConcreteAction("nom", d_definition, None)
            # On ajout des couples clef-valeur...
            o_action.resolve(key="value", datastore="datastore_id")
            assert o_action.definition_dict == d_resolved_dico
            # Qui doivent être transmis à la résolution
            o_mock_resolve.assert_called_once_with(str(json.dumps(d_definition)), key="value", datastore="datastore_id")

    def test_get_filters(self) -> None:
        """Test de get_filters."""
        d_info_full = {"info_1": "val_1", "info_2": "val_2", "info_3": "val_3"}
        d_tags_full = {"tag_1": "val_1", "tag_2": "val_2", "tag_3": "val_3"}
        # On mock la fonction Config.get
        with patch.object(Config(), "get_str", side_effect=["info_1;info_2", "tag_3"]) as o_mock_get:
            # Appel
            d_infos, d_tags = ActionAbstract.get_filters("config_key", d_info_full, d_tags_full)
            # Vérifications
            # Fonction appelée 2 fois
            self.assertEqual(o_mock_get.call_count, 2)
            # Pour récupère la liste des infos à filter
            o_mock_get.assert_any_call("config_key", "uniqueness_constraint_infos", "")
            # Pour récupère la liste des tags à filter
            o_mock_get.assert_any_call("config_key", "uniqueness_constraint_tags", "")
            # Vérifications critères conservés
            self.assertDictEqual(d_infos, {"info_1": "val_1", "info_2": "val_2"})
            self.assertDictEqual(d_tags, {"tag_3": "val_3"})

    def test_str(self) -> None:
        """test de __str__"""
        d_definition = {"test": "val"}
        o_action = ConcreteAction("nom", d_definition, None)
        self.assertEqual("ConcreteAction(workflow=nom)", str(o_action))
