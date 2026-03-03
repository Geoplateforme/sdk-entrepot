#!/usr/bin/env bash
# script d'exemple pour publier une archive sur la Géoplateforme
#Le jeu de données « 2_dataset_archive » contient des données de type archive à téléverser.
# récupération des données d'exemple
python3 -m sdk_entrepot_gpf example dataset 2_dataset_archive
# livraison des données sur la Géoplateforme
python3 -m sdk_entrepot_gpf delivery 2_dataset_archive/upload_descriptor.json
# Une fois les données livrées, il faut traiter les données avant de les publier (c'est à dire configurer un géo-service et le rendre accessible).
# Ces étapes sont décrites grâce à un workflow.
# récupération du workflow de traitement et publication d'une archive
python3 -m sdk_entrepot_gpf example workflow generic_archive.jsonc
# exécution des 4 étapes pour le traitement et la publication de l'archive
python3 -m sdk_entrepot_gpf workflow -f generic_archive.jsonc -s intégration-archive-livrée
python3 -m sdk_entrepot_gpf workflow -f generic_archive.jsonc -s patch-donnée-stockée
python3 -m sdk_entrepot_gpf workflow -f generic_archive.jsonc -s configuration-archive-livrée
python -m sdk_entrepot_gpf workflow -f generic_archive.jsonc -s publication-archive-livrée
