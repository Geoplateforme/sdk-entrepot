from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.interface.LogsInterface import LogsInterface
from tests.GpfTestCase import GpfTestCase
from sdk_entrepot_gpf.store.Errors import StoreEntityError


class LogsInterfaceTestCase(GpfTestCase):
    """Tests LogsInterface class.

    cmd : python3 -m unittest -b tests.store.interface.LogsInterfaceTestCase
    """

    def test_api_logs_filter(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter (une seule page)."
        o_response = GpfTestCase.get_response(json=["2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API."])
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=2) as o_mock_range:
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
                self.assertEqual("2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API.", "\n".join(s_data_recupere_info))

        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=2) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore="datastore_id")
                s_data_recupere_error = o_log_interface.api_logs_filter(-1, 0, 1, "ERROR")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_called_with(
                    "store_entity_logs",
                    route_params={"datastore": "datastore_id", "store_entity": "id_entité"},
                    params={"page": 2, "limit": 1},
                )
                o_mock_range.assert_called_with(o_response.headers.get("Content-Range"), 1)
                # on vérifie la similitude des données retournées
                self.assertEqual("", "\n".join(s_data_recupere_error))

    def test_api_logs_multiple_pages(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter (plusieurs pages)."
        data = "2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API."
        data1 = "2022/05/18 14:29:25       INFO §USER§ Signal transmit avec succès."
        datastore = "datastore_id"
        store_entity = "id_entité"
        path = "store_entity_logs"
        o_response_verif_total = GpfTestCase.get_response(json=[data])
        o_response1 = GpfTestCase.get_response(json=[data])
        o_response2 = GpfTestCase.get_response(json=[data1])
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", side_effect=[o_response_verif_total, o_response1, o_response2]) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=15) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": store_entity}, datastore=datastore)
                s_data_recupere_info = o_log_interface.api_logs_filter(10, 11, 1, "INFO")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_any_call(
                    path,
                    route_params={"datastore": datastore, "store_entity": store_entity},
                    params={"page": 1, "limit": 1},
                )
                o_mock_request.assert_any_call(
                    path,
                    route_params={"datastore": datastore, "store_entity": store_entity},
                    params={"page": 10, "limit": 1},
                )
                o_mock_request.assert_any_call(
                    path,
                    route_params={"datastore": datastore, "store_entity": store_entity},
                    params={"page": 11, "limit": 1},
                )
                self.assertEqual(o_mock_request.call_count, 3)
                o_mock_range.assert_called_with(o_response_verif_total.headers.get("Content-Range"), 1)
                # on vérifie la similitude des données retournées
                self.assertEqual([data, data1], s_data_recupere_info)

    def test_api_logs_errors(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter (erreur)."
        datastore = "datastore_id"
        store_entity = "id_entité"
        o_response_verif_total = GpfTestCase.get_response(json=[])
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response_verif_total) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=4) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": store_entity}, datastore=datastore)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_filter(3, 2, 1, "")
                self.assertEqual("La dernière page doit être superieur a la première (3, 2)", context.exception.message)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_filter(2, 3, -1, "")
                self.assertEqual("le nombre de ligne par page doit être positif (-1)", context.exception.message)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_filter(8, 3, 2, "")
                self.assertTrue("La première page est en dehors des limites 4", context.exception.message)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_filter(2, 7, 2, "")
                self.assertTrue("La dernière page est en dehors des limites 4", context.exception.message)
                # on vérifie que route_request et range_next_page sont appelés correctement
