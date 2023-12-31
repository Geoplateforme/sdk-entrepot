from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.interface.EventInterface import EventInterface
from tests.GpfTestCase import GpfTestCase


class EventInterfaceTestCase(GpfTestCase):
    """Tests EventInterface class.

    cmd : python3 -m unittest -b tests.store.interface.EventInterfaceTestCase
    """

    def test_api_list_events(self) -> None:
        "Vérifie le bon fonctionnement de api_list_events."
        l_data = [{"title": "string", "text": "string", "date": "2022-06-01T09:28:09.269Z", "initiator": {"_id": "string", "last_name": "string", "first_name": "string"}}]
        # Instanciation d'une fausse réponse HTTP
        o_response = GpfTestCase.get_response(json=l_data)
        for s_datastore in [None, "api_list_events"]:
            # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons param
            with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
                # on appelle la fonction à tester :api_list_events
                o_event_interface = EventInterface({"_id": "id_entité"}, s_datastore)
                l_data_recupere = o_event_interface.api_events()
                # on vérifie que route_request est appelé correctement
                o_mock_request.assert_called_once_with(
                    "store_entity_list_events",
                    route_params={"store_entity": "id_entité", "datastore": s_datastore},
                )
                # on vérifie la similitude des données retournées
                self.assertEqual(l_data, l_data_recupere)
