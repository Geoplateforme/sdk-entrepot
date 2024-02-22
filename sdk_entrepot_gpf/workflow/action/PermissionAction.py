import time
from typing import Any, Dict, Optional

from sdk_entrepot_gpf.Errors import GpfSdkError
from sdk_entrepot_gpf.store.Offering import Offering
from sdk_entrepot_gpf.store.Configuration import Configuration
from sdk_entrepot_gpf.workflow.Errors import StepActionError
from sdk_entrepot_gpf.workflow.action.ActionAbstract import ActionAbstract
from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.io.Errors import ConflictError


class PermissionAction(ActionAbstract):
    """Classe dédiée à la géstion des Permissions.

    Attributes:
        __workflow_context (str): nom du contexte du workflow
        __definition_dict (Dict[str, Any]): définition de l'action
        __parent_action (Optional["Action"]): action parente
        __offering (Optional[Offering]): représentation Python de la Offering créée
    """
