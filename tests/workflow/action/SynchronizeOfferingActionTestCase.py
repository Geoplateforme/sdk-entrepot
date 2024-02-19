from typing import Any, Dict, List
from unittest.mock import patch, MagicMock
from sdk_entrepot_gpf.io.Errors import ConflictError, NotFoundError
from sdk_entrepot_gpf.store.Configuration import Configuration
from sdk_entrepot_gpf.store.Offering import Offering
from sdk_entrepot_gpf.workflow.Errors import StepActionError

from sdk_entrepot_gpf.workflow.action.SynchronizeOfferingAction import SynchronizeOfferingAction

from tests.GpfTestCase import GpfTestCase


class TestFind(SynchronizeOfferingAction):
    """Fonction pour test de SynchronizeOfferingAction._find_offerings()"""

    def find_offerings(self, datastore: str) -> List[Offering]:
        """passe plat pour _find_offerings

        Args:
            datastore (str): datastore

        Returns:
            List[Offering]: sortie de _find_offerings
        """
        return self._find_offerings(datastore)


class SynchronizeOfferingActionTestCase(GpfTestCase):
    """Tests SynchronizeOfferingAction class.

    cmd : python3 -m unittest -b tests.workflow.action.SynchronizeOfferingActionTestCase
    """

    def test__find_offerings(self) -> None:  # pylint: disable=too-many-locals,too-many-statements
        """test de _find_offerings"""
        # problème dans la définition de l'action
        s_datastore = "datastore_run"
        d_definition: Dict[str, Any] = {}
        o_action = TestFind("base", d_definition)

        with self.assertRaises(StepActionError) as o_err:
            o_action.find_offerings(s_datastore)
        self.assertEqual('Il faut L\'une des clefs suivantes : "entity_id" ou "filter_infos" pour cette action.', o_err.exception.message)

        # Entité non trouvé avec l'id
        d_definition = {"entity_id": "123"}
        o_action = TestFind("base", d_definition)
        with patch.object(Offering, "api_get", side_effect=NotFoundError("", "", {}, {}, "")) as o_mock_api_get:
            with self.assertRaises(StepActionError) as o_err:
                o_action.find_offerings(s_datastore)
            self.assertEqual(f"Impossible de trouver l'offre : {d_definition['entity_id']}.", o_err.exception.message)
            o_mock_api_get.assert_called_once_with(d_definition["entity_id"], datastore=s_datastore)

        # entité trouvé par l'ID
        o_mock_1 = MagicMock()
        with patch.object(Offering, "api_get", return_value=o_mock_1) as o_mock_api_get:
            l_offering = o_action.find_offerings(s_datastore)
        self.assertListEqual([o_mock_1], l_offering)
        o_mock_api_get.assert_called_once_with(d_definition["entity_id"], datastore=s_datastore)

        # liste par Offering.api_list()
        d_definition = {"filter_infos": {"key": "123"}}
        o_action = TestFind("base", d_definition)
        l_mock = [MagicMock() for i in range(3)]
        with patch.object(Offering, "api_list", return_value=l_mock) as o_mock_api_list:
            l_offering = o_action.find_offerings(s_datastore)
        self.assertListEqual(l_mock, l_offering)
        o_mock_api_list.assert_called_once_with(d_definition["filter_infos"], datastore=s_datastore)

        d_config = {"type_infos": {"used_data": [{"stored_data": "1"}, {"stored_data": "2"}]}}
        l_mock = [MagicMock() for i in range(3)]
        o_mock_2 = MagicMock()
        o_mock_2.api_list_offerings.return_value = l_mock
        o_mock_2.__getitem__.side_effect = lambda key: d_config[key]
        # liste par o_config.api_list_offerings
        for d_definition in [{"filter_infos": {"configuration": "123"}}, {"filter_infos": {"configuration": "123", "stored_data": "2"}}]:
            o_action = TestFind("base", d_definition)
            with patch.object(Configuration, "api_get", return_value=o_mock_2) as o_mock_api_get:
                l_offering = o_action.find_offerings(s_datastore)
            self.assertListEqual(l_mock, l_offering)
            o_mock_api_get.assert_called_once_with(d_definition["filter_infos"]["configuration"], datastore=s_datastore)
            o_mock_2.api_list_offerings.assert_called_once_with()
            o_mock_2.reset_mock()

        # différents filtres
        d_definition = {"filter_infos": {"configuration": "123", "stored_data": "2", "type": "a", "endpoint": "b", "status": "c"}}
        o_action = TestFind("base", d_definition)
        d_mock_offering = {"type": "a", "endpoint": {"_id": "b"}, "status": "c"}
        o_mock_3 = MagicMock()
        o_mock_3.__getitem__.side_effect = lambda key: d_mock_offering[key]
        l_mock.append(o_mock_3)
        with patch.object(Configuration, "api_get", return_value=o_mock_2) as o_mock_api_get:
            l_offering = o_action.find_offerings(s_datastore)
        self.assertListEqual([o_mock_3], l_offering)
        o_mock_api_get.assert_called_once_with(d_definition["filter_infos"]["configuration"], datastore=s_datastore)
        o_mock_2.api_list_offerings.assert_called_once_with()

        # vide car stored_data différent de celle de config
        d_definition = {"filter_infos": {"configuration": "123", "stored_data": "incompatible"}}
        o_action = TestFind("base", d_definition)
        o_mock_2.reset_mock()
        with patch.object(Configuration, "api_get", return_value=o_mock_2) as o_mock_api_get:
            l_offering = o_action.find_offerings(s_datastore)
        self.assertListEqual([], l_offering)
        o_mock_api_get.assert_called_once_with(d_definition["filter_infos"]["configuration"], datastore=s_datastore)
        o_mock_2.api_list_offerings.assert_not_called()

    def test_run_ko(self) -> None:
        """test de run en erreur"""
        s_datastore = "datastore_run"

        # Liste vide
        d_definition: Dict[str, Any] = {"filter_infos": {"test": "123"}}
        o_action = SynchronizeOfferingAction("base", d_definition)
        with patch.object(SynchronizeOfferingAction, "_find_offerings", return_value=[]) as o_mock_find:
            with self.assertRaises(StepActionError) as o_err:
                o_action.run(s_datastore)
            self.assertEqual("Aucune offre trouvée pour la synchronisation", o_err.exception.message)
            o_mock_find.assert_called_once_with(s_datastore)

        # plusieurs résultat et "if_multi" == "error"
        d_definition = {"filter_infos": {"test": "123"}, "if_multi": "error"}
        l_offering = [MagicMock(), MagicMock()]
        o_action = SynchronizeOfferingAction("base", d_definition)
        with patch.object(SynchronizeOfferingAction, "_find_offerings", return_value=l_offering) as o_mock_find:
            with self.assertRaises(StepActionError) as o_err:
                o_action.run(s_datastore)
            self.assertEqual(f"Plusieurs offres trouvées pour la synchronisation : {l_offering}", o_err.exception.message)
            o_mock_find.assert_called_once_with(s_datastore)

        # Différentes erreurs lors de la synchronisation
        d_definition = {"filter_infos": {"test": "123"}}
        l_offering = []
        l_errors = []
        ## api_synchronize => ConflictError
        o_mock_1 = MagicMock()
        e_conflict = ConflictError("", "", {}, {}, "erreur type ConflictError")
        o_mock_1.api_synchronize.side_effect = e_conflict
        l_offering.append(o_mock_1)
        l_errors.append(f"Problème lors de la synchronisation de {o_mock_1} : {e_conflict.message}")
        ## api_synchronize => NotFoundError
        o_mock_2 = MagicMock()
        o_mock_2.api_synchronize.side_effect = NotFoundError("", "", {}, {}, "erreur type NotFoundError")
        l_offering.append(o_mock_2)
        l_errors.append(f"Impossible de trouver l'offre {o_mock_2}. A-elle été supprimée ?")
        # Offering.STATUS_UNSTABLE
        o_mock_3 = MagicMock()
        o_mock_3.api_synchronize.return_value = None
        o_mock_3.api_update.return_value = None
        i = -1

        def side_effect_getitem(key: str) -> str:
            """fonction pour le side effect de o_mock_3.__getitem__

            Args:
                key (str): clef

            Returns:
                str: valeur
            """
            # récupération de 'i' dans la fonction mère
            nonlocal i
            if key == "status":
                i = i + 1
                return ["non", "non", Offering.STATUS_UNSTABLE][i]
            return key

        o_mock_3.__getitem__.side_effect = side_effect_getitem
        l_offering.append(o_mock_3)
        l_errors.append(f"Synchronisation de {o_mock_3} : terminé en erreur.")

        o_action = SynchronizeOfferingAction("base", d_definition)
        with patch.object(SynchronizeOfferingAction, "_find_offerings", return_value=l_offering) as o_mock_find:
            with self.assertRaises(StepActionError) as o_err:
                o_action.run(s_datastore)
            self.assertEqual("La synchronisation d'au moins une offre est terminée en erreur \n * " + "\n * ".join(l_errors), o_err.exception.message)
            o_mock_find.assert_called_once_with(s_datastore)

    def test_run_ok(self) -> None:
        """test de run OK"""
        s_datastore = "datastore_run"

        # OK multiple
        l_mock = []
        d_mock = {"status": Offering.STATUS_PUBLISHED}
        for i in range(3):
            o_mock = MagicMock()
            o_mock.__getitem__.side_effect = lambda key: d_mock[key]
            o_mock.get_url.return_value = [f"url {i}"]
            l_mock.append(o_mock)

        d_definition: Dict[str, Any] = {"filter_infos": {"test": "123"}}
        o_action = SynchronizeOfferingAction("base", d_definition)
        with patch.object(SynchronizeOfferingAction, "_find_offerings", return_value=l_mock) as o_mock_find:
            o_action.run(s_datastore)
            o_mock_find.assert_called_once_with(s_datastore)
        for o_mock in l_mock:
            o_mock.get_url.assert_called_once_with()
            o_mock.__getitem__.assert_called_once_with("status")
            o_mock.reset_mock()

        # OK multiple + "if_multi" == "first"
        d_definition = {"filter_infos": {"test": "123"}, "if_multi": "first"}
        o_action = SynchronizeOfferingAction("base", d_definition)
        with patch.object(SynchronizeOfferingAction, "_find_offerings", return_value=l_mock) as o_mock_find:
            o_action.run(s_datastore)
            o_mock_find.assert_called_once_with(s_datastore)
        ## premier élément appeler
        l_mock[0].get_url.assert_called_once_with()
        l_mock[0].__getitem__.assert_called_once_with("status")
        l_mock[0].reset_mock()
        ## autres non
        for o_mock in l_mock[1:]:
            o_mock.get_url.assert_not_called()
            o_mock.__getitem__.assert_not_called()
            # o_mock.reset_mock()
