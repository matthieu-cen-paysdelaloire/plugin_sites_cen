🌿 Plugin QGIS : Gestionnaire des sites CEN Pays de la Loire

Ce plugin permet la consultation et la mise à jour simplifiée des données attributaires des sites naturels gérés par le CEN Pays de la Loire. Il offre une interface ergonomique pour garantir la cohérence des données saisies par les agents.


=>  Structure des fichiers :

    __init__.py : Fichier d'initialisation indispensable à Python pour reconnaître le dossier comme un paquet (package). Il contient la fonction classFactory, point d'entrée unique qui permet à QGIS de charger et de lancer l'extension.

    plugin_sites_cen.py : Orchestrateur du plugin. Gère l'intégration dans QGIS, l'explorateur de fichiers pour le GeoPackage et le chargement de la couche.

    plugin_sites_cen_dialog.py : Logique métier. Contient :

        Le mapping entre les widgets de l'interface et les champs SIG (field_map).

        Les dictionnaires de correspondance (RNX, types de milieux, etc.).

        La logique de validation (mise en surbrillance rouge des champs obligatoires).

        La gestion du défilement (optimisation de la molette de souris).

    plugin_sites_cen_dialog_base.ui : Design de l'interface réalisé sous Qt Designer (XML + Styles CSS).


=>  Prérequis sur les données (Couche SIG)

  Pour fonctionner, la table contenue dans le GeoPackage doit impérativement s'appeler 'sites_cen'.


=>  Maintenance et Évolutions :

  Modifier les listes déroulantes :
  - Toutes les valeurs des menus (Combo Boxes) sont centralisées dans les dictionnaires au début de la classe AttributeEditorSitesCENDialog. Pour ajouter ou modifier une option, intervenez directement dans le fichier plugin_sites_cen_dialog.py.

  Ajout de nouveaux champs : 
  - Pour intégrer un nouveau champ de saisie, créez le widget dans Qt Designer (.ui), puis ajoutez simplement une entrée dans le dictionnaire self.field_map du fichier ..._dialog.py en associant le nom du champ SIG à la variable du widget (ex: "mon_champ_sig": self.monNouveauWidget).

  Arbre de décision Géologique : 
  - Le système de cascade est piloté par le dictionnaire self.dict_geol_step. Sa structure imbriquée permet de modifier l'arbre de décision sans toucher à la fonction de calcul du code.


=>  Installation manuelle :

    Copier le dossier du plugin dans le répertoire des extensions QGIS :

    %AppData%\Roaming\QGIS\QGIS3\profiles\default\python\plugins

    Activer l'extension dans QGIS : Extensions > Installer/Gérer les extensions.

=>  Développeur : Matthieu Goubert

=>  Organisation : Conservatoire d'Espaces Naturels - Pays de la Loire

=>  Version : 1.0 (2026)