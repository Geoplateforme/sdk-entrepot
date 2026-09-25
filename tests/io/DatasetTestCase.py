import os
import tempfile
from pathlib import Path

from sdk_entrepot_gpf.helper.FileHelper import FileHelper
from sdk_entrepot_gpf.helper.JsonHelper import JsonHelper
from sdk_entrepot_gpf.io.Dataset import Dataset

from tests.GpfTestCase import GpfTestCase


class DatasetTestCase(GpfTestCase):
    """Test de la classe Dataset.

    cmd : python3 -m unittest -b tests.io.DatasetTestCase
    """

    def test_init(self) -> None:
        """Test du constructeur."""
        self.maxDiff = None
        # Ouverture et chemins
        p_descriptor = GpfTestCase.data_dir_path / "datasets" / "3_test_dataset_sub_dir" / "upload_descriptor.json"
        p_root = p_descriptor.parent
        d_descriptor = JsonHelper.load(p_descriptor)
        d_dataset = d_descriptor["datasets"][0]
        p_md5 = p_root / "CANTON.md5"
        # Suppression du fichier md5 (les tests doivent le régénérer)
        p_md5.unlink(missing_ok=True)
        self.assertFalse(p_md5.exists(), "CANTON.md5 existe")
        # Instanciation
        o_dataset = Dataset(d_dataset, p_root)
        # Vérifications
        self.assertEqual(o_dataset.data_dirs, [Path(i) for i in d_dataset["data_dirs"]])
        self.assertDictEqual(o_dataset.upload_infos, d_dataset["upload_infos"])
        self.assertListEqual(o_dataset.comments, d_dataset["comments"])
        self.assertDictEqual(o_dataset.tags, d_dataset["tags"])
        self.assertDictEqual(
            o_dataset.data_files,
            {
                p_root / "CANTON/CANTON.shx": "CANTON",
                p_root / "CANTON/CANTON.dbf": "CANTON",
                p_root / "CANTON/CANTON.shp": "CANTON",
                p_root / "CANTON/CANTON.cpg": "CANTON",
                p_root / "CANTON/CANTON.prj": "CANTON",
                p_root / "CANTON/sous_dossier/coucou.txt": "CANTON/sous_dossier",
            },
        )
        self.assertEqual(o_dataset.md5_files, [p_root / "CANTON.md5"])
        self.assertTrue(p_md5.exists(), "CANTON.md5 n'existe pas")
        s_data_md5 = p_md5.read_text(encoding="UTF-8")
        for p_file in o_dataset.data_files:
            s_md5 = FileHelper.md5_hash(p_file)
            s_line = f"{s_md5}  {p_file.relative_to(p_root).as_posix()}"
            self.assertIn(s_line, s_data_md5)

    def test_init_with_file(self) -> None:
        """Test du constructeur avec un data_dirs pointant directement sur un fichier (et non un dossier)."""
        self.maxDiff = None
        # Ouverture et chemins
        p_descriptor = GpfTestCase.data_dir_path / "datasets" / "4_test_dataset_file" / "upload_descriptor.json"
        p_root = p_descriptor.parent
        d_descriptor = JsonHelper.load(p_descriptor)
        d_dataset = d_descriptor["datasets"][0]
        p_md5 = p_root / "standalone.txt.md5"
        # Suppression du fichier md5 (les tests doivent le régénérer)
        p_md5.unlink(missing_ok=True)
        self.assertFalse(p_md5.exists(), "standalone.txt.md5 existe")
        # Instanciation
        o_dataset = Dataset(d_dataset, p_root)
        # Vérifications
        self.assertEqual(o_dataset.data_dirs, [Path(i) for i in d_dataset["data_dirs"]])
        self.assertDictEqual(
            o_dataset.data_files,
            {p_root / "standalone.txt": "."},
        )
        self.assertEqual(o_dataset.md5_files, [p_root / "standalone.txt.md5"])
        self.assertTrue(p_md5.exists(), "standalone.txt.md5 n'existe pas")
        s_data_md5 = p_md5.read_text(encoding="UTF-8")
        s_md5 = FileHelper.md5_hash(p_root / "standalone.txt")
        self.assertIn(f"{s_md5}  standalone.txt", s_data_md5)
        os.remove(p_md5)

    def test_init_with_invalid_data_dir(self) -> None:
        """Test du constructeur avec un data_dirs introuvable."""
        p_root = GpfTestCase.data_dir_path / "datasets" / "3_test_dataset_sub_dir"
        d_dataset = {"data_dirs": ["missing_dir"], "upload_infos": {}, "comments": [], "tags": {}}

        with self.assertRaises(FileNotFoundError):
            Dataset(d_dataset, p_root)

    def test_init_with_data_dir_outside_root(self) -> None:
        """Test du constructeur avec un data_dirs hors du dossier racine."""
        with tempfile.TemporaryDirectory() as s_tmp_dir:
            p_root = Path(s_tmp_dir) / "root"
            p_root.mkdir()
            p_outside = Path(s_tmp_dir) / "outside.txt"
            p_outside.write_text("outside", encoding="utf-8")
            d_dataset = {"data_dirs": ["../outside.txt"], "upload_infos": {}, "comments": [], "tags": {}}

            with self.assertRaises(ValueError):
                Dataset(d_dataset, p_root)

    def test_init_with_symlinked_subdir_outside_root(self) -> None:
        """Test du constructeur avec un sous-dossier symbolique pointant hors du dossier racine."""
        with tempfile.TemporaryDirectory() as s_tmp_dir:
            p_root = Path(s_tmp_dir) / "root"
            p_root.mkdir()
            p_a_file = p_root / "a/file.txt"
            p_b_file = p_root / "b/file.txt"
            p_a_file.parent.mkdir()
            p_b_file.parent.mkdir()
            p_a_file.write_text("a", encoding="utf-8")
            p_b_file.write_text("b", encoding="utf-8")
            p_data_dir = p_root / "data"
            p_data_dir.mkdir()
            p_outside_dir = Path(s_tmp_dir) / "outside"
            p_outside_dir.mkdir()
            (p_outside_dir / "secret.txt").write_text("secret", encoding="utf-8")
            p_link = p_data_dir / "linked"
            try:
                p_link.symlink_to(p_outside_dir, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("La création de liens symboliques n'est pas disponible.")
            d_dataset = {"data_dirs": ["data/linked"], "upload_infos": {}, "comments": [], "tags": {}}
            with self.assertRaises(ValueError):
                Dataset(d_dataset, p_root)
            self.assertFalse((p_a_file.parent / "file.txt.md5").exists())
            self.assertFalse((p_b_file.parent / "file.txt.md5").exists())
            os.remove(p_link)

    def test_init_with_symlinked_subdir_inside_root_keeps_symlink_path(self) -> None:
        """Test du constructeur avec un sous-dossier symbolique interne au dossier racine."""
        with tempfile.TemporaryDirectory() as s_tmp_dir:
            p_root = Path(s_tmp_dir) / "root"
            p_root.mkdir()
            p_real_dir = p_root / "data/real"
            p_real_dir.mkdir(parents=True)
            (p_real_dir / "secret.txt").write_text("secret", encoding="utf-8")
            p_nested_dir = p_real_dir / "nested"
            p_nested_dir.mkdir()
            p_nested_file = p_nested_dir / "child.txt"
            p_nested_file.write_text("child", encoding="utf-8")
            p_link = p_root / "data/linked"
            try:
                p_link.symlink_to(p_real_dir, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("La création de liens symboliques n'est pas disponible.")
            d_dataset = {"data_dirs": ["data/linked"], "upload_infos": {}, "comments": [], "tags": {}}

            o_dataset = Dataset(d_dataset, p_root)

            self.assertDictEqual(
                o_dataset.data_files,
                {
                    p_root / "data/linked/secret.txt": "data/linked",
                    p_root / "data/linked/nested/child.txt": "data/linked/nested",
                },
            )
            self.assertEqual(o_dataset.md5_files, [p_root / "data/linked.md5"])
            s_data_md5 = o_dataset.md5_files[0].read_text(encoding="UTF-8")
            s_md5 = FileHelper.md5_hash(p_real_dir / "secret.txt")
            self.assertIn(f"{s_md5}  data/linked/secret.txt", s_data_md5)
            s_nested_md5 = FileHelper.md5_hash(p_nested_file)
            self.assertIn(f"{s_nested_md5}  data/linked/nested/child.txt", s_data_md5)

    def test_init_with_symlinked_file_inside_root_keeps_symlink_path(self) -> None:
        """Test du constructeur avec un fichier symbolique interne au dossier racine."""
        with tempfile.TemporaryDirectory() as s_tmp_dir:
            p_root = Path(s_tmp_dir) / "root"
            p_root.mkdir()
            p_real_dir = p_root / "real"
            p_real_dir.mkdir()
            p_real_file = p_real_dir / "secret.txt"
            p_real_file.write_text("secret", encoding="utf-8")
            p_data_dir = p_root / "data"
            p_data_dir.mkdir()
            p_link = p_data_dir / "alias.txt"
            try:
                p_link.symlink_to(p_real_file)
            except (NotImplementedError, OSError):
                self.skipTest("La création de liens symboliques n'est pas disponible.")
            d_dataset = {"data_dirs": ["data"], "upload_infos": {}, "comments": [], "tags": {}}

            o_dataset = Dataset(d_dataset, p_root)

            self.assertDictEqual(
                o_dataset.data_files,
                {
                    p_link: "data",
                },
            )
            self.assertEqual(o_dataset.md5_files, [p_root / "data.md5"])
            s_data_md5 = o_dataset.md5_files[0].read_text(encoding="UTF-8")
            s_md5 = FileHelper.md5_hash(p_real_file)
            self.assertIn(f"{s_md5}  data/alias.txt", s_data_md5)

    def test_init_with_file_md5_name_collision(self) -> None:
        """Test du constructeur avec deux fichiers générant le même nom de md5 distant."""
        with tempfile.TemporaryDirectory() as s_tmp_dir:
            p_root = Path(s_tmp_dir)
            (p_root / "a").mkdir()
            (p_root / "b").mkdir()
            p_a_file = p_root / "a/file.txt"
            p_b_file = p_root / "b/file.txt"
            p_a_file.write_text("a", encoding="utf-8")
            p_b_file.write_text("b", encoding="utf-8")
            d_dataset = {"data_dirs": ["a/file.txt", "b/file.txt"], "upload_infos": {}, "comments": [], "tags": {}}

            with self.assertRaises(ValueError):
                Dataset(d_dataset, p_root)
            self.assertFalse((p_a_file.parent / "file.txt.md5").exists())
            self.assertFalse((p_b_file.parent / "file.txt.md5").exists())

    def test_init_with_duplicate_data_dir(self) -> None:
        """Test du constructeur avec le même data_dir déclaré plusieurs fois."""
        with tempfile.TemporaryDirectory() as s_tmp_dir:
            p_root = Path(s_tmp_dir)
            p_file = p_root / "file.txt"
            p_file.write_text("content", encoding="utf-8")
            p_md5 = p_root / "file.txt.md5"

            o_dataset = Dataset({"data_dirs": ["file.txt", "file.txt"], "upload_infos": {}, "comments": [], "tags": {}}, p_root)

            self.assertEqual(o_dataset.data_files, {p_file: "."})
            self.assertEqual(o_dataset.md5_files, [p_root / "file.txt.md5"])
            self.assertEqual(p_md5.read_text(encoding="utf-8").splitlines(), [f"{FileHelper.md5_hash(p_file)}  file.txt"])
