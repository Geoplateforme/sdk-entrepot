# Workflows

Le fichier workflow est un fichier au format JSON permettant de décrire les actions à réaliser sur des données stockées où livrées.

Certaines valeurs du workflow peuvent être complétées avec un système de résolution permettant notamment d'utiliser le nom des entités pour trouver leur ID. Pour plus d'informations consulter la [page dédiée au résolveurs](resolveurs.md).

Les actions sont les suivantes :

* lancer un traitement (càd créer une processing exécution) ;
* configurer un géoservice (càd créer une configuration) ;
* publier un géoservice (càd créer une offering) ;
* supprimer une entité de type upload, stored_data, configuration ou offering ;
* modifier une entité de type upload, stored_data, configuration ou offering ;
* copier une configuration (création d'une nouvelle configuration en reprenant les paramètres non précisés de la précédente) ;
* synchroniser une offre (mettre à jour avec la donnée stockée et une offering).

## Définition

Le fichier doit contenir un dictionnaire `workflow`. Qui contient deux clefs :

* `datastore`: (optionnel) uuid du datastore à utiliser pour le workflow.
* `step`: (obligatoire) dictionnaire des étapes à lancer ;
  * la clef sera le nom de l'étape qui servira à la lancer ;
  * sa valeur est un dictionnaire décriant l'étape :
    * `actions` : (obligatoire) listes des actions à lancer, la liste sera exécutée dans l'ordre. Le dictionnaire décrivant l'action dépend du type d'action à lancer, la clef `type` permet de définir le type d'action à effectuer (description plus bas) ;
    * `parents` : (obligatoire) liste des étapes devant précéder celle-ci. Pour une actions sans dépendances la liste doit être vide.

ce qui donne :

```json
{
  "workflow": {
    "steps": {
      "etape 1": {
        "actions": [ ... ],
        "parents": []
      },
      "etape 2": {
        "actions": [ ... ],
        "parents": []
      }
    }
  }
}
```

Ce workflow permet de lancé 2 étapes `etape 1` et `etape 2`.

Les actions possibles sont les suivantes :

* [exécuter un traitement](#executer-un-traitement)
* [configurer un flux](#configurer-un-flux)
* [publier un flux](#publier-un-flux)
* [supprimer une entité](#supprimer-une-entite)
* [modifier une entité](#modifier-une-entite)
* [copier une configuration](#copier-une-configuration)
* [synchroniser une publication](#synchroniser-une-publication)

### Exécuter un traitement

* `type`: `processing-execution`
* `body_parameters`: dictionnaire paramétrant l’exécution :
  * `processing`: id du traitement à utiliser
  * `inputs` : dictionnaire décrivant la/les données d'entrée (se référer à la documentation du traitement)
  * `output`: dictionnaire décrivant la sortie du traitement (se référer à la documentation du traitement)
  * `parameters`: dictionnaire des paramètres à utiliser pour le traitement (se référer à la documentation du traitement)
* `comments` : liste des commentaires à ajouter à la donnée en sortie (si mise à jour : les commentaires déjà présents ne sont pas ajoutés).
* `tags` : tags à ajouter à la donnée en sortie (clef-valeur) (si mise à jour : les tags déjà présents ne sont pas ajoutés).

La liste des traitement est disponible ici : [/datastores/{datastore}/processings
](https://data.geopf.fr/api/swagger-ui/index.html#/Traitements/getAll_4).

Le détail d'un traitement est disponible ici : [/datastores/{datastore}/processings/{processing}](https://data.geopf.fr/api/swagger-ui/index.html#/Traitements/get_6)

### Configurer un flux

* `type`*: `configuration`
* `body_parameters`*: dictionnaire paramétrant la configuration :
  * `type`*: type du flux (WMS-VECTOR, WFS, WMTS-TMS, WMS-RASTER, DOWNLOAD, ITINERARY-ISOCURVE, ALTIMETRY, SEARCH, VECTOR-TMS)
  * `name`*: Nom de la configuration
  * `layer_name`*: Nom technique de la ressource. Ce nom doit être unique sur la plateforme pour un type de configuration donné. Uniquement des caractères alphanumériques, tiret, tiret bas, point (pattern: ^[A-Za-z0-9_\-.]+$)
  * `type_infos`* : description des données à utiliser (dépend du flux)
  * `attribution`: (optionnel) Métadonnées liées au propriétaire de la configuration
    * `title`*: Nom du propriétaire
    * `url`*: URL vers le site du propriétaire
    * `logo`: Dictionnaire décrivant le logo du propriétaire
    * `format`*: le format (mime-type) du logo (pattern: `\w+/[-+.\w]+`, example: `image/jpeg`)
    * `url`*: l'URL d'accès au logo
    * `width`*: la largeur du logo
    * `height`*: la hauteur du logo
* `comments` : liste des commentaires à ajouter à la configuration.
* `tags` : tags à ajouter à la configuration (clef-valeur).

type_infos selon le flux :

#### WFS

* `bbox`: dictionnaire Bounding box :
  * `west`*
  * `south`*
  * `east`*
  * `north`*
* `used_data`*: liste de dictionnaires :
  * `stored_data`*: Identifiant de la donnée stockée
  * `relations`*: liste de dictionnaire décrivant la relation :
    * `native_name`*: Nom de la table
    * `public_name`: Nom public de la table
    * `title`*: Titre
    * `keywords`: Liste de mots clés (doivent être uniques)
    * `abstract`*: Description

#### WMTS-TMS

* `bbox`: dictionnaire Bounding box :
  * `west`*
  * `south`*
  * `east`*
  * `north`*
* `title`*: titre
* `keywords`: Liste de mots clés (doivent être uniques)
* `styles`: lists des identifiants des fichiers statiques de style Rok4
* `used_data`*: liste de dictionnaire :
  * `bottom_level`*:niveau minimum
  * `top_level`*: niveau maximum
  * `stored_data`*: Identifiant de la donnée stockée
* `abstract`*: Description
* `getfeatureinfo`: Dictionnaire décrivant la ressource cible du GetFeatureInfo. Une des structure suivante :
  * avec la stored data, dictionnaire :
    * `stored_data`*: Indique si on va utiliser directement la donnée stockée
  * avec une url, dictionnaire :
    * `server_url`* url utiliser pour le GetFeatureInfo

#### VECTOR-TMS

* `used_data`*: liste de dictionnaires :
  * `stored_data`*: Identifiant de la donnée stockée
  * `relations`*: liste de dictionnaire décrivant la relation :
    * `native_name`*: Nom de la table
    * `public_name`: Nom public de la table
    * `abstract`*: Description

#### WMS-VECTOR

* `bbox`: dictionnaire Bounding box :
  * `west`*
  * `south`*
  * `east`*
  * `north`*
* `title`*: titre
* `keywords`: Liste de mots clés (doivent être uniques)
* `abstract`*: Description
* `used_data`*: liste de dictionnaire :
  * `stored_data`*: Identifiant de la donnée stockée
  * `relations`*: liste de dictionnaire décrivant la relation :
    * `name`*: Nom de la table
    * `style`*: uuid du statiques de style
    * `ftl`: uuid de ?????

#### WMS-RASTER

* `bbox`: dictionnaire Bounding box :
  * `west`*
  * `south`*
  * `east`*
  * `north`*
* `title`*: titre
* `keywords`: Liste de mots clés (doivent être uniques)
* `styles`: lists des identifiants des fichiers statiques de style Rok4
* `used_data`*: liste de dictionnaire :
  * `bottom_level`*:niveau minimum
  * `top_level`*: niveau maximum
  * `stored_data`*: Identifiant de la donnée stockée
* `interpolation`: Interpolation utilisée pour les conversions de résolution : [ NEAREST-NEIGHBOUR, LINEAR, BICUBIC, LANCZOS2, LANCZOS3, LANCZOS4 ] (default: BICUBIC)
* `bottom_resolution`: Résolution minimale de la couche
* `top_resolution`: Résolution maximale de la couche
* `abstract`*: Description
* `getfeatureinfo`: Dictionnaire décrivant la ressource cible du GetFeatureInfo. Une des structure suivante :
  * avec la stored data, dictionnaire :
    * `stored_data`*: Indique si on va utiliser directement la donnée stockée
  * avec une url, dictionnaire :
    * `server_url`* url utiliser pour le GetFeatureInfo

#### DOWNLOAD

* `title`*: titre
* `keywords`: Liste de mots clés (doivent être uniques)
* `abstract`*: Description
* `used_data`*: liste de dictionnaire :
  * `sub_name`*: nom
  * `title`: titre
  * `keywords`: Liste de mots clés (doivent être uniques)
  * `format`: format
  `zone`: zone
  * `stored_data`*: Identifiant de la donnée stockée
  * `abstract`*: Description

#### ALTIMETRY

* `bbox`: dictionnaire Bounding box
  * `west`*
  * `south`*
  * `east`*
  * `north`*
* `title`*: Titre
* `keywords`:liste des mots clés
* `abstract`*: Description
* `used_data`*: liste de dictionnaire :
  * `title`*: Titre
  * `bbox`: dictionnaire Bounding box
    * `west`*
    * `south`*
    * `east`*
    * `north`*
  * `source`*: Informations sur la source des données. Une des solution suivante
    * valeur fixe :
      * `value`*: Valeur unique pour la source des données
    * Mapping entre les valeurs de la pyramide et les valeurs effectivement renvoyées
      * `mapping`: dictionnaire :
        * `< * >`: Mapping entre les valeurs de la pyramide et les valeurs effectivement renvoyées
      * `stored_data`*: Identifiant de la donnée stockée
  * `accuracy`* Informations sur la source des données. Une des solution suivante
    * valeur fixe:
      * `value`*: Valeur unique pour la source des données
    * Mapping entre les valeurs de la pyramide et les valeurs effectivement renvoyées
      * `mapping`: dictionnaire :
        * `< * >`: Mapping entre les valeurs de la pyramide et les valeurs effectivement renvoyées
      * `stored_data`*: Identifiant de la donnée stockée
  * `stored_data*: Identifiant de la donnée stockée

#### SEARCH

* `title`*: Titre
* `keywords`:liste des mots clés
* `abstract`*: Description
* `used_data`*: liste de dictionnaire :
  * `stored_data`*: Identifiant de la donnée stockée

#### ITINERARY-ISOCURVE

* `bbox`: dictionnaire Bounding box
  * `west`*
  * `south`*
  * `east`*
  * `north`*
* `title`*: Titre
* `keywords`:liste des mots clés
* `abstract`*: Description
* `limits`: dictionnaire décrivant les limites pour les calculs d'itinéraire (nombre d'étapes et de contraintes) et d'isochrone (durée et distance)
  * `steps`: Nombre d'étapes maximal pour le service d'itinéraire (maximum: 25, minimum: 0, default: 16)
  * `constraints`: Nombre de contraintes maximal pour le service d'itinéraire (maximum: 6, minimum: 0, default: 3)
  * `duration`: Durée maximale pour le calcul d'isochrone (maximum: 86400, minimum: 0, default: 43200)
  * `distance`: Distance maximale pour le calcul d'isochrone (maximum: 2000000, minimum: 0, default: 1000000)
* `constraints`: Dictionnaire de définition des contraintes pour la configuration (pas d'information sur le contenu dans la documentation API GPF)
* `srss`: liste des projections
* `used_data`* dictionnaire :
  * `profile`*: Profil de graphe à utiliser (e.g. voiture ou piéton)
  * `optimization`*: Optimisation de graphe à utiliser (e.g. plus court ou plus rapide)
  * `cost_column`: Colonne de coût (pour stored data de type GRAPHE-DB)
  * `reverse_cost_column`: Colonne de coût inverse (pour stored data de type GRAPHE-DB)
  * `cost_type`: Type de coût [ time, distance ]
  * `costing`: Méthode de calcul de coût (pour stored data de type GRAPHE-VALHALLA) [ auto, auto_shorter, pedestrian ]
  * `attributes`: liste dictionnaire des Attributs retournés par l'API:
    * `table_name`: Nom de la table
    * `native_name`*: Nom de l'attribut dans la table
    * `public_name`*: Nom de l'attribut vu du service (pattern: ^[A-Za-z0-9_-]+$)
    * `default`: boolean
  * `stored_data`*: Identifiant de la donnée stockée

### Publier un flux

* `type`*: `offering`
* `url_parameters`: dictionnaire :
  * `configuration`: uuid de la configuration que l'on veux publier
* `body_parameters`*: dictionnaire paramétrant l'offre:
  * `visibility`: niveau de visibilité [ PRIVATE, REFERENCED, PUBLIC ] (default: PRIVATE)
  * `endpoint`*: uuid du endpoint à utiliser
  * `open`: boolean
  * `permissions`: liste des uuid des permissions

### Supprimer une entité

Possibilité de supprimer des entités de type : upload, stored_data, configuration et offering.

* suppression par ID de l'entité :

```json
{
    "type": "delete-entity",
    // Type de l'entité à supprimer (upload, stored_data, configuration, offering)
    "entity_type": "configuration",
    // Id de l'entité à supprimer
    "entity_id": "{uuid}",
    // Suppression en cascade autorisée ou pas ? par défaut à false
    "cascade": true,
    // Ok si non trouvée ? par défaut à true
    "not_found_ok": true,
}
```

* suppression par filtre sur la liste :

```json
{
    "type": "delete-entity",
    // Type de l'entité à supprimer (upload, stored_data, configuration, offering)
    "entity_type": "configuration",
    // Critères pour filtrer filter_infos et/ou filter_tags
    "filter_infos": { ... },
    "filter_tags": { ... },
    // Suppression en cascade autorisée ou pas ? par défaut à false
    "cascade": true,
    // Ok si non trouvée ? par défaut à true
    "not_found_ok": true,
    // Que faire plusieurs résultats ?  first => uniquement 1er de la liste; all => on prend tout (défaut); error => sortie en erreur du programme
    "if_multi": "first|all|error",
}
```

### Modifier une entité

Possibilité de modifier une entité de type : upload, stored_data, configuration et offering.

Correspond aux requêtes PUT et PATCH de l'[API Entrepôt](https://data.geopf.fr/api/swagger-ui/index.html).

```json
{
    "type": "edit-entity",
    // Type de l'entité à modifier : (upload, stored_data, configuration, offering)
    "entity_type": "configuration",
    // Id de l'entité à modifier
    "entity_id": "{uuid}",
    // Optionnel si non présent requête n'ai pas lancée ( => mise à jour des tags et commentaires uniquement), si l'entité hérite de FullEditInterface (mise à jour totale) => fusion des informations récupérées sur l'API (GET) et de celle fournies, sinon on envoie que celles fournies
    "body_parameters": { ... },
    // Optionnel : Liste des tags ajoutés à l'entité (uniquement si la classe hérite de TagInterface)
    "tags": {},
    // Optionnel : Liste des commentaires à ajouter (uniquement si la classe hérite de CommentInterface)
    "comments": [],
}
```

Pour le `body_parameters` se référer à la documentation API GPF:

* upload *(partielle)* : PATCH [/datastores/{datastore}/uploads/{upload}](https://data.geopf.fr/api/swagger-ui/index.html#/Livraisons%20et%20v%C3%A9rifications/update_2)
  * Seul le nom de la livraison, sa description et sa visibilité sont modifiables, et uniquement par le propriétaire. Les autres informations, comme le type de la livraison, sont figées.
* stored_data *(partielle)* : PATCH [/datastores/{datastore}/stored_data/{stored_data}](https://data.geopf.fr/api/swagger-ui/index.html#/Donn%C3%A9es%20stock%C3%A9es/update_3)
  * Seul le nom de la donnée et sa visibilité sont modifiables, et uniquement par le propriétaire. Les autres informations, comme le type de la donnée, sont figées pour une donnée.
* configuration *(totale)* : PUT [/datastores/{datastore}/configurations/{configuration}](https://data.geopf.fr/api/swagger-ui/index.html#/Configurations%20et%20publications/update_1)
  * Si la configuration est liée à des offres en cours de publication, la modification n'est pas possible. Si la configuration est liée à des offres publiées, les modifications sont répercutées sur les serveurs de diffusion. Le nom technique et le type ne sont pas modifiable.
* offering *(partielle)*: PATCH [/datastores/{datastore}/offerings/{offering}](https://data.geopf.fr/api/swagger-ui/index.html#/Configurations%20et%20publications/update_4)
  * Il est possible de modifier la visibilité d'une offre afin qu'elle apparaisse dans les catalogues ou qu'on puisse donner des permissions, ou au contraire qu'elle en disparaisse. On peut également désactiver une offre pour en couper la consommation rapidement, sans déconfigurer les permissions

### Copier une configuration

Création d'une configuration à partir d'une configuration déjà existante

```json
{
    "type": "copy-configuration",
    "url_parameters" : {
        // Id de la configuration à copier
        "configuration": "{uuid}"
    },
    // nouveau name et layer_name de la configuration à créer le layer_name n'est plus modifiable pas la suite)
    "body_parameters": {
        "name": "",
        "layer_name": "",
    },
    // optionnel : Liste des tags ajoutés à la nouvelle configuration, (ne sont pas récupérer depuis la configuration source)
    "tags": { "key_tag" : "val_tag"},
    // optionnel : Liste des commentaires à ajouter à la nouvelle configuration, (ne sont pas récupérer depuis la configuration source)
    "comments": [],
}
```

### Synchroniser une publication

Synchronisation d'une ou plusieurs offres avec leur configuration et stored-data.

* Mise à jour selon ID de l'offre

```json
{
  "type": "synchronize-offering",
  // Id de l'entité à supprimer (erreur remontée par l'API si l'entité n'existe pas)
  "entity_id": "{uuid}"
}
```

* suppression par filtrage sur la liste des offres, possibilité de synchroniser plusieurs offres en même temps

```json
{
  "type": "synchronize-offering",
  // Ou Critères pour la retrouver
  "filter_infos": { ...  },
  // optionnel : Que faire plusieurs résultats ?  first => uniquement 1er de la liste; all => on prend tout (défaut); error => sortie en erreur du programme
  "if_multi": "first|all|error"
}
```

Si aucun résultat, on sort en erreur.

Pour "filter_infos" voir les filtres possibles pour la requête [/datastores/{datastore}/offerings](https://data.geopf.fr/api/swagger-ui/index.html#/Configurations%20et%20publications/getAll_6). Si on a `"configuration" : "{uuid}"` c'est la requête  [/datastores/{datastore}/configurations/{configuration}/offerings](https://data.geopf.fr/api/swagger-ui/index.html#/Configurations%20et%20publications/getOfferings) qui sera utilisée dans l'attente que la filtration sur les configurations soit possible.

## Exemple

### Actions de base

Pour les actions de base (processing-execution, configuration, offre) des workflows des tutoriels sont disponibles dans [sdk_entrepot_gpf/_data/workflows/](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/) :

* archivage [generic_archive.jsonc](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/generic_archive.jsonc) (traitement d'une archive, configuration et offre pour un géoservice Téléchargement). [Tutoriel](tutoriel_1_archive.md) ;
* flux vecteur [generic_vecteur.jsonc](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/generic_vecteur.jsonc) (traitement d'une mise en base, configuration et offre pour un géoservice Flux WFS, configuration et offre pour un flux WMS vecteur, traitement de création de pyramide, configuration et offre pour un flux TMS) [Tutoriel](./tutoriel_2_flux_vecteur.md) ;
* flux raster [generic_raster.jsonc](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/generic_raster.jsonc) (traitement de création d'une pyramide, configuration et offre pour un flux WMS, configuration et offre pour un flux WMTS) [Tutoriel](./tutoriel_3_flux_raster.md) ;
* mise en place d'une pyramide par "joincache" [generic_joincache.jsonc](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/generic_joincache.jsonc) (traitement création de pyramides, traitement de fusion de pyramides, traitement de mise à jour d'une pyramide, configuration et offre pour un flux WMS raster, configuration et offre pour un flux WMTS) ;
* mise à jour d'un base de donnée [generic_maj_bdd.jsonc](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/generic_maj_bdd.jsonc) (traitement de mise en base création + mise à jour, configuration et offre pour un flux WMS)
* création d'une pyramise rasteur à partir un flux WMS vecteur (moissonnage) [generic_moissonnage.jsonc](https://github.com/Geoplateforme/sdk-entrepot/tree/prod/sdk_entrepot_gpf/_data/workflows/generic_moissonnage.jsonc) (traitement de mise en base, configuration et offre pour un flux WMS vecteur, traitement de moissonnage, configuration et offre pour un flux WMS raster) ;

## Exécution du workflow

### Via l'utilisation du SDK comme exécutable

* Lister les étapes disponibles et valider votre workflow :

```sh
python -m sdk_entrepot_gpf workflow -f mon_workflow.json
```

* lancer une étape :

```sh
python -m sdk_entrepot_gpf workflow -f mon_workflow.json -s mon_étape
```

### Via l'utilisation du SDK comme module

Exemple de code complet permettant de valider et d'afficher les étapes du workflow et de lancer l'étape "etape 1" :

```py
from sdk_entrepot_gpf.io.Config import Config
# Importation de la classe JsonHelper
from sdk_entrepot_gpf.helper.JsonHelper import JsonHelper
# Importation des classes Workflow, GlobalResolver et StoreEntityResolver
from sdk_entrepot_gpf.workflow.Workflow import Workflow
from sdk_entrepot_gpf.workflow.resolver.GlobalResolver import GlobalResolver
from sdk_entrepot_gpf.workflow.resolver.StoreEntityResolver import StoreEntityResolver

# initialisation de la configuration, adapté le nom si besoin
Config().read("config.ini")

# initialisation du Workflow avec le fichier "mon_workflow.jsonc"
p_workflow = Path("mon_workflow.jsonc").absolute()
o_workflow = Workflow(p_workflow.stem, JsonHelper.load(p_workflow))

# validation et liste des étapes

## validation
Config().om.info("Validation du workflow...")
l_errors = o_workflow.validate()
if l_errors:
    s_errors = "\n   * ".join(l_errors)
    Config().om.error(f"{len(l_errors)} erreurs ont été trouvées dans le workflow.")
    Config().om.info(f"Liste des erreurs :\n   * {s_errors}")
    raise GpfSdkError("Workflow invalide.")
Config().om.info("Le workflow est valide.", green_colored=True)

## Affichage des étapes disponibles et des parents
Config().om.info("Liste des étapes disponibles et de leurs parents :", green_colored=True)
l_steps = o_workflow.get_all_steps()
for s_step in l_steps:
    Config().om.info(f"   * {s_step}")

# exécution d'une étape

## définition des résolveurs
GlobalResolver().add_resolver(StoreEntityResolver("store_entity"))
GlobalResolver().add_resolver(UserResolver("user"))

## OPTIONNEL:  le comportement si l'entité à créer existe déjà (si None, valeur de la configuration)
s_behavior = "STOP"

## on lance le monitoring de l'étape en précisant la gestion du ctrl-C
o_workflow.run_step(self.o_args.step, behavior=s_behavior, datastore=self.datastore)
```
