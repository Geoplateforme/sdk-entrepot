from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.interface.LogsInterface import LogsInterface
from tests.GpfTestCase import GpfTestCase
from sdk_entrepot_gpf.store.Errors import StoreEntityError


class LogsInterfaceTestCase(GpfTestCase):
    """Tests LogsInterface class.

    cmd : python3 -m unittest -b tests.store.interface.LogsInterfaceTestCase
    """

<<<<<<< HEAD
    def test_api_logs_pages_filter(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter (une seule page)."
        o_response = GpfTestCase.get_response(json=["2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API."])
=======
    def test_api_logs_monopage(self) -> None:
        "Vérifie le bon fonctionnement de api_logs (une seule page)."
        s_data = "2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API.\n2022/05/18 14:29:25       INFO §USER§ Signal transmis avec succès."
        l_rep: List[Dict[str, Any]] = [
            {"datastore": "datastore_id", "data": s_data.split("\n"), "rep": s_data},
            {"datastore": "datastore_id", "data": "", "rep": ""},
            {"datastore": "datastore_id", "data": [], "rep": ""},
            {"datastore": "datastore_id", "data": ["log1", "log2", ' log "complexe"'], "rep": 'log1\nlog2\n log "complexe"'},
        ]

        for d_rep in l_rep:
            o_response = GpfTestCase.get_response(json=d_rep["data"])
            # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
            with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
                with patch.object(ApiRequester, "range_next_page", return_value=False) as o_mock_range:
                    # on appelle la fonction à tester : api_logs
                    o_log_interface = LogsInterface({"_id": "id_entité"}, datastore=d_rep["datastore"])
                    s_data_recupere = o_log_interface.api_logs()
                    # on vérifie que route_request et range_next_page sont appelés correctement
                    o_mock_request.assert_called_once_with(
                        "store_entity_logs",
                        route_params={"datastore": d_rep["datastore"], "store_entity": "id_entité"},
                        params={"page": 1, "limit": 2000},
                    )
                    o_mock_range.assert_called_once_with(o_response.headers.get("Content-Range"), len(d_rep["data"]))
                    # on vérifie la similitude des données retournées
                    self.assertEqual(d_rep["rep"], s_data_recupere)

    def test_test_api_logs_multipage(self) -> None:
        "Vérifie le bon fonctionnement de api_logs (plusieurs pages)."
        # paramètre
        s_datastore = "datastore_id"
        l_data = [f"log {j}" for j in range(2000)]

        # nombre de page voulue
        i_page = 4

        o_response = GpfTestCase.get_response(json=l_data)
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_next_page", side_effect=[True] * (i_page - 1) + [False]) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore=s_datastore)
                s_data_recupere = o_log_interface.api_logs()
                # on vérifie la similitude des données retournées
                s_data = "\n".join(l_data * i_page)

                print(len(s_data), len(s_data_recupere))

                self.assertEqual(s_data, s_data_recupere)
                # on vérifie que route_request et range_next_page sont appelés correctement
                self.assertEqual(i_page, o_mock_request.call_count)
                self.assertEqual(i_page, o_mock_range.call_count)
                for i in range(1, i_page + 1):
                    o_mock_request.assert_any_call(
                        "store_entity_logs",
                        route_params={"datastore": s_datastore, "store_entity": "id_entité"},
                        params={"page": i, "limit": 2000},
                    )

                    o_mock_range.assert_any_call(o_response.headers.get("Content-Range"), 2000 * i)

    def test_api_logs_filter(self) -> None:
        "Vérifie le bon fonctionnement de api_logs_filter (une seule page)."
        s_data = "2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API.\n2022/05/18 14:29:25       INFO §USER§ Signal transmis avec succès."
        d_rep: Dict[str, Any] = {"datastore": "datastore_id", "data": s_data.split("\n"), "rep": s_data}
        o_response = GpfTestCase.get_response(json=d_rep["data"])
>>>>>>> dev
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=2) as o_mock_range:
                # on appelle la fonction à tester : api_logs
<<<<<<< HEAD
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore="datastore_id")
                s_data_recupere_info = o_log_interface.api_logs_pages_filter(1, 1, 1, "INFO")
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
                s_data_recupere_error = o_log_interface.api_logs_pages_filter(-1, 0, 1, "ERROR")
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
                s_data_recupere_info = o_log_interface.api_logs_pages_filter(10, 11, 1, "INFO")
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
                    o_log_interface.api_logs_pages_filter(3, 2, 1, "")
                self.assertEqual("La dernière page doit être superieur a la première (3, 2)", context.exception.message)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_pages_filter(2, 3, -1, "")
                self.assertEqual("le nombre de ligne par page doit être positif (-1)", context.exception.message)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_pages_filter(8, 3, 2, "")
                self.assertTrue("La première page est en dehors des limites 4", context.exception.message)
                with self.assertRaises(StoreEntityError) as context:
                    o_log_interface.api_logs_pages_filter(2, 7, 2, "")
                self.assertTrue("La dernière page est en dehors des limites 4", context.exception.message)
                # on vérifie que route_request et range_next_page sont appelés correctement
=======
                s_response_info = s_data
                s_response_success = s_data.split("\n")[1]
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore=d_rep["datastore"])
                s_data_recupere_info = o_log_interface.api_logs_filter(str_filter="INFO")
                s_data_recupere_error = o_log_interface.api_logs_filter(str_filter="ERROR")
                s_data_recupere_success = o_log_interface.api_logs_filter(str_filter="succès")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_called_with(
                    "store_entity_logs",
                    route_params={"datastore": d_rep["datastore"], "store_entity": "id_entité"},
                    params={"page": 1, "limit": 2000},
                )
                o_mock_range.assert_called_with(o_response.headers.get("Content-Range"), len(d_rep["data"]))
                # on vérifie la similitude des données retournées
                self.assertEqual(s_response_info, "\n".join(s_data_recupere_info))
                self.assertEqual("", "\n".join(s_data_recupere_error))
                self.assertEqual(s_response_success, "\n".join(s_data_recupere_success))
>>>>>>> dev
