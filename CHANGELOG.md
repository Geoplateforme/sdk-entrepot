# CHANGE LOG

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
