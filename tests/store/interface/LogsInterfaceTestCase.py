from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.interface.LogsInterface import LogsInterface
from tests.GpfTestCase import GpfTestCase


class LogsInterfaceTestCase(GpfTestCase):
    """Tests LogsInterface class.

    cmd : python3 -m unittest -b tests.store.interface.LogsInterfaceTestCase
    """

    def test_api_logs_pages_filter(self) -> None:
        "Vérifie le bon fonctionnement de api_logs__pages_filter (une seule page)."
        s_data = "2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API.\n2022/05/18 14:29:25       INFO §USER§ Signal transmis avec succès."
        o_response = GpfTestCase.get_response(json="2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API.")
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            with patch.object(ApiRequester, "range_total_page", return_value=2) as o_mock_range:
                # on appelle la fonction à tester : api_logs
                # s_response_signal = s_data.split("\n")[1]
                o_log_interface = LogsInterface({"_id": "id_entité"}, datastore="datastore_id")
                s_data_recupere_info = o_log_interface.api_logs_pages_filter(1, 1, 1, "INFO")
                # s_data_recupere_error = o_log_interface.api_logs_pages_filter(-1, 0, 1, "ERROR")
                # s_data_recupere_signal = o_log_interface.api_logs_pages_filter(str_filter="Signal")
                # on vérifie que route_request et range_next_page sont appelés correctement
                o_mock_request.assert_called_with(
                    "store_entity_logs",
                    route_params={"datastore": "datastore_id", "store_entity": "id_entité"},
                    params={"page": 1, "limit": 1},
                )
                o_mock_range.assert_called_with(o_response.headers.get("Content-Range"), 1)
                # on vérifie la similitude des données retournées
                self.assertEqual("2022/05/18 14:29:25       INFO §USER§ Envoi du signal de début de l'exécution à l'API.", "\n".join(s_data_recupere_info))
                # self.assertEqual("", "\n".join(s_data_recupere_error))
                # self.assertEqual(s_response_signal, "\n".join(s_data_recupere_signal))
