from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.Endpoint import Endpoint
from sdk_entrepot_gpf.store.Errors import StoreEntityError

from tests.GpfTestCase import GpfTestCase


class EndpointTestCase(GpfTestCase):
    """Tests Endpoint class.

    cmd : python3 -m unittest -b tests.store.EndpointTestCase
    """

    def test_api_list(self) -> None:
        """Vérifie le bon fonctionnement de api_list."""
        # Extrait de la requête "datastore" de l'API
        d_data = {
            "endpoints": [
                {
                    "endpoint": {
                        "_id": "endpoint_1",
                        "name": "Service WMTS",
                        "type": "WMTS-TMS",
                    }
                },
                {
                    "endpoint": {
                        "_id": "endpoint_2",
                        "name": "Service de téléchargement",
                        "type": "DOWNLOAD",
                    }
                },
            ]
        }

        # Instanciation d'une fausse réponse HTTP
        o_response = GpfTestCase.get_response(json=d_data)

        # 1 : pas de filtres
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons param
        with patch.object(ApiRequester(), "route_request", return_value=o_response) as o_mock_request:
            l_endpoints = Endpoint.api_list(datastore="datastore_id")
            # on vérifie que route_request est appelée correctement
            o_mock_request.assert_called_once_with("datastore_get", route_params={"datastore": "datastore_id"})
            # on vérifie qu'on a bien récupéré une liste de 2 Endpoints
            self.assertIsInstance(l_endpoints, list)
            self.assertEqual(len(l_endpoints), 2)
            self.assertIsInstance(l_endpoints[0], Endpoint)
            self.assertIsInstance(l_endpoints[1], Endpoint)
            self.assertEqual(l_endpoints[0].id, "endpoint_1")
            self.assertEqual(l_endpoints[1].id, "endpoint_2")

        # 2 : filtre sur le nom
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons param
        with patch.object(ApiRequester(), "route_request", return_value=o_response) as o_mock_request:
            l_endpoints = Endpoint.api_list(infos_filter={"name": "Service WMTS"})
            # on vérifie que route_request est appelée correctement
            o_mock_request.assert_called_once_with("datastore_get", route_params={"datastore": None})
            # on vérifie qu'on a bien récupéré une liste de 1 Endpoint
            self.assertIsInstance(l_endpoints, list)
            self.assertEqual(len(l_endpoints), 1)
            self.assertIsInstance(l_endpoints[0], Endpoint)
            self.assertEqual(l_endpoints[0].id, "endpoint_1")

        # 2 : filtre sur le type
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons param
        with patch.object(ApiRequester(), "route_request", return_value=o_response) as o_mock_request:
            l_endpoints = Endpoint.api_list(infos_filter={"type": "DOWNLOAD"})
            # on vérifie que route_request est appelée correctement
            o_mock_request.assert_called_once_with("datastore_get", route_params={"datastore": None})
            # on vérifie qu'on a bien récupéré une liste de 1 Endpoint
            self.assertIsInstance(l_endpoints, list)
            self.assertEqual(len(l_endpoints), 1)
            self.assertIsInstance(l_endpoints[0], Endpoint)
            self.assertEqual(l_endpoints[0].id, "endpoint_2")

    def test_api_create(self) -> None:
        """Vérifie le bon fonctionnement de api_create."""
        with self.assertRaises(StoreEntityError) as o_arc:
            Endpoint.api_create(None)
        self.assertEqual("Impossible de créer un Endpoint", o_arc.exception.message)

    def test_api_delete(self) -> None:
        """Vérifie le bon fonctionnement de api_delete."""
        with self.assertRaises(StoreEntityError) as o_arc:
            Endpoint({}).api_delete()
        self.assertEqual("Impossible de supprimer un Endpoint", o_arc.exception.message)

    def test_api_get(self) -> None:
        """Vérifie le bon fonctionnement de api_get."""
        # Extrait de la requête "datastore" de l'API
        s_datastore = "datastore"
        l_endpoint = [
            Endpoint(
                {
                    "_id": "endpoint_1",
                    "name": "Service WMTS",
                    "type": "WMTS-TMS",
                },
                s_datastore,
            ),
            Endpoint(
                {
                    "_id": "endpoint_2",
                    "name": "Service de téléchargement",
                    "type": "DOWNLOAD",
                },
                s_datastore,
            ),
        ]
        with patch.object(Endpoint, "api_list", return_value=l_endpoint) as o_mock_api_list:
            o_endpoint = Endpoint.api_get("endpoint_2", datastore=s_datastore)
            self.assertEqual(o_endpoint, l_endpoint[1])
            o_mock_api_list.assert_called_once_with(datastore=s_datastore)

        s_id = "pas dans la liste"
        with patch.object(Endpoint, "api_list", return_value=l_endpoint) as o_mock_api_list:
            with self.assertRaises(StoreEntityError) as o_arc:
                Endpoint.api_get(s_id, datastore=s_datastore)
            self.assertEqual(f"le endpoint {s_id} est introuvable", o_arc.exception.message)
