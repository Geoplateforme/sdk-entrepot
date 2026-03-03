#!/usr/bin/env bash
# Script de publication pour un flux raster sur la Géoplateforme
#Le jeu de données « 3_dataset_raster » contient des données de type flux raster à téléverser.
# récupération des données d'exemple
python3 -m sdk_entrepot_gpf example dataset 3_dataset_raster
# livraison des données sur la Géoplateforme
python3 -m sdk_entrepot_gpf delivery 3_dataset_raster/upload_descriptor.jsonc
# Une fois les données livrées, il faut traiter les données avant de les publier (c'est à dire configurer un géo-service et le rendre accessible).
# Ces étapes sont décrites grâce à un workflow.
# récupération du workflow de traitement et publication d'un flux raster
python3 -m sdk_entrepot_gpf example workflow generic_raster.jsonc
# exécution des 4 étapes pour le traitement et la publication du flux raster
# partie création de la pyramide
python3 -m sdk_entrepot_gpf workflow -f generic_raster.jsonc -s pyramide
# partie publication WMTS
python3 -m sdk_entrepot_gpf workflow -f generic_raster.jsonc -s configuration-WMTS
python3 -m sdk_entrepot_gpf workflow -f generic_raster.jsonc -s publication-WMTS
# partie publication WMS
python3 -m sdk_entrepot_gpf workflow -f generic_raster.jsonc -s configuration-WMS
python3 -m sdk_entrepot_gpf workflow -f generic_raster.jsonc -s publication-WMS
