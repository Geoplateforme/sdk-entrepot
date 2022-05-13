from typing import Any, Dict, List, Optional
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ignf_gpf_api.action.UploadAction import UploadAction
from ignf_gpf_api.store.Upload import Upload
from ignf_gpf_api.io.Config import Config
from ignf_gpf_api.Errors import GpfApiError

# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
# pylint:disable=too-many-branches
# fmt: off
# (on désactive le formatage en attendant Python 3.10 et la possibilité de mettre des parenthèses pour gérer le multi with proprement)


class UploadActionTestCase(unittest.TestCase):
    """Tests UploadAction class.

    cmd : python3 -m unittest -b tests.action.UploadActionTestCase
    """

    def run_args(
        self,
        behavior: Optional[str],
        return_value_api_list: List[Upload],
        list_api: Dict[str, Dict[str, str]],
        api_create: bool,
        api_delete: bool,
        run_fail: bool,
        data_files: Dict[Path, str],
        md5_files: List[Path],
        upload_infos: Dict[str, Any],
        tags: Dict[str, str],
        comments: List[str],
    ) -> None:
        """Lance le test UploadAction.run selon un cas de figure. Faire varier les paramètres permet de jouer sur le cas testé.

        Args:
            behavior (Optional[str]): _description_
            return_value_api_list (List[Upload]): _description_
            list_api (Dict[str, Dict[str, str]]): _description_
            api_create (bool): _description_
            api_delete (bool): _description_
            run_fail (bool): _description_
            data_files (Dict[Path, str]): _description_
            md5_files (List[Path]): _description_
            upload_infos (Dict[str, Any]): _description_
            tags (Dict[str, str]): _description_
            comments (List[str]): _description_
        """

        def create(d_dict: Dict[str, Any]) -> Upload:
            print("new creation")
            d_dict["status"] = "OPEN"
            return Upload(d_dict)

        def config_get(a: str, b: str) -> Optional[str]:  # pylint:disable=invalid-name,unused-argument
            if b == "uniqueness_constraint_upload_infos":
                return "name"
            if b == "uniqueness_constraint_tags":
                return ""
            if b == "behavior_if_exists":
                return "STOP"
            if b == "open_status":
                return "OPEN"
            raise Exception("cas non prévu", a, b)

        with patch.object(Upload, "api_list", return_value=return_value_api_list) as o_mock_api_list, \
            patch.object(Upload, "api_create", wraps=create) as o_mock_api_create, \
            patch.object(Upload, "api_close", MagicMock()) as o_mock_close, \
            patch.object(Upload, "api_delete", MagicMock()) as o_mock_api_delete, \
            patch.object(Upload, "api_add_tags", MagicMock()) as o_mock_api_add_tags, \
            patch.object(Upload, "api_add_comment", MagicMock()) as o_mock_api_add_comment, \
            patch.object(Upload, "api_push_data_file", MagicMock()) as o_mock_api_push_data_file, \
            patch.object(Upload, "api_push_md5_file", MagicMock()) as o_mock_api_push_md5_file, \
            patch.object(Config, "get", wraps=config_get) \
        :
            # création du dataset
            o_mock_dataset = MagicMock()
            o_mock_dataset.data_files = data_files
            o_mock_dataset.md5_files = md5_files
            o_mock_dataset.upload_infos = upload_infos
            o_mock_dataset.tags = tags
            o_mock_dataset.comments = comments
            # exécution de UploadAction
            o_ua = UploadAction(o_mock_dataset, behavior)
            if run_fail:
                with self.assertRaises(GpfApiError) as o_arc:
                    o_ua.run()
                self.assertEqual(o_arc.exception.message, f"Impossible de créer la livraison, une livraison identique {return_value_api_list[0]} existe déjà.")
                return
            o_ua.run()

            # vérif de o_mock_api_list
            o_mock_api_list.assert_called_once_with(**list_api)

            # vérif de o_mock_api_create
            if api_create:
                o_mock_api_create.assert_called_once_with(upload_infos)
            else:
                o_mock_api_create.assert_not_called()

            # vérif de o_mock_api_delete
            if api_delete:
                o_mock_api_delete.assert_called_once_with()
            else:
                o_mock_api_delete.assert_not_called()

            # vérif de o_mock_api_add_tags
            if tags is not None:
                o_mock_api_add_tags.assert_called_once_with(tags)
            else:
                o_mock_api_add_tags.assert_not_called()

            # vérif de o_mock_api_add_comment
            if comments is not None:
                assert o_mock_api_add_comment.call_count == len(comments)
                for s_comment in comments:
                    o_mock_api_add_comment.assert_any_call({"text": s_comment})
            else:
                o_mock_api_add_comment.assert_not_called()

            # vérif de o_mock_api_push_data_file
            assert o_mock_api_push_data_file.call_count == len(data_files)
            for p_file_path, s_api_path in data_files.items():
                o_mock_api_push_data_file.assert_any_call(p_file_path, s_api_path)

            # vérif de o_mock_api_push_md5_file
            assert o_mock_api_push_md5_file.call_count == len(md5_files)
            for p_file_path in md5_files:
                o_mock_api_push_md5_file.assert_any_call(p_file_path)

            # vérif de o_mock_close
            o_mock_close.assert_called_once_with()

    def test_run(self) -> None:
        """Lance le test de UploadAction.run selon plusieurs cas de figures."""
        self.run_args(
            behavior=None,
            return_value_api_list=[],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=True,
            api_delete=False,
            run_fail=False,
        )
        # tout mode sans doublon
        self.run_args(
            behavior="STOP",
            return_value_api_list=[],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=True,
            api_delete=False,
            run_fail=False,
        )
        self.run_args(
            behavior="DELETE",
            return_value_api_list=[],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=True,
            api_delete=False,
            run_fail=False,
        )
        self.run_args(
            behavior="CONTINUE",
            return_value_api_list=[],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=True,
            api_delete=False,
            run_fail=False,
        )

        # mode stop mais avec doublon => ça plante
        self.run_args(
            behavior="STOP",
            return_value_api_list=[Upload({"_id": "upload_existant", "name": "Upload existant", "status": "OPEN"})],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=True,
            api_delete=False,
            run_fail=True,
        )
        # mode DELETE mais avec doublon => suppression mais OK
        self.run_args(
            behavior="DELETE",
            return_value_api_list=[Upload({"_id": "upload_existant", "name": "Upload existant", "status": "OPEN"})],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=True,
            api_delete=True,
            run_fail=False,
        )

        # mode CONTINUE mais avec doublon => pas suppression ni création
        self.run_args(
            behavior="CONTINUE",
            return_value_api_list=[Upload({"_id": "upload_existant", "name": "Upload existant", "status": "OPEN"})],
            data_files={Path("./a"): "a", Path("./b"): "b", Path("./c"): "c"},
            md5_files=[Path("./a"), Path("./2")],
            upload_infos={"_id": "upload_base", "name": "upload_name"},
            tags={"tag1": "val1", "tag2": "val2"},
            comments=["comm1", "comm2", "comm3"],
            list_api={"infos_filter": {"name": "upload_name"}, "tags_filter": {}},
            api_create=False,
            api_delete=False,
            run_fail=False,
        )
