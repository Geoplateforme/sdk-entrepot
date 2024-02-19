from sdk_entrepot_gpf.workflow.resolver.AbstractResolver import AbstractResolver

from tests.GpfTestCase import GpfTestCase


class AbstractResolverTestCase(GpfTestCase):
    """Tests AbstractResolver class.

    cmd : python3 -m unittest -b tests.workflow.resolver.AbstractResolverTestCase
    """

    def test_get(self) -> None:
        """test unitaire pour get()"""

        d_data = {"key": "val", "dict": {"key": "val_dict"}, "list": ["val_list", {"key": "val_list_dict"}]}
        l_res = [
            ("key", "val"),
            ("dict.key", "val_dict"),
            ("list[0]", "val_list"),
            ("list[1].key", "val_list_dict"),
        ]
        for s_js_key, s_res in l_res:
            self.assertEqual(s_res, AbstractResolver.get(d_data, s_js_key))
