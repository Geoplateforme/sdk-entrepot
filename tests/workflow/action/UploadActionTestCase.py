from typing import Any, Dict, List, Optional

from pathlib import Path
from unittest.mock import patch, MagicMock
from sdk_entrepot_gpf.store.CheckExecution import CheckExecution
from sdk_entrepot_gpf.workflow.action.ActionAbstract import ActionAbstract

from sdk_entrepot_gpf.workflow.action.UploadAction import UploadAction
from sdk_entrepot_gpf.store.Upload import Upload
from sdk_entrepot_gpf.io.Config import Config
from sdk_entrepot_gpf.Errors import GpfSdkError
from tests.GpfTestCase import GpfTestCase

# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
# pylint:disable=too-many-branches
# pylint:disable=dangerous-default-value
# pylint:disable=too-many-statements
# pylint:disable=protected-access
# fmt: off
# (on désactive le formatage en attendant Python 3.10 et la possibilité de mettre des parenthèses pour gérer le multi with proprement)


class UploadActionTestCase(GpfTestCase):
    """Tests UploadAction class.

    cmd : python3 -m unittest -b tests.workflow.action.UploadActionTestCase
    """

    # constante afin de savoir si un fichier téléversé est entièrement téléversé ou pas.
    SIZE_OK = 10000
    @classmethod
    def setUpClass(cls) -> None:
        """fonction lancée une fois avant tous les tests de la classe"""
        super().setUpClass()
        # On détruit le Singleton Config
        Config._instance = None
        # On charge une config spéciale pour les tests d'upload
        o_config = Config()
        o_config.read(GpfTestCase.conf_dir_path / "test_upload.ini")
        o_config.set_output_manager(MagicMock())

    @classmethod
    def tearDownClass(cls) -> None:
        """fonction lancée une fois après tous les tests de la classe"""
        super().tearDownClass()
        # On détruit le Singleton Config
        Config._instance = None

    def test_find_upload(self) -> None:
        """Test find_upload."""
        o_u1 = Upload({"_id": "upload_1"})
        o_u2 = Upload({"_id": "upload_2"})
        # création du dataset
        o_mock_dataset = MagicMock()
        o_mock_dataset.data_files = {Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"}
        o_mock_dataset.md5_files = [Path("./a"), Path("./2")]
        o_mock_dataset.upload_infos = {"_id": "upload_base", "name": "upload_name"}
        o_mock_dataset.tags = {"tag1": "val1", "tag2": "val2"}
        o_mock_dataset.comments = ["comm1", "comm2", "comm3"]
        # exécution de UploadAction
        o_ua = UploadAction(o_mock_dataset)
        # Mock de ActionAbstract.get_filters et Upload.api_list
        with patch.object(ActionAbstract, "get_filters", return_value=({"info":"val"}, {"tag":"val"})) as o_mock_get_filters:
            with patch.object(Upload, "api_list", return_value=[o_u1, o_u2]) as o_mock_api_list :
                # Appel de la fonction find_upload
                o_upload = o_ua.find_upload("datastore_id")
                # Vérifications
                o_mock_get_filters.assert_called_once_with("upload", o_mock_dataset.upload_infos, o_mock_dataset.tags)
                o_mock_api_list.assert_called_once_with(infos_filter={"info":"val"}, tags_filter={"tag":"val"}, datastore="datastore_id")
                self.assertEqual(o_upload, o_u1)

    def run_args(
        self,
        behavior: Optional[str],
        return_value_find_upload: Optional[Upload],
        api_create: bool,
        api_delete: bool,
        run_fail: bool,
        message_exception: Optional[str] = None,
        files_on_api: Dict[str, int] = {},
        nb_data_files_on_api_ok: int = 0,
        nb_md5_files_on_api_ok: int = 0,
        comment_exist: bool = False,
        is_open: bool = True,
    ) -> None:
        """Lance le test UploadAction.run selon un cas de figure. Faire varier les paramètres permet de jouer sur le cas testé.
        Args:
            behavior (Optional[str]): mode lorsque la livraison existe déjà
            return_value_find_upload (Optional[Upload]): liste des upload retourné par le mock de Upload.api_list
            api_create (bool): vérification de l'exécution de Upload.api_create (True => api_create exécuté; False => api_create non exécuté)
            api_delete (bool): vérification de l'exécution de Upload.api_delete (True => api_delete exécuté; False => api_delete non exécuté)
            run_fail (bool): vérification de l'exécution avec erreur de UploadAction.run (True => run plant; False => run s'exécute sans erreur)
            message_exception (Optional[str]): si run_fail==True le message d'erreur attendu
            files_on_api (Dict[str, int]): liste des fichiers déjà livrés sur l'API et leur taille (SIZE_OK si ok)
            nb_data_files_on_api_ok (int): nombre fichiers de données déjà livrés sur l'API et à ne pas re-livrer
            nb_md5_files_on_api_ok (int): nombre fichiers de clé déjà livrés sur l'API et à ne pas re-livrer
            comment_exist (bool): si on a un commentaire qui existe déjà
            is_open (bool): si livraison ouverte
        """

        def create(d_dict: Dict[str, Any], route_params: Optional[Dict[str, Any]] = None) -> Upload:
            print("new creation")
            if route_params is None:
                route_params = {}
            d_dict["status"] = "OPEN"
            return Upload(d_dict, route_params.get("datastore", None))

        def config_get(a: str, b: str) -> Optional[str]:  # pylint:disable=invalid-name,unused-argument
            if b == "uniqueness_constraint_infos":
                return "name"
            if b == "uniqueness_constraint_tags":
                return ""
            if b == "behavior_if_exists":
                return "STOP"
            if b == "status_open":
                return "OPEN"
            raise Exception("cas non prévu", a, b)

        l_return_api_list_comments = [{"text": "commentaire existe"}] if comment_exist else []
        d_data_files : Dict[Path, str] = {Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"}
        l_md5_files: List[Path] = [Path("./a"), Path("./2")]
        d_upload_infos: Dict[str, str] = {"_id": "upload_base", "name": "upload_name"}
        d_tags: Dict[str, str] = {"tag1": "val1", "tag2": "val2"}
        l_comments: List[str] = ["comm1", "comm2", "comm3"]

        with patch.object(UploadAction, "find_upload", return_value=return_value_find_upload) as o_mock_find_upload, \
            patch.object(Upload, "api_create", wraps=create) as o_mock_api_create, \
            patch.object(Upload, "api_close", MagicMock()) as o_mock_close, \
            patch.object(Upload, "api_delete", MagicMock()) as o_mock_api_delete, \
            patch.object(Upload, "api_add_tags", MagicMock()) as o_mock_api_add_tags, \
            patch.object(Upload, "api_list_comments", return_value=l_return_api_list_comments) as o_mock_api_list_comments, \
            patch.object(Upload, "api_add_comment", MagicMock()) as o_mock_api_add_comment, \
            patch.object(Upload, "api_push_data_file", MagicMock()) as o_mock_api_push_data_file, \
            patch.object(Upload, "api_push_md5_file", MagicMock()) as o_mock_api_push_md5_file, \
            patch.object(Upload, "api_tree", MagicMock()) as o_mock_api_tree, \
            patch.object(UploadAction, "parse_tree", return_value=files_on_api) as o_mock_parse_tree, \
            patch.object(Upload, "api_update", return_value=None), \
            patch.object(Path, "stat") as o_mock_path_stat, \
            patch.object(Config, "get", wraps=config_get) \
        :
            # Mock de la fonction stat
            o_mock_path_stat.return_value.st_size = self.SIZE_OK
            # création du dataset
            o_mock_dataset = MagicMock()
            o_mock_dataset.data_files = d_data_files
            o_mock_dataset.md5_files = l_md5_files
            o_mock_dataset.upload_infos = d_upload_infos
            o_mock_dataset.tags = d_tags
            o_mock_dataset.comments = l_comments.copy()
            if comment_exist:
                o_mock_dataset.comments.append("commentaire existe")

            # exécution de UploadAction
            o_ua = UploadAction(o_mock_dataset, behavior)
            if run_fail:
                with self.assertRaises(GpfSdkError) as o_arc:
                    o_ua.run("datastore_id")
                self.assertEqual(o_arc.exception.message, message_exception)
                return
            o_ua.run("datastore_id")

            # vérif de o_mock_find_upload
            o_mock_find_upload.assert_called_once_with("datastore_id")

            # cas livraison fermé : aucune action
            if not is_open:
                o_mock_api_create.assert_not_called()
                o_mock_api_delete.assert_not_called()
                o_mock_api_add_tags.assert_not_called()
                o_mock_api_list_comments.assert_not_called()
                o_mock_api_add_comment.assert_not_called()
                o_mock_api_push_data_file.assert_not_called()
                o_mock_api_push_md5_file.assert_not_called()

                o_mock_api_tree.assert_not_called()
                o_mock_parse_tree.assert_not_called()
                o_mock_close.assert_not_called()
                return

            # vérif de o_mock_api_create
            if api_create:
                o_mock_api_create.assert_called_once_with(d_upload_infos, route_params={'datastore': 'datastore_id'})
            else:
                o_mock_api_create.assert_not_called()
            # vérif de o_mock_api_delete
            if api_delete:
                o_mock_api_delete.assert_called_once_with()
            else:
                o_mock_api_delete.assert_not_called()
            # vérif de o_mock_api_add_tags
            if d_tags is not None:
                o_mock_api_add_tags.assert_called_once_with(d_tags)
            else:
                o_mock_api_add_tags.assert_not_called()
            # vérif de o_mock_api_add_comment
            if l_comments is not None:
                o_mock_api_list_comments.assert_called_once_with()
                self.assertEqual(o_mock_api_add_comment.call_count, len(l_comments))
                for s_comment in l_comments:
                    o_mock_api_add_comment.assert_any_call({"text": s_comment})
            else:
                o_mock_api_add_comment.assert_not_called()
            # vérif de o_mock_api_push_data_file
            if len(d_data_files) == nb_data_files_on_api_ok:
                o_mock_api_push_data_file.assert_not_called()
            else:
                # appelée une fois par fichiers à livrer moins le nb de fichiers déjà livrés
                self.assertEqual(o_mock_api_push_data_file.call_count, len(d_data_files) - nb_data_files_on_api_ok)
                # appelée selon le Path des fichiers à livrer
                for p_file_path, s_api_path in d_data_files.items():
                    # S'il ne sont pas déjà livrés et avec la bonne taille
                    if files_on_api.get(f"data/{s_api_path}") != self.SIZE_OK:
                        o_mock_api_push_data_file.assert_any_call(p_file_path, s_api_path)
            # vérif de o_mock_api_push_md5_file
            if len(l_md5_files) == nb_md5_files_on_api_ok:
                o_mock_api_push_md5_file.assert_not_called()
            else:
                # appelée une fois par fichiers à livrer moins le nb de fichiers déjà livrés
                self.assertEqual(o_mock_api_push_md5_file.call_count, len(l_md5_files) - nb_md5_files_on_api_ok)
                # appelée selon le Path des fichiers à livrer
                for p_file_path in l_md5_files:
                    # S'il ne sont pas déjà livrés et avec la bonne taille
                    if files_on_api.get(p_file_path.name) != self.SIZE_OK:
                        o_mock_api_push_md5_file.assert_any_call(p_file_path)
            # vérif de o_mock_api_tree (appelée par UploadAction.__push_data_files et UploadAction.__push_md5_files)
            self.assertEqual(o_mock_api_tree.call_count, 2)
            # vérif de o_mock_parse_tree (appelée par UploadAction.__push_data_files et UploadAction.__push_md5_files)
            self.assertEqual(o_mock_parse_tree.call_count, 2)
            # vérif de o_mock_close
            o_mock_close.assert_called_once_with()


    def test_run(self) -> None:
        """Lance le test de UploadAction.run selon plusieurs cas de figures."""
        # tout mode sans doublon
        self.run_args(
            behavior=None,
            return_value_find_upload=None,
            api_create=True,
            api_delete=False,
            run_fail=False,
        )
        self.run_args(
            behavior="STOP",
            return_value_find_upload=None,
            api_create=True,
            api_delete=False,
            run_fail=False,
        )
        self.run_args(
            behavior="DELETE",
            return_value_find_upload=None,
            api_create=True,
            api_delete=False,
            run_fail=False,
        )
        self.run_args(
            behavior="CONTINUE",
            return_value_find_upload=None,
            api_create=True,
            api_delete=False,
            run_fail=False,
        )

        # mode stop mais avec doublon => ça plante
        o_return_value_find_upload = Upload({"_id": "upload_existant", "name": "Upload existant", "status": "OPEN"})
        self.run_args(
            behavior="STOP",
            return_value_find_upload=o_return_value_find_upload,
            api_create=True,
            api_delete=False,
            run_fail=True,
            message_exception=f"Impossible de créer la livraison, une livraison identique {o_return_value_find_upload} existe déjà.",
        )
        # mode DELETE mais avec doublon => suppression mais OK
        self.run_args(
            behavior="DELETE",
            return_value_find_upload = o_return_value_find_upload,
            api_create=True,
            api_delete=True,
            run_fail=False,
        )

        # mode CONTINUE mais avec doublon (ouvert) => pas suppression ni création
        self.run_args(
            behavior="CONTINUE",
            return_value_find_upload = o_return_value_find_upload,
            api_create=False,
            api_delete=False,
            run_fail=False,
        )

        # mode CONTINUE mais avec doublon (ouvert) et commentaire déjà présent
        self.run_args(
            behavior="CONTINUE",
            return_value_find_upload = o_return_value_find_upload,
            api_create=False,
            api_delete=False,
            run_fail=False,
            comment_exist=True
        )

        # mode CONTINUE mais avec doublon (fermé) => ça passe mais sans modifications
        o_return_value_find_upload = Upload({"_id": "upload_existant", "name": "Upload existant", "status": "CLOSE"})
        self.run_args(
            behavior="CONTINUE",
            return_value_find_upload=o_return_value_find_upload,
            api_create=False,
            api_delete=False,
            run_fail=False,
            is_open=False,
        )
        # mode CONTINUE mais avec doublon (ouvert) et commentaire déjà présent
        self.run_args(
            behavior="TOTO",
            return_value_find_upload = o_return_value_find_upload,
            run_fail=True,
            api_create = False,
            api_delete = False,
            message_exception="Le comportement TOTO n'est pas reconnu, l'exécution de traitement est annulée."
        )

    def test_monitor_until_end_ok(self) -> None:
        """Vérifie le bon fonctionnement de monitor_until_end si à la fin c'est ok."""
        # 3 réponses possibles pour api_list_checks : il faut attendre sur les 2 premières; tout est ok sur la troisième.
        d_list_checks_wait_1 = {"asked": [{}, {}],"in_progress": [],"passed": [],"failed": []}
        d_list_checks_wait_2 = {"asked": [{}],"in_progress": [{}],"passed": [],"failed": []}
        d_list_checks_ok = {"asked": [],"in_progress": [],"passed": [{},{}],"failed": []}
        # On patch la fonction api_list_checks de l'upload
        # elle renvoie une liste avec des traitements en attente 2 fois puis une liste avec que des succès
        l_returns = [d_list_checks_wait_1, d_list_checks_wait_2, d_list_checks_ok]
        with patch.object(Upload, "api_list_checks", side_effect=l_returns) as o_mock_list_checks:
            # On instancie un Upload
            o_upload = Upload({"_id": "id_upload_monitor"})
            # On instancie un faux callback
            f_callback = MagicMock()
            f_ctrl_c = MagicMock(return_value=False)
            # On effectue le monitoring
            b_result = UploadAction.monitor_until_end(o_upload, f_callback, f_ctrl_c)
            # Vérification sur o_mock_list_checks et f_callback: ont dû être appelés 3 fois
            self.assertEqual(o_mock_list_checks.call_count, 3)
            self.assertEqual(f_callback.call_count, 3)
            f_callback.assert_any_call("Vérifications : 2 en attente, 0 en cours, 0 en échec, 0 en succès")
            f_callback.assert_any_call("Vérifications : 1 en attente, 1 en cours, 0 en échec, 0 en succès")
            f_callback.assert_any_call("Vérifications : 0 en attente, 0 en cours, 0 en échec, 2 en succès")
            # Vérification sur f_ctrl_c : n'a pas dû être appelée
            f_ctrl_c.assert_not_called()
            # Vérifications sur b_result : doit être finalement ok
            self.assertTrue(b_result)

    def test_monitor_until_end_ko(self) -> None:
        """Vérifie le bon fonctionnement de monitor_until_end si à la fin c'est ko."""
        # 3 réponses possibles pour api_list_checks : il faut attendre sur les 2 premières; il y a un pb sur la troisième.
        d_list_checks_wait_1 = {"asked": [{}, {}],"in_progress": [],"passed": [],"failed": []}
        d_list_checks_wait_2 = {"asked": [{}],"in_progress": [{}],"passed": [],"failed": []}
        d_list_checks_ko = {"asked": [],"in_progress": [],"passed": [{}],"failed": [{}]}
        # On patch la fonction api_list_checks de l'upload
        # elle renvoie une liste avec des traitements en attente 2 fois puis une liste avec des erreurs
        l_returns = [d_list_checks_wait_1, d_list_checks_wait_2, d_list_checks_ko]
        with patch.object(Upload, "api_list_checks", side_effect=l_returns) as o_mock_list_checks:
            # On instancie un Upload
            o_upload = Upload({"_id": "id_upload_monitor"})
            # On instancie un faux callback
            f_callback = MagicMock()
            f_ctrl_c = MagicMock(return_value=False)
            # On effectue le monitoring
            b_result = UploadAction.monitor_until_end(o_upload, f_callback, f_ctrl_c)
            # Vérification sur o_mock_list_checks et f_callback: ont dû être appelés 3 fois
            self.assertEqual(o_mock_list_checks.call_count, 3)
            self.assertEqual(f_callback.call_count, 3)
            f_callback.assert_any_call("Vérifications : 2 en attente, 0 en cours, 0 en échec, 0 en succès")
            f_callback.assert_any_call("Vérifications : 1 en attente, 1 en cours, 0 en échec, 0 en succès")
            f_callback.assert_any_call("Vérifications : 0 en attente, 0 en cours, 1 en échec, 1 en succès")
            # Vérification sur f_ctrl_c : n'a pas dû être appelée
            f_ctrl_c.assert_not_called()
            # Vérifications sur b_result : doit être finalement ko
            self.assertFalse(b_result)

    def test_interrupt_monitor_until_end(self) -> None:
        """Vérifie le bon fonctionnement de monitor_until_end si il y a interruption en cours de route."""
        # tout déjà traité
        with patch.object(Upload, "api_list_checks", side_effect=[KeyboardInterrupt(), {"asked":[], "in_progress": []}] ) as o_mock_list_checks:
            with patch.object(Upload, "api_open") as o_mock_api_open:
                # On instancie un Upload
                o_upload = Upload({"_id": "id_upload_monitor"})
                # On instancie un faux callback
                f_callback = MagicMock()
                f_ctrl_c = MagicMock(return_value=True)
                # On effectue le monitoring
                with self.assertRaises(KeyboardInterrupt):
                    UploadAction.monitor_until_end(o_upload, f_callback, f_ctrl_c)

            # Vérification sur les appels de fonction
            self.assertEqual(2, o_mock_list_checks.call_count)
            f_ctrl_c.assert_called_once_with()
            o_mock_api_open.assert_not_called()
        # tout traitement en cours
        with patch.object(Upload, "api_list_checks", side_effect=[KeyboardInterrupt(), {"asked":[], "in_progress": [{'_id': "1"}, {'_id': "2"}]}] ) as o_mock_list_checks:
            with patch.object(CheckExecution, "api_delete") as o_mock_delete:
                with patch.object(Upload, "api_open") as o_mock_api_open:
                    # On instancie un Upload
                    o_upload = Upload({"_id": "id_upload_monitor"})
                    # On instancie un faux callback
                    f_callback = MagicMock()
                    f_ctrl_c = MagicMock(return_value=True)
                    # On effectue le monitoring
                    with self.assertRaises(KeyboardInterrupt):
                        UploadAction.monitor_until_end(o_upload, f_callback, f_ctrl_c)

            # Vérification sur les appels de fonction
            self.assertEqual(2, o_mock_list_checks.call_count)
            self.assertEqual(2, o_mock_delete.call_count)
            f_ctrl_c.assert_called_once_with()
            o_mock_api_open.assert_called_once_with()
        # traitement en cours et en attente
        o_mock_1 = MagicMock()
        o_mock_1.__getitem__.side_effect = ["WAITING", "WAITING", "PROGRESS", "PROGRESS"]
        o_mock_1.api_update.return_value = None
        o_mock_1.api_delete.return_value = None
        o_mock_2 = MagicMock()
        o_mock_2.__getitem__.side_effect = ["WAITING", "WAITING", "FAIL", "FAIL"]
        o_mock_2.api_update.return_value = None
        o_mock_2.api_delete.return_value = None
        with patch.object(Upload, "api_list_checks", side_effect=[KeyboardInterrupt(), {"asked":[{'_id': "3"}, {'_id': "4"}], "in_progress": [{'_id': "1"}, {'_id': "2"}]}] ) as o_mock_list_checks:
            with patch.object(CheckExecution, "api_delete") as o_mock_delete:
                with patch.object(CheckExecution, "api_get", side_effect=[o_mock_1, o_mock_2]) as o_mock_get:
                    with patch.object(Upload, "api_open") as o_mock_api_open:
                        # On instancie un Upload
                        o_upload = Upload({"_id": "id_upload_monitor"}, "test")
                        # On instancie un faux callback
                        f_callback = MagicMock()
                        f_ctrl_c = MagicMock(return_value=True)
                        # On effectue le monitoring
                        with self.assertRaises(KeyboardInterrupt):
                            UploadAction.monitor_until_end(o_upload, f_callback, f_ctrl_c)

            # Vérification sur les appels de fonction
            self.assertEqual(2, o_mock_list_checks.call_count)
            self.assertEqual(2, o_mock_delete.call_count)
            self.assertEqual(2, o_mock_get.call_count)
            o_mock_get.assert_any_call("3", "test")
            o_mock_get.assert_any_call("4", "test")
            f_ctrl_c.assert_called_once_with()
            o_mock_api_open.assert_called_once_with()
            self.assertEqual(2, o_mock_1.api_update.call_count)
            self.assertEqual(2, o_mock_2.api_update.call_count)
            o_mock_1.api_delete.assert_called_once_with()
            o_mock_2.api_delete.assert_not_called()

    def test_api_tree_not_empty(self) -> None:
        """Vérifie le bon fonctionnement de api_tree si ce n'est pas vide."""
        # Arborescence en entrée
        l_tree: List[Dict[str, Any]] = [
            {
                "name": "data",
                "children": [
                    {
                        "name": "toto",
                        "children": [
                            {
                                "name": "titi",
                                "children": [
                                    {
                                        "name": "fichier_2.pdf",
                                        "size": 467717,
                                        "extension": ".pdf",
                                        "type": "file",
                                    }
                                ],
                                "size": 467717,
                                "type": "directory",
                            },
                            {
                                "name": "fichier_1.pdf",
                                "size": 300000,
                                "extension": ".pdf",
                                "type": "file",
                            },
                        ],
                        "size": 767717,
                        "type": "directory",
                    }
                ],
                "size": 767717,
                "type": "directory",
            },
            {"name": "md5sum.md5", "size": 78, "extension": ".md5", "type": "file"},
        ]
        # Valeurs attendues
        d_files_wanted: Dict[str, int] = {
            "data/toto/titi/fichier_2.pdf": 467717,
            "data/toto/fichier_1.pdf": 300000,
            "md5sum.md5": 78,
        }
        # Parsing
        d_files = UploadAction.parse_tree(l_tree)
        # Vérification
        self.assertDictEqual(d_files, d_files_wanted)

    def test_api_tree_empty(self) -> None:
        """Vérifie le bon fonctionnement de api_tree si c'est vide."""
        # Arborescence en entrée
        l_tree: List[Dict[str, Any]] = []
        # Valeurs attendues
        d_files_wanted: Dict[str, int] = {}
        # Parsing
        d_files = UploadAction.parse_tree(l_tree)
        # Vérification
        self.assertDictEqual(d_files, d_files_wanted)
