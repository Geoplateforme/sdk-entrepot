from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.store.Metadata import Metadata
from tests.GpfTestCase import GpfTestCase


class MetadataTestCase(GpfTestCase):
    """Tests Metadata class.

    cmd : python3 -m unittest -b tests.store.MetadataTestCase
    """

    def test_publish(self) -> None:
        "Vérifie le bon fonctionnement de publish."
        l_file = ["a", "b", "c"]
        s_endpoint_id = "hdsfkhdlfh"

        for s_datastore in [None, "publish"]:
            # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
            o_response = GpfTestCase.get_response()
            with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
                # on appelle la fonction à tester : publish
                Metadata.publish(l_file, s_endpoint_id, s_datastore)

                # on vérifie que route_request est appelé correctement
                o_mock_request.assert_called_once_with(
                    "metadata_publish",
                    route_params={"datastore": s_datastore},
                    data={"file_identifiers": l_file, "endpoint": s_endpoint_id},
                    method=ApiRequester.POST,
                )

    def test_unpublish(self) -> None:
        "Vérifie le bon fonctionnement de unpublish."
        l_file = ["a", "b", "c"]
        s_endpoint_id = "hdsfkhdlfh"

        for s_datastore in [None, "unpublish"]:
            # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
            o_response = GpfTestCase.get_response()
            with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
                # on appelle la fonction à tester : unpublish
                Metadata.unpublish(l_file, s_endpoint_id, s_datastore)

                # on vérifie que route_request est appelé correctement
                o_mock_request.assert_called_once_with(
                    "metadata_unpublish",
                    route_params={"datastore": s_datastore},
                    data={"file_identifiers": l_file, "endpoint": s_endpoint_id},
                    method=ApiRequester.POST,
                )
