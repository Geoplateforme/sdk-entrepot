from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from sdk_entrepot_gpf.store.Permission import Permission
from sdk_entrepot_gpf.workflow.Errors import StepActionError
from sdk_entrepot_gpf.workflow.action.CopieConfigurationAction import CopieConfigurationAction
from sdk_entrepot_gpf.workflow.action.ConfigurationAction import ConfigurationAction
from sdk_entrepot_gpf.workflow.action.PermissionAction import PermissionAction

from tests.GpfTestCase import GpfTestCase


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
# pylint:disable=too-many-branches


class PermissionActionTestCase(GpfTestCase):
    """Tests CopieConfigurationAction class.

    cmd : python3 -m unittest -b tests.workflow.action.PermissionActionTestCase
    """

    def test_run(self) -> None:
        """test de run"""
        d_action: Dict[str, Any] = {
            "type": "permission",
            "body_parameters": {
                "name": "name_permission",
                "layer_name": "layer_name_permission",
            },
        }
        o_action = PermissionAction("context", d_action)
        self.assertIsNone(o_action.permission)

        # fonctionnement OK
        permission = Permission({"_id": "permission_id"})
        with patch.object(Permission, "api_create", return_value=permission) as o_mock_create:
            o_action.run("datastore")

        o_mock_create.assert_called_once_with(d_action["body_parameters"], route_params={"datastore": "datastore"})
        self.assertEqual(permission, o_action.permission)
