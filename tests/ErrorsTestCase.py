from ignf_gpf_sdk.Errors import GpfSdkError
from tests.GpfTestCase import GpfTestCase


class ErrorsTestCase(GpfTestCase):
    """Tests Errors classes.

    cmd : python3 -m unittest -b tests.ErrorsTestCase
    """

    @staticmethod
    def raise_gpf_api_error() -> None:
        raise GpfSdkError("message")

    def test_gpf_api_error(self) -> None:
        """Vérifie le bon fonctionnement de GpfSdkError."""
        # On lève l'exception
        with self.assertRaises(GpfSdkError) as o_arc:
            ErrorsTestCase.raise_gpf_api_error()
        # Vérifications
        # Message renvoi message
        self.assertEqual(o_arc.exception.message, "message")
        # La forme str renvoi message
        self.assertEqual(str(o_arc.exception), "message")
        self.assertEqual(f"{o_arc.exception}", "message")
        # La représentation est le nom de classe + le message
        self.assertEqual(repr(o_arc.exception), "GpfSdkError(message)")
