from sdk_entrepot_gpf.workflow.resolver.DictResolver import DictResolver
from sdk_entrepot_gpf.workflow.resolver.Errors import ResolverNotFoundError
from sdk_entrepot_gpf.workflow.resolver.GlobalResolver import GlobalResolver

from tests.GpfTestCase import GpfTestCase


class GlobalResolverTestCase(GpfTestCase):
    """Tests GlobalResolver class.

    cmd : python3 -m unittest -b tests.workflow.resolver.GlobalResolverTestCase
    """

    localization = {
        "Jacques_country": "France",
        "Jacques_city": "Paris",
        "Jacques_street": "Champs-Elysée",
        "John_country": "England",
        "John_city": "London",
        "John_street": "rue_Londres",
        "city": ["Paris", "London"],
        "store": {"Paris": "Champs-Elysée", "London": "rue_Londres"},
    }
    profession = {
        "chef": "Jacques",
        "sailor": "John",
    }

    @classmethod
    def setUpClass(cls) -> None:
        """fonction lancée une fois avant tous les tests de la classe"""
        super().setUpClass()
        GlobalResolver._instance = None  # pylint:disable=protected-access
        GlobalResolver().add_resolver(DictResolver("localization", GlobalResolverTestCase.localization))
        GlobalResolver().add_resolver(DictResolver("profession", GlobalResolverTestCase.profession))

    def test_add_resolver(self) -> None:
        """Vérifie le bon fonctionnement de la fonction add_resolver."""
        # La fonction a déjà été appelée dans le SetUpClass
        # On vérifie juste que l'on a bien 2 résolveurs
        self.assertEqual(len(GlobalResolver().resolvers), 2)
        self.assertTrue("localization" in GlobalResolver().resolvers)
        self.assertTrue("profession" in GlobalResolver().resolvers)

    def test_regex(self) -> None:
        """Vérifie que la regex fonctionne bien sur les cas particuliers."""
        o_regex = GlobalResolver().regex

        d_tests = {
            "{localization.Jacques_country}_{profession.sailor}": [
                {
                    "param": "{localization.Jacques_country}",
                    "resolver_name": "localization",
                    "to_solve": "Jacques_country",
                },
                {
                    "param": "{profession.sailor}",
                    "resolver_name": "profession",
                    "to_solve": "sailor",
                },
            ],
            "{localization.Jacques_country} {profession.sailor}": [
                {
                    "param": "{localization.Jacques_country}",
                    "resolver_name": "localization",
                    "to_solve": "Jacques_country",
                },
                {
                    "param": "{profession.sailor}",
                    "resolver_name": "profession",
                    "to_solve": "sailor",
                },
            ],
            "{localization.{profession.chef}_city}": [
                {
                    "param": "{localization.{profession.chef}_city}",
                    "resolver_name": "localization",
                    "to_solve": "{profession.chef}_city",
                },
            ],
            "{store_entity.stored_data.infos.name [INFOS(name=ADMIN-EXPRESS_{param.edition}), TAGS(demande={param.demande})]}": [
                {
                    "param": "{store_entity.stored_data.infos.name [INFOS(name=ADMIN-EXPRESS_{param.edition}), TAGS(demande={param.demande})]}",
                    "resolver_name": "store_entity",
                    "to_solve": "stored_data.infos.name [INFOS(name=ADMIN-EXPRESS_{param.edition}), TAGS(demande={param.demande})]",
                }
            ],
            "stored_data.infos.name [INFOS(name=ADMIN-EXPRESS_{param.edition}), TAGS(demande={param.demande})]": [
                {
                    "param": "{param.edition}",
                    "resolver_name": "param",
                    "to_solve": "edition",
                },
                {
                    "param": "{param.demande}",
                    "resolver_name": "param",
                    "to_solve": "demande",
                },
            ],
        }
        for s_string, l_results in d_tests.items():
            self.assertListEqual(l_results, [i.groupdict() for i in o_regex.finditer(s_string)])

    def test_resolve(self) -> None:
        """Vérifie le bon fonctionnement de la fonction resolve."""
        # Cas simples : une seule résolution
        # Comme string (pour insérer une ou plusieurs string)
        self.assertEqual(GlobalResolver().resolve("{localization.Jacques_country}"), "France")
        self.assertEqual(GlobalResolver().resolve("{profession.sailor}"), "John")
        self.assertEqual(GlobalResolver().resolve("{localization.Jacques_country}_{profession.sailor}"), "France_John")
        # Comme liste (pour insérer une string)
        self.assertEqual(GlobalResolver().resolve('["localization","Jacques_country"]'), "France")
        # Comme dict (pour insérer une string)
        self.assertEqual(GlobalResolver().resolve('{"localization":"Jacques_country"}'), "France")
        # Comme liste (pour insérer une liste)
        self.assertEqual(GlobalResolver().resolve('["localization","city"]'), "['Paris', 'London']")
        # Comme dict (pour insérer un dict)
        self.assertEqual(GlobalResolver().resolve('{"localization":"store"}'), "{'Paris': 'Champs-Elysée', 'London': 'rue_Londres'}")
        # Cas avancés : deux résolutions l'une dans l'autre
        # Comme string
        self.assertEqual(GlobalResolver().resolve("{localization.{profession.sailor}_country}"), "England")
        self.assertEqual(GlobalResolver().resolve("{localization.{profession.chef}_city}"), "Paris")
        # Comme liste (pour insérer une string)
        self.assertEqual(GlobalResolver().resolve('["localization","{profession.sailor}_country"]'), "England")
        # Comme dict (pour insérer une string)
        self.assertEqual(GlobalResolver().resolve('{"localization":"{profession.sailor}_country"}'), "England")
        # Cas erreur :
        with self.assertRaises(ResolverNotFoundError) as o_arc:
            GlobalResolver().resolve("{resolver_not_found.foo}")
        self.assertEqual(o_arc.exception.resolver_name, "resolver_not_found")
        self.assertEqual(o_arc.exception.message, "Le résolveur 'resolver_not_found' demandé est non défini.")
