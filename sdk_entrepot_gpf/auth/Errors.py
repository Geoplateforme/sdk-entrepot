from sdk_entrepot_gpf.Errors import GpfSdkError


class AuthentificationError(GpfSdkError):
    """Est levée quand un problème apparaît durant la récupération d'informations d'authentification

    Attr:
        __message (str): message décrivant le problème
    """
