from unittest.mock import patch

from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from sdk_entrepot_gpf.io.Errors import NotFoundError
from sdk_entrepot_gpf.store.Offering import Offering
from sdk_entrepot_gpf.store.StoreEntity import StoreEntity
from tests.GpfTestCase import GpfTestCase


class OfferingTestCase(GpfTestCase):
    """Tests Offering class.

    cmd : python3 -m unittest -b tests.store.OfferingTestCase
    """

    def test_api_delete(self) -> None:
        """Vérifie le bon fonctionnement de api_delete."""
        with patch.object(StoreEntity, "api_delete", return_value=None) as o_mock_delete:
            with patch.object(Offering, "api_update", side_effect=[None, None, NotFoundError("", "", {}, {}, "")]) as o_mock_update:
                # on appelle la fonction à tester : api_abort
                o_offering = Offering({"_id": "id_entité"})
                o_offering.api_delete()

        o_mock_delete.assert_called_once_with()
        self.assertEqual(3, o_mock_update.call_count)

    def test_api_synchronize(self) -> None:
        """Vérifie le bon fonctionnement de api_synchronize."""
        for s_datastore in [None, "datastore_offering"]:
            # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
            with patch.object(ApiRequester, "route_request", return_value=None) as o_mock_request:
                with patch.object(Offering, "api_update", return_value=None) as o_mock_update:
                    # on appelle la fonction à tester : api_abort
                    o_offering = Offering({"_id": "id_entité"}, s_datastore)
                    o_offering.api_synchronize()

                    # on vérifie que route_request est appelé correctement
                    o_mock_request.assert_called_once_with(
                        "offering_synchronize",
                        route_params={"offering": "id_entité", "datastore": s_datastore},
                        method=ApiRequester.PUT,
                    )
                    o_mock_update.assert_called_once_with()

    def test_get_url(self) -> None:
        """Vérifie le bon fonctionnement de get_url."""
        # urls sous forme de liste de string
        o_offering = Offering({"_id": "id_entité", "urls": [f"url_{i}" for i in range(3)]})
        l_url = o_offering.get_url()
        self.assertListEqual([f"url_{i}" for i in range(3)], l_url)

        # urls sous forme de liste de dict
        o_offering = Offering({"_id": "id_entité", "urls": [{"url": f"url_{i}"} for i in range(3)]})
        l_url = o_offering.get_url()
        self.assertListEqual([f"url_{i}" for i in range(3)], l_url)
