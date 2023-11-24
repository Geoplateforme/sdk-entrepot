from unittest.mock import MagicMock, patch
from sdk_entrepot_gpf.store.Configuration import Configuration

from sdk_entrepot_gpf.store.StoredData import StoredData
from tests.GpfTestCase import GpfTestCase


class StoredDataTestCase(GpfTestCase):
    """Tests StoredData class.

    cmd : python3 -m unittest -b tests.store.StoredDataTestCase
    """

    def test_delete_cascade(self) -> None:
        """test de delete_cascade"""
        o_store_entity = StoredData({"_id": "1", "datetime": "2022-09-20T10:45:04.396Z"})

        # Mock offerings
        o_mock_offering_1 = MagicMock()
        o_mock_offering_2 = MagicMock()
        o_mock_offering_3 = MagicMock()
        # mock config 1 => 2 offering
        o_mock_config_1 = MagicMock()
        o_mock_config_1.api_list_offerings.return_value = [o_mock_offering_1, o_mock_offering_2]
        # mock config 2 => 0 offering
        o_mock_config_2 = MagicMock()
        o_mock_config_2.api_list_offerings.return_value = []
        # mock config 3 => 1 offering
        o_mock_config_3 = MagicMock()
        o_mock_config_3.api_list_offerings.return_value = [o_mock_offering_3]

        # mock pour la fonction before_delete
        o_mock = MagicMock()
        o_mock.before_delete_function.return_value = [o_store_entity]

        for f_before_delete in [None, o_mock.before_delete_function]:
            # StoredData sans configuration
            with patch.object(Configuration, "api_list", return_value=[]) as o_mock_list:
                with patch.object(StoredData, "delete_liste_entities", return_value=None) as o_mock_delete:
                    o_store_entity.delete_cascade(f_before_delete)
                    o_mock_delete.assert_called_once_with([o_store_entity], f_before_delete)
                    o_mock_list.assert_called_once_with({"stored_data": "1"})

            # StoredData avec configuration et offres
            with patch.object(Configuration, "api_list", return_value=[o_mock_config_1, o_mock_config_2, o_mock_config_3]) as o_mock_list:
                with patch.object(StoredData, "delete_liste_entities", return_value=None) as o_mock_delete:
                    o_store_entity.delete_cascade(f_before_delete)
                    o_mock_delete.assert_called_once_with(
                        [
                            o_mock_offering_1,
                            o_mock_offering_2,
                            o_mock_config_1,
                            o_mock_config_2,
                            o_mock_offering_3,
                            o_mock_config_3,
                            o_store_entity,
                        ],
                        f_before_delete,
                    )
                    o_mock_list.assert_called_once_with({"stored_data": "1"})
                    o_mock_config_1.api_list_offerings.assert_called_once_with()
                    o_mock_config_2.api_list_offerings.assert_called_once_with()
                    o_mock_config_3.api_list_offerings.assert_called_once_with()
            o_mock_config_1.reset_mock()
            o_mock_config_2.reset_mock()
            o_mock_config_3.reset_mock()
