# -*- coding: utf-8 -*-
import os
from qgis.PyQt import uic, QtWidgets, QtCore, QtGui
from qgis.core import NULL

# Permet de créer la connexion entre notre fichier .ui contennant les codes pour le design de notre interface et notre fichier python
# Permet de modifier l'aspect visuel de notre plugin, sans toucher à la logique du code
UI_FILE = os.path.join(os.path.dirname(__file__), 'plugin_sites_cen_dialog_base.ui')
FORM_CLASS, _ = uic.loadUiType(UI_FILE)

# Configuration de la fonction permettant de lancer le script python 
class AttributeEditorSitesCENDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        super(AttributeEditorSitesCENDialog, self).__init__(parent)
        self.setupUi(self)
        
        # --- VERROUILLAGE DES DIMENSIONS ---
        # On récupère la taille définie dans le .ui
        ui_width = self.width()
        ui_height = self.height()
        
        # On fixe les limites min et max à cette taille
        # Cela empêche l'utilisateur de tirer sur les bords
        self.setMinimumSize(QtCore.QSize(ui_width, ui_height))
        self.setMaximumSize(QtCore.QSize(ui_width, ui_height))
        
        # Optionnel : On réactive les indices de redimensionnement 
        # (Parfois nécessaire pour que les boîtes de message ne soient pas tronquées)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        
        self.iface = iface 

        # --- CONFIGURATION SCROLLAREA ---
        if hasattr(self, 'scrollArea'):
            self.scrollArea.setWidgetResizable(False)
            if hasattr(self, 'scrollAreaWidgetContents'):
                self.scrollAreaWidgetContents.setMinimumSize(QtCore.QSize(590, 1750))

        self.layer = None
        self.features_dict = {}
        self.current_fid = None

        # --- DICTIONNAIRES ---
        # Contient les valeurs à renseigner dans la table, pour les listes déroulantes 
        self.dict_rnx = {"-- À renseigner --": "NULL", "Le site ne correspond à aucune réserve": 0, "Le site correspond à une Réserve Naturelle Nationalle (RNN)": 1, "Le site correspond à une Réserve Naturelle Régionale (RNR)": 2, "Le site correspond exactement à une Réserve Naturelle Corse (RNC)": 3}
        self.dict_militaire = {"-- À renseigner --": "NULL", "OUI": 1, "NON": 0}
        self.dict_type_milieu = {"-- À renseigner --": "NULL", "Inconnu" : "0", "Toubière et Marais" : "1", "Pelouses sèches" : "2", "Landes, fruticées et prairies" : "3", "Écosystèmes alluviaux" : "4", "Gîtes à Chiroptères" : "5", "Écosystèmes littoraux et marins" : "6", "Écosystèmes aquatiques" : "7", "Écosystèmes forestiers" : "8", "Écosystèmes lacustres" : "9", "Milieux variés" : "10", "Milieux rupestres ou rocheux" : "11", "Milieux artificialisés (carrières, terrils, gravières ...)" : "12", "Sites géologiques" : "13", "Écosystèmes montagnards" : "14", "Autres" : "16"}
        self.dict_nature = {"-- À renseigner --": "NULL", "Ne sais pas": "N", "Vrai": "V", "Faux": "F"}
        self.dict_geol = {"-- À renseigner --": "NULL", "Ne sais pas": "N", "Vrai": "V", "Faux": "F"}
        self.dict_carto = {"-- À renseigner --": "NULL", "Site non cartographié": 0, "Site partiellement cartographié": 1, "Site entièrement cartographié": 2}
        self.dict_typo = {"-- À renseigner --": "NULL", "Inconnue": 0, "Corine biotopes": 1, "EUNIS": 2, "Prodromes des végétations de France (PVF)": 3, "Autre": 4}
        self.dict_doc_pres = {"-- À renseigner --": "NULL", "OUI": 1, "NON": 0}
        self.dict_doc_eval = {"-- À renseigner --": "NULL", "Pas d'évaluation": "Null", "Evaluation intermédiaire": "Evaluation intermédiaire", "Evaluation finale": "Evaluation finale"}
        self.dict_oui_non = {"-- À renseigner --": "NULL", "OUI": 1, "NON": 0}

        self.dict_geol_step = {
            "-- À renseigner --": "", 
            "Présence d'objets géologiques": {
                "-- À renseigner --": "", 
                "Présence de patrimoine géologique": 10,
                "Patrimoine géologique identifié en se basant sur l'IRPG": {
                    "-- À renseigner --": "",
                    "Le site correspond exactement à un périmètre IRPG": {"-- À renseigner --": "", "Patrimoine géologique géré": 1111, "Patrimoine géologique non géré": 1112},
                    "Le site est contenu entièrement au sein d'un périmètre IRPG": {"-- À renseigner --": "", "Patrimoine géologique géré": 1121, "Patrimoine géologique non géré": 1122},
                    "Le site contient entièrement un périmètre IRPG": {"-- À renseigner --": "", "Patrimoine géologique géré": 1131, "Patrimoine géologique non géré": 1132},
                    "Le site intersecte un périmètre IRPG": {"-- À renseigner --": "", "Patrimoine géologique géré": 1141, "Patrimoine géologique non géré": 1142} 
                },
                "Patrimoine géologique identifié à dire d'expert": {
                    "-- À renseigner --": "", "Site à vocation géologique, géré pour cela": 121,
                    "Site géré pour sa biodiversité mais qui présente également du patrimoine géolgique": {"-- À renseigner --": "", "Patrimoine géologique géré": 1221, "Patrimoine géologique non géré": 1222}
                },
            }, 
            "Site à vocation purement biologique": {"-- À renseigner --": "", "Absence de site géologique en limite ou dans le voisinage": 21, "Présence d'un site géologique en limite ou dans le voisinage": 22}, 
            "On ne sais pas si le site présente des objets géologiques...": {"-- À renseigner --": "", "Absence de site géologique en limite ou dans le voisinage": 31, "Présence d'un site géologique en limite ou dans le voisinage": 32},
            "Objets géologiques ordinaires...": {"-- À renseigner --": "", "Absence de site géologique en limite ou dans le voisinage": 41, "Présence d'un site géologique en limite ou dans le voisinage": 42}
        }

        # Dictionnaire permettant la connexion entre les champs de la table SIG et les variables du script python
        self.field_map = {
            "site_lien_rnx": self.cbLienRNX, "site_rnx_surface_m2": self.spinRNX,
            "terrain_militaire": self.cbMilitaire, "nbre_contrat_agri": self.spinContrats,
            "nb_agri": self.spinAgri, "surf_contra_m2": self.spinSurfContrat,
            "code_milieu_princ": self.cbType_milieu, "nature_site_inpn": self.cbNatureInpn,
            "geol_site_inpn": self.cbGeolInpn, "carto_habitats": self.cbCartoHab,
            "typo_carto_habitat": self.cbTypoHab, "gestionnaire_site": self.txtGestionnaire,
            "surf_libre_evolution_m2": self.spinLibreEvo, "doc_gestion_presence": self.cbDocPres,
            "doc_gestion_nom": self.txtDocNom, "doc_gestion_evaluation": self.cbDocEval,
            "surf_doc_gestion_m2": self.spinSurfDoc, "url_fiche_inpn": self.txtUrlInpn,
            "url_fiche_cen": self.txtUrlCen, "ouverture_public": self.cbOuverture,
            "description_site": self.txtDescription, "url_site_photo": self.txtUrlPhoto,
            "sensibilite": self.cbSensibilite, "non_diffusion": self.cbNonDiffusion,
            "remq_sensibilite": self.txtRemqSensibilite, "code_geol": self.txtGeolResult,
            "doc_gestion_date_ini": self.dateIni, "doc_gestion_date_maj": self.dateMaj, "doc_gestion_date_fin": self.dateFin
        }

        self.init_ui_elements()
        self.setup_tooltips()
        self.connect_signals()

    def setup_tooltips(self):
        """
        Configuration des infobulles (utilisation de la méthode TOOLTIPS)
        """
        self.label_rnx.setToolTip("Le site est-il inclus dans une réserve naturelle (nationale, régionale, corse) ?")
        self.label_num.setToolTip("Surface totale du site déclarée dans le cadre de la RNX (en m²).")
        self.label_militaire.setToolTip("Le site est-il un terrain militaire ? (entièrement ou en partie)")
        self.label_contrats.setToolTip("Nombre de contrats agricole (0 est une réponse possible).")
        self.label_agri.setToolTip("Nombre d’agriculteurs sous contrat (écrit ou oral) sur le site (0 est une réponse possible).")
        self.label_surf_contrat.setToolTip("Superficie (en m²) du site sous contrat (écrit ou oral) avec un ou N agriculteurs (0 est une réponse possible).")
        self.label_type_milieu.setToolTip("Milieu naturel prédominant sur le site.")
        self.label_nature.setToolTip("Le site est-il classé pour protéger des éléments du patrimoine naturel ?")
        self.label_geol.setToolTip("Le site est-il classé pour protéger des éléments du patrimoine géologique ?")
        self.groupGeolDecision.setToolTip("Quel est l'intérêt géologique du sites ? Utilisez les listes pour générer le code géologique du site.")
        self.label_carto_hab.setToolTip("Existe-t-il une cartographie d'habitats naturels sur le site ?")
        self.label_typo_hab.setToolTip("Typologie utilisée pour la cartographie d'habitats ou de végétation.")
        self.label_gestionnaire.setToolTip("Organisme localement responsable de la gestion de l'espace naturel protégé.")
        self.label_surf_libre.setToolTip("Surface du site laissée en libre évolution (en m²).")
        self.label_doc_pres.setToolTip("Existe-t-il un plan de gestion ou un document notifiant l'action du CEN ?")
        self.label_doc_nom.setToolTip("Titre complet du document de gestion en vigueur.")
        self.label_doc_eval.setToolTip("Résultat de la dernière évaluation du plan de gestion.")
        self.label_date_ini.setToolTip("Date de mise en œuvre initiale du document de gestion.")
        self.label_date_maj.setToolTip("Date de la dernière mise à jour du document.")
        self.label_date_fin.setToolTip("Date d'échéance ou de fin de validité du document.")
        self.label_surf_doc.setToolTip("Surface couverte par le document de gestion actuel (en m²).")
        self.label_url_inpn.setToolTip("Lien direct vers la fiche de l'inventaire national du patrimoine naturel.")
        self.label_url_cen.setToolTip("Lien vers la page dédiée sur le site web du CEN.")
        self.label_ouverture.setToolTip("Le site est-il accessible au public ?")
        self.label_desc.setToolTip("Résumé des enjeux et caractéristiques principales du site.")
        self.label_url_photo.setToolTip("Lien vers une photographie représentative du paysage.")
        self.label_sensi.setToolTip("Le site est-il sensible à la diffusion ?")
        self.label_diffusion.setToolTip("Si il est sensible a la diffusion, est-ce pour des raisons de partenariat ?")
        self.label_remq_sensi.setToolTip("Précisions sur les raisons de la sensibilité ou de la non-diffusion.")

    def apply_highlight(self, widget, is_invalid):
        """
        Applique le style rouge si le champ est vide ou considéré comme étant invalide. Utilisation de la méthode STYLESHEET.
        """
        if is_invalid:
            widget.setStyleSheet("background-color: #ffe6e6; border: 1px solid #ff4d4d; border-radius: 3px;")
        else:
            widget.setStyleSheet("")

    def check_field_validity(self):
        """
        Vérifie tous les champs, pour permettre la mise en surbrillance.
        """
        # ComboBoxes standards (listes de valeurs)
        combos = [self.cbLienRNX, self.cbMilitaire, self.cbType_milieu, self.cbNatureInpn, 
                self.cbGeolInpn, self.cbCartoHab, self.cbTypoHab, self.cbDocPres, 
                self.cbDocEval, self.cbOuverture, self.cbSensibilite, self.cbNonDiffusion]
        
        # ComboBoxes de la cascade géologique
        geol_combos = [self.cbGeolStep1, self.cbGeolStep2, self.cbGeolStep3, self.cbGeolStep4]
        
        for cb in (combos + geol_combos):
            # On vérifie si l'élément est visible (pour éviter de colorer des listes vides cachées)
            # et si le texte est celui par défaut
            is_invalid = cb.currentText() == "-- À renseigner --" or cb.currentText() == ""
            self.apply_highlight(cb, is_invalid)
        
        # SpinBoxes (Listes numériques)
        spins = [self.spinRNX, self.spinContrats, self.spinAgri, self.spinSurfContrat, 
                self.spinLibreEvo, self.spinSurfDoc]
        for s in spins:
            self.apply_highlight(s, s.value() <= -1)

        # LineEdits (Edition de texte (Une seule ligne))
        lines = [self.txtGestionnaire, self.txtDocNom, self.txtUrlInpn, self.txtUrlCen, self.txtUrlPhoto]
        for l in lines:
            self.apply_highlight(l, l.text().strip() == "")

        # TextEdits (Edition de texte (Multi-lignes))
        self.apply_highlight(self.txtDescription, self.txtDescription.toPlainText().strip() == "")
        self.apply_highlight(self.txtRemqSensibilite, self.txtRemqSensibilite.toPlainText().strip() == "")

    def save_current_feature(self):
        """
        Permet de récupérer les valeur saisies dans le formulaire, puis de les retranscrires au sein de la couche SIG
        """
        # Option de sécurité, permet de vérifier si un élément a bien été saisie dans l'éléménet 'listSites' et de vérifier si la couche SIG a bien été chargée
        items = self.listSites.selectedItems()
        if not items or not self.layer: return False
        
        # Permet la récupération du FID (l'identifiant unique) du polygone dans la couche SIG des sites
        item = items[0]
        fid = item.data(QtCore.Qt.UserRole)
        data_to_save = {}
        all_dicos = [self.dict_rnx, self.dict_militaire, self.dict_type_milieu, self.dict_nature, self.dict_geol, self.dict_carto, self.dict_typo, self.dict_doc_pres, self.dict_doc_eval, self.dict_oui_non]

        # Option permettant de parcourir tous les champs du formulaire
        for field, widget in self.field_map.items():
            if isinstance(widget, QtWidgets.QComboBox):
                val = "NULL"
                for dico in all_dicos:
                    if widget.currentText() in dico:
                        val = dico[widget.currentText()]; break
                data_to_save[field] = NULL if val == "NULL" else val
            elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                data_to_save[field] = NULL if widget.value() <= -1 else widget.value()
            elif isinstance(widget, QtWidgets.QDateEdit):
                data_to_save[field] = widget.date()
            else:
                txt = widget.toPlainText() if hasattr(widget, 'toPlainText') else widget.text()
                data_to_save[field] = txt.strip() if txt.strip() else NULL

        # Passage de la couche SIG en mode édition, récupère l'index de l'entité dans la table attributaire et modifie la valeur pour l'objet (fid) concerné
        self.layer.startEditing()
        for field, val in data_to_save.items():
            idx = self.layer.fields().indexFromName(field)
            if idx != -1:
                self.layer.changeAttributeValue(fid, idx, val)

        # Si la modification a été effectué, la boucle va enregistrer physiquement les modifications 
        if self.layer.commitChanges():
            # Permet d'enregistre le 'cache' sans devoir relire toute la couche SIG entière
            for f, v in data_to_save.items():
                self.features_dict[fid][f] = v
            
            #Application de nos fonctions de  et de
            self.set_item_style(item, self.is_feature_incomplete(self.features_dict[fid]))
            self.refresh_stats()

            if self.iface:
                self.iface.messageBar().pushMessage("Succès", "Données sauvegardées", level=0)
            else:
                QtWidgets.QMessageBox.information(self, "Succès", "Données sauvegardées.")
            return True
        else:
            # Permet de de tout annuler si l'écriture, on revient à l'état initial pour ne pas laisser de données corrompues en mémoire
            self.layer.rollBack()
            QtWidgets.QMessageBox.warning(self, "Erreur", "La sauvegarde a échoué.")
            return False

    def is_feature_incomplete(self, feat):
        """
        Permet de définir quels sont les champs obligatoires à renseigner pour pouvoir valider le formulaire 
        """
        # Permet de repérer et définir ce qu'est un dossier vide dans notre couche SIG 
        def is_empty(v): 
            return v is None or v == NULL or str(v) == 'NULL' or str(v).strip() == ""
        # Champs obligatoires à saisir pour valider le formulaire de saisie 
        return (is_empty(feat['terrain_militaire']) or 
                feat['site_rnx_surface_m2'] in [None, NULL, -1] or 
                is_empty(feat['gestionnaire_site']) or 
                is_empty(feat['description_site']))
        
    def refresh_stats(self):
        """
        Permet de décompter le nombre de sites à compléter sur le nombre total de sites
        """
        total = self.listSites.count()
        inc = sum(1 for i in range(total) 
                if self.is_feature_incomplete(self.features_dict[self.listSites.item(i).data(QtCore.Qt.UserRole)]))
        self.setWindowTitle(f"Gestionnaire CEN - {inc} à compléter sur {total}")

    def set_item_style(self, item, incomplete):
        """
        Permet de passer les champs incomplet en rouge et en gras
        """
        font = item.font()
        item.setForeground(QtGui.QColor('red' if incomplete else 'black'))
        font.setBold(incomplete)
        item.setFont(font)

    def on_selection_changed(self):
        """
        Permet d'associer les descriptions des différents champs en fonction de la valeur contenue dans les dictionnaires de données
        """
        # Identification du site sélectionné, récupération de l'élément cliqué dans la liste 
        items = self.listSites.selectedItems()
        if not items: return
        self.current_fid = items[0].data(QtCore.Qt.UserRole)
        feat = self.features_dict[self.current_fid]
        
        # Blocage du signal entre le formulaire et la table attributaire de la couche SIG
        # (permet d'éviter au formulaire de devoir refaire des calculs si l'on possède des formules effectuant des calculs automatiques)
        self.blockSignals(True)
        all_dicos = [self.dict_rnx, self.dict_militaire, self.dict_type_milieu, self.dict_nature, self.dict_geol, self.dict_carto, self.dict_typo, self.dict_doc_pres, self.dict_doc_eval, self.dict_oui_non]
        
        # Cherche dans tous les dictionnaires de données (que l'on a mis en place au début) les clés associées aux valeurs correspondants aux valeurs brutes des tables SIG (jointure attributaire en quelque sorte)
        for field, widget in self.field_map.items():
            val = feat[field]
            if isinstance(widget, QtWidgets.QComboBox):
                found = False
                for dico in all_dicos:
                    for k, v in dico.items():
                        if str(v) == str(val): widget.setCurrentText(k); found = True; break
                    if found: break
                if not found: widget.setCurrentText("-- À renseigner --")
            elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                widget.setValue(int(val) if val is not None and str(val) != 'NULL' else -1)
            elif isinstance(widget, QtWidgets.QDateEdit):
                widget.setDate(val if val and hasattr(val, 'isValid') and val.isValid() else QtCore.QDate.currentDate())
            elif isinstance(widget, QtWidgets.QLineEdit): widget.setText(str(val) if val and str(val) != 'None' else "")
            elif isinstance(widget, QtWidgets.QTextEdit): widget.setPlainText(str(val) if val and str(val) != 'None' else "")
        
        # Déblocage du signal entre le formulaire et la table, relance de la fonction de vérification pour la validation des champs
        self.blockSignals(False)
        self.check_field_validity()
        if hasattr(self, 'scrollArea'): self.scrollArea.setFocus()

    def connect_signals(self):
        """
        Permet la connexion entre nos widgets et nos fonctions 
        """
        # Mise en place des connexions principales (Naviguation et Boutons)
        self.txtSearch.textChanged.connect(self.filter_list)
        self.listSites.itemSelectionChanged.connect(self.on_selection_changed)
        self.btnApply.clicked.connect(self.save_current_feature)
        self.button_box.accepted.connect(self.save_and_close)
        self.button_box.rejected.connect(self.reject)
        
        # Mise en place de la surveillance automatique (Validation en temps réel)
        for widget in self.field_map.values():
            if isinstance(widget, QtWidgets.QComboBox): widget.currentIndexChanged.connect(self.check_field_validity)
            elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)): widget.valueChanged.connect(self.check_field_validity)
            elif isinstance(widget, QtWidgets.QLineEdit): widget.textChanged.connect(self.check_field_validity)
            elif isinstance(widget, (QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit)): widget.textChanged.connect(self.check_field_validity)

        # Mise en place des listes en cascades (Le système Géologique)
        self.cbGeolStep1.currentIndexChanged.connect(lambda: self.update_geol_cascade(1))
        self.cbGeolStep2.currentIndexChanged.connect(lambda: self.update_geol_cascade(2))
        self.cbGeolStep3.currentIndexChanged.connect(lambda: self.update_geol_cascade(3))
        self.cbGeolStep4.currentIndexChanged.connect(self.update_final_geol_code)

    def populate_list(self, layer):
        """ 
        Passerelle entre QGIS et l'interface
        """
        self.layer = layer
        self.listSites.clear()
        self.features_dict.clear()
        if not self.layer: return
        
        # Scannage de la couche SIG 
        for feat in self.layer.getFeatures():
            fid = feat.id()
            self.features_dict[fid] = feat
            
            # Création de notre interface visuelle
            nom = str(feat['NOM_SITE']) if feat['NOM_SITE'] else f"ID {fid}"
            item = QtWidgets.QListWidgetItem(nom)
            item.setData(QtCore.Qt.UserRole, fid)
            
            # Mise en forme et statistiques 
            self.set_item_style(item, self.is_feature_incomplete(feat))
            self.listSites.addItem(item)
        self.refresh_stats()

    def save_and_close(self):
        """
        Fonction permettant de sauvegarder et de quitter le plugin (connecté à un boutton)
        """
        if self.save_current_feature():
            self.accept()

    def init_ui_elements(self):
        """
        Permet de remplir de remplir les widgets au moment de l'ouverture du plugin
        """
        # Configuration des dictionnaires temporaires, permettant d'associer le widget au dictionnaire de donnée
        config = {self.cbLienRNX: self.dict_rnx, self.cbMilitaire: self.dict_militaire, self.cbType_milieu: self.dict_type_milieu, self.cbCartoHab: self.dict_carto, self.cbTypoHab: self.dict_typo, self.cbDocPres: self.dict_doc_pres, self.cbOuverture: self.dict_oui_non, self.cbSensibilite: self.dict_oui_non, self.cbNonDiffusion: self.dict_oui_non, self.cbNatureInpn: self.dict_nature, self.cbGeolInpn: self.dict_geol, self.cbDocEval: self.dict_doc_eval}
        
        # Boucle de remplissage automatique des valeurs dans les dictionnaires 
        for cb, d in config.items():
            cb.clear(); cb.addItems(d.keys())
        
        # Cas à part de la Géologie, permet de seulement remplir la 1ere colonne     
        self.cbGeolStep1.clear(); 
        self.cbGeolStep1.addItems(self.dict_geol_step.keys())

    def update_geol_cascade(self, step):
        """
        Permet la mise à jours de nos menus, pour la partie géologique de notre formulaire 
        """
        # Blocage du signal entre le formulaire et la table attributaire de la couche SIG
        self.blockSignals(True)
        t1, t2, t3 = self.cbGeolStep1.currentText(), self.cbGeolStep2.currentText(), self.cbGeolStep3.currentText()
        
        # Vérifier si c'est bien la première ligne qui a été sélectionné 
        if step == 1:
            # Reset des valeurs des autres listes si il y a eu des saisies 
            self.cbGeolStep2.clear(); self.cbGeolStep3.clear(); self.cbGeolStep4.clear()
            # Recherche de la branche correspondante 
            node = self.dict_geol_step.get(t1)
            # Si c'est un dictionnaire, alors on récupère toutes les clés liées au dictionnaire suivant, pour les réinjecter dans l'étape suivante 
            if isinstance(node, dict): self.cbGeolStep2.addItems(node.keys())
            
        # Vérifier si c'est bien la seconde ligne qui a été sélectionné             
        elif step == 2:
            # Reset des valeurs des autres listes si il y a eu des saisies 
            self.cbGeolStep3.clear(); self.cbGeolStep4.clear()
            # Recherche de la branche correspondante 
            node1 = self.dict_geol_step.get(t1, {})
            # Si c'est un dictionnaire, alors on récupère toutes les clés liées au dictionnaire suivant, pour les réinjecter dans l'étape suivante ...
            if isinstance(node1, dict):
                node2 = node1.get(t2)
                if isinstance(node2, dict): self.cbGeolStep3.addItems(node2.keys())

        # Vérifier si c'est bien la troisième ligne qui a été sélectionné                         
        elif step == 3:
            # Reset des valeurs des autres listes si il y a eu des saisies 
            self.cbGeolStep4.clear()
            # Recherche de la branche correspondante 
            node1 = self.dict_geol_step.get(t1, {})
            # Si c'est un dictionnaire, alors on récupère toutes les clés liées au dictionnaire suivant, pour les réinjecter dans l'étape suivante ...            
            if isinstance(node1, dict):
                node2 = node1.get(t2, {})
                if isinstance(node2, dict):
                    node3 = node2.get(t3)
                    if isinstance(node3, dict): self.cbGeolStep4.addItems(node3.keys())
                    
        # Relancement du signal entre le formulaire et la table attributaire + application de la fonction 'update_final_geol_code' pour les valeurs 
        self.blockSignals(False)
        self.update_final_geol_code()

    def update_final_geol_code(self):
        """
        Permet de parcourir notre arbre et de récupérer les valeurs au bout de chaque branche de notre dictionnaire, puis de faire la concaténation de tous les valeurs récupérées 
        """
        val = self.dict_geol_step
        # Boucle permettant de chekquer nos 4 listes géologiques l'une après l'autre dans l'ordre
        for cb in [self.cbGeolStep1, self.cbGeolStep2, self.cbGeolStep3, self.cbGeolStep4]:
            # Récupération du texte sélectionné par l'utilisateur pour la liste en cours
            txt = cb.currentText()
            # Arrête la boucle si : la liste est vide, c'est une valeur finale ou le texte choisit n'est pas dans le dictionnaire
            if not txt or not isinstance(val, dict) or txt not in val: break
            # La variable val définit au début de notre fonction, elle va se réduire en fonction de la sous-partie du dictionnaire correpondant au choix de l'utilisateur 
            val = val[txt]
            # Détection du résultat final, si val n'est plus un dictionnaire, on arrête tout et on affiche le résultat final 
            if not isinstance(val, dict): 
                self.txtGeolResult.setText(str(val))
                return
        # Si la boucle s'est arrêté prématurément (à cause du break) sans arriver au bout, alors on efface le code final car incomplet 
        self.txtGeolResult.clear()

    def filter_list(self):
        """
        Fonction filtre, permettant de retrouver plus rapidement un site grâce à la barre de recherche 
        """
        # Récupération de la saisie de l'utilisateur et le convertit en minuscule pour éviter la casse au moment de la saisie
        txt = self.txtSearch.text().lower()
        # Boucle permettant de parcourir l'intégralité de nos sites, et de masquer tous les noms de sites dont la saisie diffère du contenu 
        for i in range(self.listSites.count()):
            item = self.listSites.item(i)
            item.setHidden(txt not in item.text().lower())

    def eventFilter(self, obj, event):
        """
        Fonction permettant la maîtrise de la molette. Permet de régler le conflit entre les listes déroulantes et la barre de défilement
        """
        # Vérifié si l'utilisateur fait tourner sa molette 
        if event.type() == QtCore.QEvent.Wheel:
            # Si la souris survole un widget mais que l'utilisateur n'a pas cliqué dessus, on ignore l'action sur le widget
            if not obj.hasFocus(): return False 
            #Récupération du scrolling de l'utilisateur pour l'appliquer à la barre de défilement 
            if hasattr(self, 'scrollArea'):
                delta = event.angleDelta().y()
                sb = self.scrollArea.verticalScrollBar()
                sb.setValue(sb.value() - delta)
                return True
        # Permet de dire à l'applicatif d'avoir un comportement standard comme une fenêtre Windows/Linux classique 
        return super(AttributeEditorSitesCENDialog, self).eventFilter(obj, event)