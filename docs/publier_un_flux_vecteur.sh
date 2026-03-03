#!/usr/bin/env bash
# script d'exemple pour publier un flux vecteur sur la Géoplateforme
#Le jeu de données « 1_dataset_vector » contient des données de type flux vecteur à téléverser.
# récupération des données d'exemple
python3 -m sdk_entrepot_gpf example dataset 1_dataset_vector
# livraison des données sur la Géoplateforme
python3 -m sdk_entrepot_gpf delivery 1_dataset_vector/upload_descriptor.json
# Une fois les données livrées, il faut traiter les données avant de les publier (c'est à dire configurer un géo-service et le rendre accessible).
# Ces étapes sont décrites grâce à un workflow.
# récupération du workflow de traitement et publication d'un flux vecteur
python3 -m sdk_entrepot_gpf example workflow generic_vector.jsonc
# exécution des 4 étapes pour le traitement et la publication du flux vecteur
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s mise-en-base
# WFS depuis BDD
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s configuration-wfs-bdd
python -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s publication-wfs-bdd
# WMS depuis BDD
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s configuration-wms-bdd
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s publication-wms-bdd
# création pyramide et WFS
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s création-pyramide
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s configuration-tms-py
python3 -m sdk_entrepot_gpf workflow -f generic_vecteur.jsonc -s publication-tms-py
