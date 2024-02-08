# CHANGE LOG

## v0.1.20

### [Added]

* DeleteAction : suppression des upload, stored_data, configuration et offering dans un workflow #63
* EditAction : édition(modification) des upload, stored_data, configuration et offering dans un workflow (entité + tags + commentaires) #66
* Offering #58 :
    * ajout fonction Offering.api_synchronize() : synchronisation de l'offre avec la configuration
    * ajout de la fonction Offering.get_url() : récupération de la liste des urls d'une offre
    * ajout de l'action `SynchronizeOfferingAction` : synchronisation de l'offre avec la configuration depuis un workflow
* Documentation sur les [workflow](./docs/workflow.md) et les [résolveurs](./docs/resolveurs.md)

### [Changed]

* Workflow : ajout des actions DeleteAction, EditAction, SynchronizeOfferingAction
* StoreEntity: ajout de `edit()` permettant de gérer l'édition des entités si possible. Ici impossible de mettre à jour les entités.
* PartialEditInterface: surcharge de `edit()` pour permettre l’édition partielle
* FullEditInterface: surcharge de `edit()` pour permettre l’édition complète

### [Fixed]

* StoreEntityResolver: avant utilisation de l'entité, récupération de toutes ses informations
* Endpoint: neutralisation des fonction inutilisable

## v0.1.19

### [Added]

* Classe Metadata + configuration associée et tests
* Classe DescriptorFileReader pour la livraisons des fichiers static, metadata et annexe
* Main: gestion des fichiers static, metadata et annexe (upload, liste, détail, publication et dépublication)
* Main: fonction ctrl_c_upload() pour la gestion du Ctrl+C pendant le monitoring des vérifications

### [Changed]

* Résolution des workflows :
    * `ActionAbstract` : si l'action après résolution n'est plus un JSON valide, on log le texte obtenue en niveau debug ;
    * `ActionAbstract` : on n'indente pas le JSON avant résolution
    * Regex resolver : ajout de `_` avant et après le nom du résolveur si format list ou dict.
* renommage DescriptorFileReader en UploadDescriptorFileReader
* valeur définie dans la configuration pour `client_secret` et `client_id` et mise à jour de la documentation
* conservation de NotFoundError lors de ApiRequester.url_request()
* ApiRequester.url_request(): suppression de l'affichage automatique des erreurs
* main : meilleure gestion globale des erreurs
* Attente à la suppression des offres (non instantanée) pour éviter bug avec -b DELETE #57 et suppression en cascade.

### [Fixed]

* Bug de config pour les URL des fichiers statics
* Bug absence de transmission des behavior venant de la commande pour ConfigurationAction et OfferingAction
* Gestion du Ctrl+C pendant le monitoring des vérification, suppression des vérifications non fini et réouverture de la livraison

## v0.1.18

### [Added]

* Ajout d'un fichier de listing des modifications.

### [Changed]

* La livraison de plusieurs jeux de données est plus efficace (livraison des jeux de données puis attente des vérifications)
* Documentation : uniformisation du style + maj liens et noms

### [Fixed]

* Bug de config `upload_push_data` manquante.
