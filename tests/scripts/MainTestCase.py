from pathlib import Path
import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from sdk_entrepot_gpf.Errors import GpfSdkError
from sdk_entrepot_gpf.scripts.run import Main
from sdk_entrepot_gpf.io.Config import Config
from tests.GpfTestCase import GpfTestCase


class MainTestCase(GpfTestCase):
    """Tests Main class.

    cmd : python3 -m unittest -b tests.scripts.MainTestCase
    """

    datastore = "data"

    def test_parse_args(self) -> None:
        """Vérifie le bon fonctionnement de parse_args."""
        # Sans rien, ça quitte en erreur
        with self.assertRaises(SystemExit) as o_arc:
            Main.parse_args(args=[])
        self.assertEqual(o_arc.exception.code, 2)

        # Avec --help, ça quitte en succès
        with self.assertRaises(SystemExit) as o_arc:
            Main.parse_args(args=["--help"])
        self.assertEqual(o_arc.exception.code, 0)

        # Avec --version, ça quitte en succès
        with self.assertRaises(SystemExit) as o_arc:
            Main.parse_args(args=["--version"])
        self.assertEqual(o_arc.exception.code, 0)

    def test_parse_args_auth(self) -> None:
        """Vérifie le bon fonctionnement de parse_args."""
        # Avec tâche="auth" seul, c'est ok
        o_args = Main.parse_args(args=["auth"])
        self.assertEqual(o_args.task, "auth")
        self.assertIsNone(o_args.show)

        # Avec tâche="auth" et show="token", c'est ok
        o_args = Main.parse_args(args=["auth", "token"])
        self.assertEqual(o_args.task, "auth")
        self.assertEqual(o_args.show, "token")

        # Avec tâche "auth" et show="header", c'est ok
        o_args = Main.parse_args(args=["auth", "header"])
        self.assertEqual(o_args.task, "auth")
        self.assertEqual(o_args.show, "header")

    def test_parse_args_config(self) -> None:
        """Vérifie le bon fonctionnement de parse_args."""
        # Avec tâche="config" seul, c'est ok
        o_args = Main.parse_args(args=["config"])
        self.assertEqual(o_args.task, "config")
        self.assertIsNone(o_args.file)
        self.assertIsNone(o_args.section)
        self.assertIsNone(o_args.option)

        # Avec tâche="config" et file="toto.ini", c'est ok
        o_args = Main.parse_args(args=["config", "--file", "toto.ini"])
        self.assertEqual(o_args.task, "config")
        self.assertEqual(o_args.file, "toto.ini")
        self.assertIsNone(o_args.section)
        self.assertIsNone(o_args.option)

        # Avec tâche "config", file="toto.ini" et section="store_authentification", c'est ok
        o_args = Main.parse_args(args=["config", "--file", "toto.ini", "store_authentification"])
        self.assertEqual(o_args.task, "config")
        self.assertEqual(o_args.file, "toto.ini")
        self.assertEqual(o_args.section, "store_authentification")
        self.assertIsNone(o_args.option)

        # Avec tâche "config", section="store_authentification", c'est ok
        o_args = Main.parse_args(args=["config", "store_authentification"])
        self.assertEqual(o_args.task, "config")
        self.assertIsNone(o_args.file)
        self.assertEqual(o_args.section, "store_authentification")
        self.assertIsNone(o_args.option)

        # Avec tâche "config", section="store_authentification" et option="password", c'est ok
        o_args = Main.parse_args(args=["config", "store_authentification", "password"])
        self.assertEqual(o_args.task, "config")
        self.assertIsNone(o_args.file)
        self.assertEqual(o_args.section, "store_authentification")
        self.assertEqual(o_args.option, "password")

    def run_test_init(self, params: Any, res: Dict[str, Any], fichier_config: str) -> None:
        """Vérifie le bon fonctionnement de l'init.

        Args:
            params (Any): paramétres de la méthode Main.parse_args()
            res (Dict[str, Any]): dict contant les fonction lancées et leurs arguments
            fichier_config (str): fichier de configuration utilisé
        """
        d_mock_fun = {}
        # On mock la méthode Main.xxx()
        # fmt: off
        with patch.object(Main, "parse_args", return_value=params) , \
            patch.object(Path, "exists", return_value=True), \
            patch.object(Config, "read") as d_mock_read, \
            patch.object(Main, "_Main__datastore", return_value=self.datastore), \
            patch.object(Main, "auth") as d_mock_fun["auth"], \
            patch.object(Main, "config") as d_mock_fun["config"], \
            patch.object(Main, "me_") as d_mock_fun["me_"], \
            patch.object(Main, "workflow") as d_mock_fun["workflow"], \
            patch.object(Main, "dataset") as d_mock_fun["dataset"], \
            patch.object(Main, "delete") as d_mock_fun["delete"], \
            patch.object(Main, "upload") as d_mock_fun["upload"], \
            patch.object(Main, "annexe") as d_mock_fun["annexe"], \
            patch.object(Main, "static") as d_mock_fun["static"], \
            patch.object(Main, "metadata") as d_mock_fun["metadata"], \
            patch.object(Main, "key") as d_mock_fun["key"]:
            # on mock les classes
            with patch("sdk_entrepot_gpf.scripts.example.Example.__init__", return_value=None) as d_mock_fun["Example"], \
                patch("sdk_entrepot_gpf.scripts.resolve.ResolveCli.__init__", return_value=None) as d_mock_fun["ResolveCli"], \
                patch("sdk_entrepot_gpf.scripts.workflow.WorkflowCli.__init__", return_value=None) as d_mock_fun["WorkflowCli"], \
                patch("sdk_entrepot_gpf.scripts.delivery.Delivery.__init__", return_value=None) as d_mock_fun["Delivery"], \
                patch("sdk_entrepot_gpf.scripts.entities.Entities.__init__", return_value=None) as d_mock_fun["Entities"]:
                Main('TOTO')
        # fmt: on
        d_mock_read.assert_called_once_with(fichier_config)
        for s_key, o_mock in d_mock_fun.items():
            if s_key not in res:
                o_mock.assert_not_called()
            else:
                o_mock.assert_called_once_with(*res[s_key].get("args", ()), **res[s_key].get("kwargs", {}))

    def test_run(self) -> None:
        """Vérifie le bon fonctionnement de run."""

        # on vérifie que le programme sort bien en erreur si le fichier de configuration n'existe pas
        o_params = MagicMock()
        with patch.object(Path, "exists", return_value=False) as o_mock_exists:
            with patch.object(Main, "parse_args", return_value=o_params):
                with self.assertRaises(GpfSdkError) as o_arc:
                    Main()
                o_mock_exists.assert_called_once_with()
                self.assertEqual(o_arc.exception.message, f"Le fichier de configuration précisé ({o_params.config}) n'existe pas.")

        with patch.object(os, "environ", {}):
            with self.subTest("Default config_file sans env + auth"):
                o_params = MagicMock(
                    config="--default--",
                    task="auth",
                )
                self.run_test_init(o_params, {"auth": {}}, "config.ini")

            with self.subTest("param config_file sans env + me"):
                o_params = MagicMock(
                    config="toto.ini",
                    task="me",
                )
                self.run_test_init(o_params, {"me_": {}}, "toto.ini")

        with patch.object(os, "environ", {"SDK_ENTREPOT_CONFIG_FILE": "tutu.ini"}):
            with self.subTest("Default config_file avec env + config"):
                o_params = MagicMock(
                    config="--default--",
                    task="config",
                )
                self.run_test_init(o_params, {"config": {}}, "tutu.ini")
            with self.subTest("param config_file avec env + example"):
                o_params = MagicMock(
                    config="toto.ini",
                    task="example",
                    type="type_params",
                    name="nom_params",
                    output="output_params",
                )
                self.run_test_init(o_params, {"Example": {"args": (o_params.type, o_params.name, o_params.output)}}, "toto.ini")

        with self.subTest("resolve"):
            o_params = MagicMock(config="toto.ini", task="resolve", params=[("datastore", "data"), ("resolve", "resolve_url")])
            d_params = {x[0]: x[1] for x in o_params.params}
            self.run_test_init(o_params, {"ResolveCli": {"args": [o_params.datastore, o_params.resolve, d_params]}}, "toto.ini")

        with self.subTest("workflow - workflow"):
            o_params = MagicMock(config="toto.ini", task="workflow")
            self.run_test_init(o_params, {"workflow": {}}, "toto.ini")

        with self.subTest("workflow - WorkflowCli"):
            o_params = MagicMock(config="toto.ini", task="workflow", file="file", params=[("datastore", "data"), ("resolve", "resolve_url")], tags=[("key1", "val1"), ("key2", "val2")])
            o_params.name = None
            d_params = {x[0]: x[1] for x in o_params.params}
            d_tags = {l_el[0]: l_el[1] for l_el in o_params.tags}
            self.run_test_init(o_params, {"WorkflowCli": {"args": [o_params.datastore, o_params.file, o_params.behavior, o_params.step, d_params, d_tags, o_params.comments]}}, "toto.ini")

        with self.subTest("delivery"):
            o_params = MagicMock(config="toto.ini", task="delivery")
            self.run_test_init(o_params, {"Delivery": {"args": [self.datastore, o_params.file, o_params.behavior, o_params.check_before_close, o_params.mode_cartes]}}, "toto.ini")

        for s_task in ["dataset", "delete"]:
            with self.subTest(s_task):
                o_params = MagicMock(config="toto.ini", task=s_task)
                self.run_test_init(o_params, {s_task: {}}, "toto.ini")

        with self.subTest("Entities"):
            o_params = MagicMock(config="toto.ini", task="Entities", file=None)
            self.run_test_init(o_params, {"Entities": {"args": [self.datastore, o_params.task, o_params.id, o_params]}}, "toto.ini")

        for s_task in ["upload", "annexe", "static", "metadata", "key"]:
            with self.subTest(s_task):
                o_params = MagicMock(config="toto.ini", task=s_task)
                self.run_test_init(o_params, {s_task: {}, "Entities": {"args": [self.datastore, o_params.task, o_params.id, o_params]}}, "toto.ini")
