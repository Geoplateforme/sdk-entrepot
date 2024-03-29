from unittest.mock import patch
from pathlib import Path
from typing import Any, Dict, List

from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.store.Upload import Upload
from sdk_entrepot_gpf.io.ApiRequester import ApiRequester
from tests.GpfTestCase import GpfTestCase


class UploadTestCase(GpfTestCase):
    """Tests Upload class.

    cmd : python3 -m unittest -b tests.store.UploadTestCase
    """

    def test_api_push_data_file(self) -> None:
        """Vérifie le bon fonctionnement de api_push_data_file.
        Dans ce test, on suppose que le datastore est défini (cf. route_params).
        """
        # On instancie une livraison pour laquelle on veut pousser des fichiers
        o_upload = Upload({"_id": "id_de_test"}, "id_datastore")
        # On récupère le nom de la clé associée au fichier
        s_key_file = Config().get("upload", "push_data_file_key")
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_upload_file", return_value=None) as o_mock_request:
            # Initialisation des paramètres utilisés par la fonction à tester
            p_file_path = Path("path/dun/fichier/a/tester.txt")
            # on prend un chemin coté api
            s_api_path = "path/cote/api"
            # On appelle la fonction que l'on veut tester
            o_upload.api_push_data_file(p_file_path, s_api_path)

            # Vérification sur o_mock_request
            o_mock_request.assert_called_once_with(
                "upload_push_data",
                p_file_path,
                s_key_file,
                route_params={"datastore": "id_datastore", "upload": "id_de_test"},
                params={"path": s_api_path + "/" + p_file_path.name},
                method=ApiRequester.POST,
            )

    def test_api_push_md5_file(self) -> None:
        """Vérifie le bon fonctionnement de api_push_md5_file.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        # On instancie une livraison pour laquelle on veut pousser des fichiers
        o_upload = Upload({"_id": "id_de_test"})
        # On récupère le nom de la clé associée au fichier
        s_key_file = Config().get("upload", "push_md5_file_key")
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_upload_file", return_value=None) as o_mock_request:
            # Initialisation des paramètres utilisés par la fonction à tester
            p_file_path = Path("path/dun/fichier/a/tester.txt")
            # On appelle la fonction que l'on veut tester
            o_upload.api_push_md5_file(p_file_path)

            # Vérification sur o_mock_request
            o_mock_request.assert_called_once_with(
                "upload_push_md5",
                p_file_path,
                s_key_file,
                route_params={"datastore": None, "upload": "id_de_test"},
                method=ApiRequester.POST,
            )

    def test_api_delete_data_file_1(self) -> None:
        """Vérifie le bon fonctionnement de api_delete_data_file si le chemin ne contient pas data/.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        # On instancie une livraison pour laquelle on veut supprimer des fichiers
        # peu importe si la livraison comporte ou pas des fichiers
        o_upload = Upload({"_id": "id_de_test"})
        # on prend un chemin coté api
        s_api_path = "path/cote/api"

        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=None) as o_mock_request:
            # On appelle la fonction que l'on veut tester
            o_upload.api_delete_data_file(s_api_path)

            # Vérification sur o_mock_request
            o_mock_request.assert_called_once_with(
                "upload_delete_data",
                method=ApiRequester.DELETE,
                route_params={"datastore": None, "upload": "id_de_test"},
                params={"path": s_api_path},
            )

    def test_api_delete_md5_file(self) -> None:
        """Vérifie le bon fonctionnement de api_delete_md5_file.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        # On instancie une livraison pour laquelle on veut supprimer des fichiers md5
        # peu importe si la livraison comporte ou pas des fichiers
        o_upload = Upload({"_id": "id_de_test"})
        # on prend un chemin coté api
        s_api_path = "path/cote/api"

        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=None) as o_mock_request:
            # On appelle la fonction que l'on veut tester
            o_upload.api_delete_md5_file(s_api_path)

            # Vérification sur o_mock_request
            o_mock_request.assert_called_once_with(
                "upload_delete_md5",
                method=ApiRequester.DELETE,
                route_params={"datastore": None, "upload": "id_de_test"},
                params={"path": s_api_path},
            )

    def test_api_open(self) -> None:
        """Vérifie le bon fonctionnement de api_open.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=None) as o_mock_request:
            # On effectue l'ouverture d'une livraison
            # On instancie une livraison à ouvrir
            o_upload_2_open = Upload({"_id": "id_à_ouvrir"})
            # On mock la fonction api_update
            with patch.object(o_upload_2_open, "api_update", return_value=None) as o_mock_api_update:
                # On appelle la fonction api_open
                o_upload_2_open.api_open()
                # Vérification sur o_mock_request
                o_mock_request.assert_called_once_with(
                    "upload_open",
                    method=ApiRequester.POST,
                    route_params={"datastore": None, "upload": "id_à_ouvrir"},
                )
                # Vérification de l'appel à api_update
                o_mock_api_update.assert_called_once()

    def test_api_close(self) -> None:
        """Vérifie le bon fonctionnement de api_close.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=None) as o_mock_request:
            # On effectue la fermeture d'une livraison
            # On instancie une livraison à fermer
            o_upload_2_close = Upload({"_id": "id_à_fermer"})
            # On mock la fonction api_update
            with patch.object(o_upload_2_close, "api_update", return_value=None) as o_mock_api_update:
                # On appelle la fonction api_close
                o_upload_2_close.api_close()
                # Vérification sur o_mock_request
                o_mock_request.assert_called_once_with(
                    "upload_close",
                    method=ApiRequester.POST,
                    route_params={"datastore": None, "upload": "id_à_fermer"},
                )
                # Vérification de l'appel à api_update
                o_mock_api_update.assert_called_once()

    def test_api_tree(self) -> None:
        """Vérifie le bon fonctionnement de api_tree.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        l_tree_wanted = [{"key_1": "value_1", "key_2": "value_2"}]
        # Instanciation d'une fausse réponse HTTP
        o_response = GpfTestCase.get_response(json=l_tree_wanted)
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            # On instancie un upload
            o_upload = Upload({"_id": "identifiant"})
            # On appelle api_tree
            l_tree = o_upload.api_tree()
            # Vérification sur o_mock_request (route upload_tree avec comme params de route l'id)
            o_mock_request.assert_called_once_with(
                "upload_tree",
                route_params={"datastore": None, "upload": "identifiant"},
            )
            # Vérifications sur l_tree
            self.assertEqual(l_tree, l_tree_wanted)

    def test_api_list_checks(self) -> None:
        """Vérifie le bon fonctionnement de api_list_checks.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        d_list_checks_wanted: Dict[str, List[Dict[str, Any]]] = {"key_1": [], "key_2": []}
        # Instanciation d'une fausse réponse HTTP
        o_response = GpfTestCase.get_response(json=d_list_checks_wanted)
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=o_response) as o_mock_request:
            # On instancie un upload
            o_upload = Upload({"_id": "identifiant"})
            # On appelle api_list_checks
            d_list_checks = o_upload.api_list_checks()
            # Vérification sur o_mock_request (route api_list_checks avec comme params de route l'id)
            o_mock_request.assert_called_once_with(
                "upload_list_checks",
                route_params={"datastore": None, "upload": "identifiant"},
            )
            # Vérifications sur list_checks
            self.assertEqual(d_list_checks, d_list_checks_wanted)

    def test_api_run_checks(self) -> None:
        """Vérifie le bon fonctionnement de api_run_checks.
        Dans ce test, le datastore n'est pas défini (cf. route_params).
        """
        # On mock la fonction route_request, on veut vérifier qu'elle est appelée avec les bons params
        with patch.object(ApiRequester, "route_request", return_value=None) as o_mock_request:
            # On instancie une livraison
            o_upload_run_checks = Upload({"_id": "id"})
            # liste des ids à verifier
            l_list_checks_ids: List[Any] = ["id1", "id2"]
            # On appelle la fonction api_run_checks
            o_upload_run_checks.api_run_checks(l_list_checks_ids)
            # Vérification sur o_mock_request
            o_mock_request.assert_called_once_with(
                "upload_run_checks",
                method=ApiRequester.POST,
                route_params={"datastore": None, "upload": "id"},
                data=["id1", "id2"],
            )
