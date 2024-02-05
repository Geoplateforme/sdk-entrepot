# Résolveur

Les résolveur sont des outils permettant de compléter les workflow en remplaçant un pattern par la valeur calculée.

## Utilisation

 => TODO

## résolveur de base

Il y a 4 résolveur de base

* [DictResolver](DictResolver): permet d'insérer les valeur contenu dans une dictionnaire
* [FileResolver](FileResolver): insert les valeurs contenu dans un fichier
* [StoreEntityResolver](StoreEntityResolver): récupère des informations sur les entités depuis la GPF
* [UserResolver](UserResolver): récupère des informations de l'utilisateur courant.

### DictResolver

Permet de résoudre des paramètres clé -> valeur (pas de sous clef)

Prend en initialisation le dictionnaire contenant les valeurs.

Exemple :

```python
from sdk_entrepot_gpf.workflow.resolver.DictResolver import DictResolver
from sdk_entrepot_gpf.workflow.resolver.GlobalResolver import GlobalResolver

dictionnaire = {
    "ajout_text": "valeur 1",
    "ajout_liste": ["val 1", "val 2"],
    "ajout_dict": {"key1": "val1", "key2": "val2"},
}

# initialisation
dict_resolver = DictResolver("my_dict", dictionnaire)
GlobalResolver().add_resolver(dict_resolver)

# texte à résoudre
text = """
insertion de text ici >{my_dict.ajout_text}<
ici une liste >["_my_dict.ajout_liste"]<
ou une liste >["_my_dict_","ajout_liste"]<
ici un dictionnaire >{"_my_dict_": "ajout_dict"}<
"""

# resolution
print(GlobalResolver().resolve(text))
## affichage
#    insertion de text ici >valeur 1<
#    ici une liste >['val 1', 'val 2']<
#    ou une liste >['val 1', 'val 2']<
#    ici un dictionnaire >{'key1': 'val1', 'key2': 'val2'}<

```

### FileResolver

Permet de résoudre des paramètres faisant référence à des fichiers : ce résolveur permet d'insérer le contenu d'un fichier au moment de la résolution.

Ce fichier peut être un fichier texte basique, une liste au format JSON ou un dictionnaire au format JSON.

Exemple :

```python
from pathlib import Path
from sdk_entrepot_gpf.workflow.resolver.FileResolver import FileResolver
from sdk_entrepot_gpf.workflow.resolver.GlobalResolver import GlobalResolver

# dans le répertoire courant on a les fichiers suivants
## text simple: "text.txt"
# * contenu => "coucou"
## liste: "liste.json"
# * contenu => ["valeur 1", "valeur 2"]
## dictionnaire: "dict.json"
# * contenu => {"k1":"v1", "k2":"v2"}

# initialisation
file_resolver = FileResolver("fichiers", Path("."))
GlobalResolver().add_resolver(file_resolver)

# texte à résoudre
text = """
insertion de text ici >{fichiers.str(text.txt)}<
ici une liste >["_fichiers_","list(liste.json)"]<
ici un dictionnaire >{"_fichiers_":"dict(dict.json)"}<
"""

# resolution
print(GlobalResolver().resolve(text))
## affichage
#   insertion de text ici >coucou<
#   ici une liste >["valeur 1", "valeur 2"]<
#   ici un dictionnaire >{"k1":"v1", "k2":"v2"}<
```

### StoreEntityResolver


### UserResolver

## créer son résolveur
