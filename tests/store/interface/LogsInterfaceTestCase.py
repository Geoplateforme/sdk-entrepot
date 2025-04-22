from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.interface.LogsInterface import LogsInterface
from sdk_entrepot_gpf.store.Errors import StoreEntityError

from tests.GpfTestCase import GpfTestCase


class LogsInterfaceTestCase(GpfTestCase):
    """Tests LogsInterface class.

    cmd : python3 -m unittest -b tests.store.interface.LogsInterfaceTestCase
    """

    def test_api_logs_filter(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter."
        s_data = "2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API."
        o_response = GpfTestCase.get_response(json=[s_data])
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=1) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore="datastore_id")
                s_data_recupere_info = o_log_interface.api_logs_filter(1, 1, 1, "INFO")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_called_with(
                    "store_entity_logs",
                    route_params={"datastore": "datastore_id", "store_entity": "id_entité"},
                    params={"page": 1, "limit": 1},
                )
                o_mock_range.assert_called_with(o_response.headers.get("Content-Range"), 1)
                # on vérifie la similitude des données retournées
                self.assertEqual(s_data, "\n".join(s_data_recupere_info.logs))
                self.assertTrue(s_data_recupere_info.starting_logs)
                self.assertTrue(s_data_recupere_info.ending_logs)
                self.assertEqual(1, s_data_recupere_info.first_page)
                self.assertEqual(1, s_data_recupere_info.last_page)

        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=1) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore="datastore_id")
                s_data_recupere_error = o_log_interface.api_logs_filter(-1, 0, 1, "ERROR")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_called_with(
                    "store_entity_logs",
                    route_params={"datastore": "datastore_id", "store_entity": "id_entité"},
                    params={"page": 1, "limit": 1},
                )
                o_mock_range.assert_called_with(o_response.headers.get("Content-Range"), 1)
                # on vérifie la similitude des données retournées
                self.assertEqual("", "\n".join(s_data_recupere_error.logs))
                self.assertTrue(s_data_recupere_error.ending_logs)
                self.assertTrue(s_data_recupere_error.starting_logs)
                self.assertEqual(1, s_data_recupere_error.first_page)
                self.assertEqual(1, s_data_recupere_error.last_page)

    def test_api_logs_multiple_pages(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__filter (plusieurs pages)."
        s_data = "2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API."
        s_data1 = "2022/05/18 14:29:25       INFO §USER§ Signal transmit avec succès."
        s_datastore = "datastore_id"
        s_store_entity = "id_entité"
        p_path = "store_entity_logs"
        o_response_verif_total = GpfTestCase.get_response(json=[s_data])
        o_response1 = GpfTestCase.get_response(json=[s_data])
        o_response2 = GpfTestCase.get_response(json=[s_data1])
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", side_effect=[o_response_verif_total, o_response1, o_response2]) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=15) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": s_store_entity}, datastore=s_datastore)
                s_data_recupere_info = o_log_interface.api_logs_filter(10, 11, 1, "INFO")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_any_call(
                    p_path,
                    route_params={"datastore": s_datastore, "store_entity": s_store_entity},
                    params={"page": 1, "limit": 1},
                )
                o_mock_request.assert_any_call(
                    p_path,
                    route_params={"datastore": s_datastore, "store_entity": s_store_entity},
                    params={"page": 10, "limit": 1},
                )
                o_mock_request.assert_any_call(
                    p_path,
                    route_params={"datastore": s_datastore, "store_entity": s_store_entity},
                    params={"page": 11, "limit": 1},
                )
                self.assertEqual(o_mock_request.call_count, 3)
                o_mock_range.assert_called_with(o_response_verif_total.headers.get("Content-Range"), 1)
                # on vérifie la similitude des données retournées
                self.assertEqual([s_data, s_data1], s_data_recupere_info.logs)
                self.assertFalse(s_data_recupere_info.ending_logs)
                self.assertFalse(s_data_recupere_info.starting_logs)
                self.assertEqual(s_data_recupere_info.first_page, 10)
                self.assertEqual(s_data_recupere_info.last_page, 11)

    def test_api_logs_errors(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter (erreur)."
        s_datastore = "datastore_id"
        s_store_entity = "id_entité"
        o_response_verif_total = GpfTestCase.get_response(json=[])
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response_verif_total):
            with patch.object(ApiRequester, "range_total_page", return_value=4):
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": s_store_entity}, datastore=s_datastore)
                with self.assertRaises(StoreEntityError) as o_context_1:
                    o_log_interface.api_logs_filter(3, 2, 1, "")
                self.assertEqual("La dernière page doit être supérieur à la première (3, 2).", o_context_1.exception.message)
                with self.assertRaises(StoreEntityError) as o_context_2:
                    o_log_interface.api_logs_filter(2, 3, -1, "")
                self.assertEqual("Le nombre de lignes par page (-1) doit être positif.", o_context_2.exception.message)
                with self.assertRaises(StoreEntityError) as o_context_3:
                    o_log_interface.api_logs_filter(8, 3, 2, "")
                self.assertEqual("La première page demandée (8) est en dehors des limites (4).", o_context_3.exception.message)
                with self.assertRaises(StoreEntityError) as o_context_4:
                    o_log_interface.api_logs_filter(2, 7, 2, "")
                self.assertEqual("La dernière page demandée (7) est en dehors des limites (4).", o_context_4.exception.message)
