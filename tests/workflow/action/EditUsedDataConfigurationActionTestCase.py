from typing import Any, Dict
from unittest.mock import patch, MagicMock

from sdk_entrepot_gpf.Errors import GpfSdkError
from sdk_entrepot_gpf.store.Configuration import Configuration
from sdk_entrepot_gpf.store.StoredData import StoredData
from sdk_entrepot_gpf.workflow.action.EditUsedDataConfigurationAction import EditUsedDataConfigurationAction

from tests.GpfTestCase import GpfTestCase


class EditUsedDataConfigurationActionTestCase(GpfTestCase):
    """Tests EditUsedDataConfigurationAction class.

    cmd : python3 -m unittest -b tests.workflow.action.EditUsedDataConfigurationActionTestCase
    """

    def run_run(self, s_uuid: str, d_definition: Dict[str, Any], d_base_config: Dict[str, Any], d_new_config: Dict[str, Any], s_nom: str) -> None:
        """lancement des tests de EditUsedDataConfigurationAction.run

        Args:
            s_uuid (str): uuid
            d_definition (Dict[str, Any]): dictionnaire de l'action
            d_base_config (Dict[str, Any]): dictionnaire de la configuration à modifiée
            d_new_config (Dict[str, Any]): dictionnaire de la configuration après modification qui sera envoyé à la GPF
        """
        with self.subTest(i=s_nom):
            o_action = EditUsedDataConfigurationAction("contexte", d_definition, None)
            o_mock_base_config = MagicMock()
            o_mock_base_config.get_store_properties.return_value = d_base_config

            with patch.object(Configuration, "api_get", return_value=o_mock_base_config) as o_mock_get:
                o_action.run("datastore")
            o_mock_get.assert_called_once_with(s_uuid, datastore="datastore")
            o_mock_base_config.get_store_properties.assert_called_once_with()
            o_mock_base_config.api_full_edit.assert_called_once_with(d_new_config)

    def test_run(self) -> None:
        """test de run"""
        s_uuid = "123"
        d_add_data = {"data": "data", "stored_data": "stored_data"}
        # ajout + suppression (pas de reset de la BBox)
        d_definition: Dict[str, Any] = {
            "type": "used_data-configuration",
            "entity_id": s_uuid,
            "append_used_data": [d_add_data],
            "delete_used_data": [{"param1": "val1"}, {"param2": "val2"}, {"param1": "val3", "param2": "val3"}],
        }
        l_used_data = [
            {"param1": "val1", "autre": "val", "stored_data": "stored_data1"},
            {"param2": "val2", "autre": "val", "stored_data": "stored_data2"},
            {"param1": "val3", "param2": "val3", "autre": "val", "stored_data": "stored_data3"},
            {"param1": "val4", "param2": "val3", "autre": "val", "stored_data": "stored_data4"},
            {"param1": "val3", "param2": "val4", "autre": "val", "stored_data": "stored_data5"},
            {"param1": "val4", "param2": "val4", "autre": "val", "stored_data": "stored_data6"},
        ]
        d_base_config = {
            "name": "nouveau name",
            "type_infos": {
                "used_data": [*l_used_data],
                "bbox": {},
            },
        }
        d_new_config: Dict[str, Any] = {
            "name": "nouveau name",
            "type_infos": {
                "used_data": [
                    {"param1": "val4", "param2": "val3", "autre": "val", "stored_data": "stored_data4"},
                    {"param1": "val3", "param2": "val4", "autre": "val", "stored_data": "stored_data5"},
                    {"param1": "val4", "param2": "val4", "autre": "val", "stored_data": "stored_data6"},
                    d_add_data,
                ],
                "bbox": {},
            },
        }

        # ajout + suppression (pas de reset de la BBox)
        self.run_run(s_uuid, d_definition, d_base_config, d_new_config, "ajout + suppression (pas de reset de la BBox)")

        # maj de BBox + modif stored_data
        d_base_config["type_infos"] = {"used_data": [*l_used_data], "bbox": {}}
        self.run_run(s_uuid, d_definition, d_base_config, d_new_config, "maj de BBox + modif stored_data")

        # maj de bbox demandée mais pas de bbox dans la config
        d_definition["reset_bbox"] = True
        del d_new_config["type_infos"]["bbox"]
        d_base_config["type_infos"] = {"used_data": [*l_used_data]}
        self.run_run(s_uuid, d_definition, d_base_config, d_new_config, "maj de bbox demandée mais pas de bbox dans la config")

        # pas de modif stored_data
        d_base_config["type_infos"] = {"used_data": [*l_used_data], "bbox": {}}
        d_definition_2: Dict[str, Any] = {"type": "used_data-configuration", "entity_id": s_uuid}
        self.run_run(s_uuid, d_definition_2, d_base_config, d_base_config, "pas de modif stored_data")

        # maj de BBox + pas modif stored_data
        d_definition_2["reset_bbox"] = True
        d_base_config["type_infos"] = {"used_data": [*l_used_data], "bbox": {}}
        d_new_config_2 = {"name": "nouveau name", "type_infos": {"used_data": [*l_used_data]}}
        self.run_run(s_uuid, d_definition_2, d_base_config, d_new_config_2, "maj de BBox + pas modif stored_data")

        # ajout de used data avec suppression de doublon
        d_definition = {
            "type": "used_data-configuration",
            "entity_id": s_uuid,
            "append_used_data": [d_add_data],
            "resolve_conflict": True,
        }
        d_base_config["type_infos"] = {"used_data": [*l_used_data, d_add_data], "bbox": {}}
        d_new_config_2 = {"name": "nouveau name", "type_infos": {"used_data": [*l_used_data, *d_definition["append_used_data"]], "bbox": {}}}
        self.run_run(s_uuid, d_definition, d_base_config, d_new_config_2, "ajout de used data avec suppression de doublon")

        # ajout de used data sans suppression de doublon => erreur
        d_definition["resolve_conflict"] = False
        with self.subTest(i="ajout de used data sans suppression de doublon"):
            o_action = EditUsedDataConfigurationAction("contexte", d_definition, None)
            o_mock_base_config = MagicMock()
            o_mock_base_config.get_store_properties.return_value = d_base_config
            s_message = "La requête formulée par le programme est incorrecte (Une donnée stockée est référencée plusieurs fois). Contactez le support."
            o_mock_base_config.api_full_edit.side_effect = GpfSdkError(s_message)

            #  api_get raise une erreur GpfSdkError
            with patch.object(Configuration, "api_get", return_value=o_mock_base_config):
                with patch.object(StoredData, "api_get", return_value="stored_data"):
                    with self.assertRaises(GpfSdkError) as o_raise:
                        o_action.run("datastore")
            l_doublons = ["stored_data (2)"]
            s_new_message = s_message = (
                "Il y a au moins un doublon dans les used_data. Veuillez vérifier les append_used_data. L'option 'resolve_conflict = True'"
                + " permet de résoudre les conflits en supprimant les doublons. \n * "
                + "\n * ".join(l_doublons)
            )
            self.assertEqual(o_raise.exception.message, s_new_message)

        # autre erreur (hors doublon)
        with self.subTest(i="autre erreur (hors doublon)"):
            o_action = EditUsedDataConfigurationAction("contexte", d_definition, None)
            o_mock_base_config = MagicMock()
            o_mock_base_config.get_store_properties.return_value = d_base_config
            s_message = "autre problème"
            o_mock_base_config.api_full_edit.side_effect = GpfSdkError(s_message)

            #  api_get raise une erreur GpfSdkError
            with patch.object(Configuration, "api_get", return_value=o_mock_base_config):
                with self.assertRaises(GpfSdkError) as o_raise:
                    o_action.run("datastore")
            l_doublons = ["stored_data (2)"]
            self.assertEqual(o_raise.exception.message, s_message)
