# -*- coding: utf-8 -*-
import os
from qgis.PyQt import uic, QtWidgets, QtCore, QtGui

UI_FILE = os.path.join(os.path.dirname(__file__), 'plugin_sites_cen_dialog_base.ui')
FORM_CLASS, _ = uic.loadUiType(UI_FILE)

class AttributeEditorSitesCENDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        super(AttributeEditorSitesCENDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface 
        self.layer = None
        self.features_dict = {}
        
        # --- CONFIGURATION DES DICTIONNAIRES ---
        self.dict_rnx = {
            "-- À renseigner --": "NULL",
            "Aucun lien avec une RNX": "0",
            "Inclus dans le périmètre RNX": "INCLUS",
            "Adjacent à une RNX": "ADJ",
            "Partiellement superposé": "SUPERP"
        }
        self.dict_militaire = {"-- À renseigner --": "NULL", "Oui": "OUI", "Non": "NON"}
        self.dict_type_milieu = {
            "-- À renseigner --": "NULL", "Inconnu" : "0", "Toubière et Marais" : "1",
            "Pelouses sèches" : "2", "Landes, fruticées et prairies" : "3",
            "Écosystèmes alluviaux" : "4", "Gîtes à Chiroptères" : "5",
            "Écosystèmes littoraux et marins" : "6", "Écosystèmes aquatiques" : "7",
            "Écosystèmes forestiers" : "8", "Écosystèmes lacustres" : "9",
            "Milieux variés" : "10", "Milieux rupestres ou rocheux" : "11",
            "Milieux artificialisés (carrières, terrils, gravières ...)" : "12",
            "Sites géologiques" : "13", "Écosystèmes montagnards" : "14", "Autres" : "16"
        }
        self.dict_nature = {"-- À renseigner --": "NULL", "Naturel": "NAT", "Semi-naturel": "SEMI", "Artificiel": "ART"}
        self.dict_geol = {"-- À renseigner --": "NULL", "Sédimentaire": "SED", "Magmatique": "MAG", "Métamorphique": "MET"}
        self.dict_code_geol = {
            "-- À renseigner --": "NULL", "Calcaires et marnes": "CALC", "Sables et grès": "SAB",
            "Schistes et quartzites": "SCH", "Granites et gneiss": "GRA",
            "Alluvions et dépôts récents": "ALLU", "Tourbe": "TOU"
        }
        self.dict_carto = {"-- À renseigner --": "NULL", "Réalisée": "OUI", "Non réalisée": "NON", "En cours": "EN_COURS"}
        self.dict_typo = {"-- À renseigner --": "NULL", "EUNIS": "EUNIS", "Prodrome": "PROD", "Cahiers d'habitats": "CAH", "Corine Biotope": "CORINE"}
        self.dict_doc_pres = {"-- À renseigner --": "NULL", "Oui": "OUI", "Non": "NON", "En projet": "PRJ"}
        self.dict_doc_eval = {"-- À renseigner --": "NULL", "Favorable": "FAV", "Défavorable": "DEF", "En cours": "ENC"}
        self.dict_oui_non = {"-- À renseigner --": "NULL", "Oui": "OUI", "Non": "NON"}
        
        # --- CONFIGURATION DES INFOBULLES (TOOLTIPS) ---
        self.label_rnx.setToolTip("Le site est-il inclus dans une réserve naturelle (nationale, régionale, corse) ?")
        self.label_num.setToolTip("Surface totale du site déclarée dans le cadre de la RNX (en m²).")
        self.label_militaire.setToolTip("Le site est-il un terrain militaire ? (entièrement ou en partie)")
        self.label_contrats.setToolTip("Nombre de contrats agricole.")
        self.label_agri.setToolTip("Nombre d’agriculteurs sous contrat (écrit ou oral) sur le site.")
        self.label_surf_contrat.setToolTip("Superficie (en m²) du site sous contrat (écrit ou oral) avec un ou N agriculteurs.")
        self.label_type_milieu.setToolTip("Milieu naturel prédominant sur le site.")
        self.label_nature.setToolTip("Le site est classé pour protéger des éléments du patrimoine naturel ?")
        self.label_geol.setToolTip("Le site est classé pour protéger des éléments du patrimoine géologique ?")
        self.label_code_geol.setToolTip("L'intérêt géologique du site.")
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
        self.label_diffusion.setToolTip("Si 'Oui', les données précises ne seront pas diffusées publiquement.")
        self.label_remq_sensi.setToolTip("Précisions sur les raisons de la sensibilité ou de la non-diffusion.")

        # Remplissage des ComboBox
        self.combos_map = {
            self.cbLienRNX: self.dict_rnx, self.cbMilitaire: self.dict_militaire,
            self.cbType_milieu: self.dict_type_milieu, self.cbNatureInpn: self.dict_nature,
            self.cbGeolInpn: self.dict_geol, self.cbCodeGeol: self.dict_code_geol,
            self.cbCartoHab: self.dict_carto, self.cbTypoHab: self.dict_typo,
            self.cbDocPres: self.dict_doc_pres, self.cbDocEval: self.dict_doc_eval,
            self.cbOuverture: self.dict_oui_non, self.cbSensibilite: self.dict_oui_non,
            self.cbNonDiffusion: self.dict_oui_non
        }
        for cb, d in self.combos_map.items():
            cb.clear()
            cb.addItems(d.keys())

        # --- CONNEXIONS ---
        self.txtSearch.textChanged.connect(self.filter_list)
        self.listSites.itemSelectionChanged.connect(self.on_selection_changed)
        self.btnApply.clicked.connect(self.save_current_feature)

        # Liste des widgets pour la surveillance (Auto-Highlight)
        self.widgets_to_watch = [
            self.cbLienRNX, self.cbMilitaire, self.cbDocPres, self.cbSensibilite,
            self.spinRNX, self.spinContrats, self.spinAgri, self.spinSurfContrat, 
            self.cbType_milieu, self.cbNatureInpn, self.cbGeolInpn, self.cbCodeGeol, 
            self.cbCartoHab, self.cbTypoHab, self.txtGestionnaire, 
            self.spinLibreEvo, self.txtDocNom, self.cbDocEval, self.spinSurfDoc,
            self.txtUrlInpn, self.txtUrlCen, self.cbOuverture, self.txtUrlPhoto, self.cbNonDiffusion,
            self.dateIni, self.dateMaj, self.dateFin # Réintégration des dates
        ]
        
        for w in self.widgets_to_watch:
            if isinstance(w, QtWidgets.QComboBox):
                w.currentIndexChanged.connect(self.check_field_validity)
            elif isinstance(w, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                w.valueChanged.connect(self.check_field_validity)
            elif isinstance(w, QtWidgets.QLineEdit):
                w.textChanged.connect(self.check_field_validity)
            elif isinstance(w, QtWidgets.QDateEdit):
                w.dateChanged.connect(self.check_field_validity)

        self.txtDescription.textChanged.connect(self.check_field_validity)
        self.txtRemqSensibilite.textChanged.connect(self.check_field_validity)

    def apply_highlight(self, widget, is_invalid):
        if is_invalid:
            widget.setStyleSheet("background-color: #ffe6e6; border: 1px solid #ff4d4d; border-radius: 3px;")
        else:
            widget.setStyleSheet("")

    def check_field_validity(self):
        """Vérifie la validité des champs et applique le style rouge"""
        self.apply_highlight(self.cbLienRNX, self.cbLienRNX.currentText() == "-- À renseigner --")
        self.apply_highlight(self.spinRNX, self.spinRNX.value() == -1)
        self.apply_highlight(self.cbMilitaire, self.cbMilitaire.currentText() == "-- À renseigner --")
        self.apply_highlight(self.spinContrats, self.spinContrats.value() == -1)
        self.apply_highlight(self.spinAgri, self.spinAgri.value() == -1)
        self.apply_highlight(self.spinSurfContrat, self.spinSurfContrat.value() == -1)
        self.apply_highlight(self.cbType_milieu, self.cbType_milieu.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbNatureInpn, self.cbNatureInpn.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbGeolInpn, self.cbGeolInpn.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbCodeGeol, self.cbCodeGeol.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbCartoHab, self.cbCartoHab.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbTypoHab, self.cbTypoHab.currentText() == "-- À renseigner --")
        self.apply_highlight(self.spinLibreEvo, self.spinLibreEvo.value() == -1)
        self.apply_highlight(self.txtGestionnaire, self.txtGestionnaire.text().strip() == "")
        self.apply_highlight(self.txtDocNom, self.txtDocNom.text().strip() == "")
        self.apply_highlight(self.cbDocEval, self.cbDocEval.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbDocPres, self.cbDocPres.currentText() == "-- À renseigner --")
        self.apply_highlight(self.spinSurfDoc, self.spinSurfDoc.value() == -1)
        self.apply_highlight(self.cbSensibilite, self.cbSensibilite.currentText() == "-- À renseigner --")
        self.apply_highlight(self.txtUrlInpn, self.txtUrlInpn.text().strip() == "")
        self.apply_highlight(self.txtUrlCen, self.txtUrlCen.text().strip() == "")
        self.apply_highlight(self.cbOuverture, self.cbOuverture.currentText() == "-- À renseigner --")
        self.apply_highlight(self.txtDescription, self.txtDescription.toPlainText().strip() == "")
        self.apply_highlight(self.txtUrlPhoto, self.txtUrlPhoto.text().strip() == "")
        self.apply_highlight(self.cbNonDiffusion, self.cbNonDiffusion.currentText() == "-- À renseigner --")
        self.apply_highlight(self.txtRemqSensibilite, self.txtRemqSensibilite.toPlainText().strip() == "")

    def on_selection_changed(self):
        items = self.listSites.selectedItems()
        if not items: return
        
        self.scrollArea.verticalScrollBar().setValue(0)
        fid = items[0].data(QtCore.Qt.UserRole)
        feat = self.features_dict.get(fid)
        
        if feat:
            self.blockSignals(True)
            
            def get_key(dico, val): 
                return next((k for k, v in dico.items() if v == str(val)), "-- À renseigner --")

            # ComboBoxes
            self.cbLienRNX.setCurrentText(get_key(self.dict_rnx, feat['site_lien_rnx']))
            self.cbMilitaire.setCurrentText(get_key(self.dict_militaire, feat['terrain_militaire']))
            self.cbType_milieu.setCurrentText(get_key(self.dict_type_milieu, feat['code_milieu_princ']))
            self.cbNatureInpn.setCurrentText(get_key(self.dict_nature, feat['nature_site_inpn']))
            self.cbGeolInpn.setCurrentText(get_key(self.dict_geol, feat['geol_site_inpn']))
            self.cbCodeGeol.setCurrentText(get_key(self.dict_code_geol, feat['code_geol']))
            self.cbCartoHab.setCurrentText(get_key(self.dict_carto, feat['carto_habitats']))
            self.cbTypoHab.setCurrentText(get_key(self.dict_typo, feat['typo_carto_habitat']))
            self.cbDocPres.setCurrentText(get_key(self.dict_doc_pres, feat['doc_gestion_presence']))
            self.cbDocEval.setCurrentText(get_key(self.dict_doc_eval, feat['doc_gestion_evaluation']))
            self.cbOuverture.setCurrentText(get_key(self.dict_oui_non, feat['ouverture_public']))
            self.cbSensibilite.setCurrentText(get_key(self.dict_oui_non, feat['sensibilite']))
            self.cbNonDiffusion.setCurrentText(get_key(self.dict_oui_non, feat['non_diffusion']))

            # Textes
            self.txtGestionnaire.setText(str(feat['gestionnaire_site']) if feat['gestionnaire_site'] else "")
            self.txtDocNom.setText(str(feat['doc_gestion_nom']) if feat['doc_gestion_nom'] else "")
            self.txtUrlInpn.setText(str(feat['url_fiche_inpn']) if feat['url_fiche_inpn'] else "")
            self.txtUrlCen.setText(str(feat['url_fiche_cen']) if feat['url_fiche_cen'] else "")
            self.txtUrlPhoto.setText(str(feat['url_site_photo']) if feat['url_site_photo'] else "")
            self.txtDescription.setPlainText(str(feat['description_site']) if feat['description_site'] else "")
            self.txtRemqSensibilite.setPlainText(str(feat['remq_sensibilite']) if feat['remq_sensibilite'] else "")

            # SpinBoxes
            def set_spin(w, val):
                if val is None or str(val).upper() == 'NULL' or str(val) == '': w.setValue(-1)
                else:
                    try: w.setValue(int(float(str(val))))
                    except: w.setValue(-1)

            set_spin(self.spinRNX, feat['site_rnx_surface_m2'])
            set_spin(self.spinContrats, feat['nbre_contrat_agri'])
            set_spin(self.spinAgri, feat['nb_agri'])
            set_spin(self.spinSurfContrat, feat['surf_contra_m2'])
            set_spin(self.spinLibreEvo, feat['surf_libre_evolution_m2'])
            set_spin(self.spinSurfDoc, feat['surf_doc_gestion_m2'])

            # RÉINSERTION DES DATES
            for field, widget in [('doc_gestion_date_ini', self.dateIni), 
                                  ('doc_gestion_date_maj', self.dateMaj), 
                                  ('doc_gestion_date_fin', self.dateFin)]:
                val = feat[field]
                widget.setDate(val if val and hasattr(val, 'isValid') and val.isValid() else QtCore.QDate.currentDate())

            self.blockSignals(False)
            self.check_field_validity()
            self.zoom_to_feature(feat)

    def save_current_feature(self):
        items = self.listSites.selectedItems()
        if not items or not self.layer: return
        fid = items[0].data(QtCore.Qt.UserRole)

        def val_or_null(spin_val):
            return None if spin_val == -1 else spin_val

        data = {
            'site_lien_rnx': self.dict_rnx[self.cbLienRNX.currentText()],
            'site_rnx_surface_m2': val_or_null(self.spinRNX.value()),
            'terrain_militaire': self.dict_militaire[self.cbMilitaire.currentText()],
            'nbre_contrat_agri': val_or_null(self.spinContrats.value()),
            'nb_agri': val_or_null(self.spinAgri.value()),
            'surf_contra_m2': val_or_null(self.spinSurfContrat.value()),
            'code_milieu_princ': self.dict_type_milieu[self.cbType_milieu.currentText()],
            'nature_site_inpn': self.dict_nature[self.cbNatureInpn.currentText()],
            'geol_site_inpn': self.dict_geol[self.cbGeolInpn.currentText()],
            'code_geol': self.dict_code_geol[self.cbCodeGeol.currentText()],
            'carto_habitats': self.dict_carto[self.cbCartoHab.currentText()],
            'typo_carto_habitat': self.dict_typo[self.cbTypoHab.currentText()],
            'gestionnaire_site': self.txtGestionnaire.text(),
            'surf_libre_evolution_m2': val_or_null(self.spinLibreEvo.value()),
            'doc_gestion_presence': self.dict_doc_pres[self.cbDocPres.currentText()],
            'doc_gestion_nom': self.txtDocNom.text(),
            'doc_gestion_evaluation': self.dict_doc_eval[self.cbDocEval.currentText()],
            'doc_gestion_date_ini': self.dateIni.date(), # Date réinsérée
            'doc_gestion_date_maj': self.dateMaj.date(), # Date réinsérée
            'doc_gestion_date_fin': self.dateFin.date(), # Date réinsérée
            'surf_doc_gestion_m2': val_or_null(self.spinSurfDoc.value()),
            'url_fiche_inpn': self.txtUrlInpn.text(),
            'url_fiche_cen': self.txtUrlCen.text(),
            'url_site_photo': self.txtUrlPhoto.text(),
            'description_site': self.txtDescription.toPlainText(),
            'remq_sensibilite': self.txtRemqSensibilite.toPlainText(),
            'ouverture_public': self.dict_oui_non[self.cbOuverture.currentText()],
            'sensibilite': self.dict_oui_non[self.cbSensibilite.currentText()],
            'non_diffusion': self.dict_oui_non[self.cbNonDiffusion.currentText()]
        }

        self.layer.startEditing()
        for field, val in data.items():
            idx = self.layer.fields().indexFromName(field)
            if idx != -1: 
                self.layer.changeAttributeValue(fid, idx, val if val != "NULL" else None)

        if self.layer.commitChanges():
            for f, v in data.items(): 
                self.features_dict[fid][f] = v
            self.set_item_style(items[0], self.is_feature_incomplete(self.features_dict[fid]))
            self.refresh_stats()
            QtWidgets.QMessageBox.information(self, "Succès", "Données sauvegardées.")
        else:
            self.layer.rollBack()
            QtWidgets.QMessageBox.warning(self, "Erreur", "La sauvegarde a échoué.")

    def is_feature_incomplete(self, feat):
        return (str(feat['terrain_militaire']) in ["NULL", "None"] or 
                feat['site_rnx_surface_m2'] in [None, -1] or 
                not feat['gestionnaire_site'] or
                not feat['description_site'])

    def set_item_style(self, item, inc):
        font = item.font()
        item.setForeground(QtGui.QColor('red' if inc else 'black'))
        font.setBold(inc)
        item.setFont(font)

    def populate_list(self, layer):
        self.layer = layer
        self.listSites.clear()
        self.features_dict.clear()
        if not self.layer: return
        total, inc = 0, 0
        for feat in self.layer.getFeatures():
            total += 1
            fid = feat.id()
            self.features_dict[fid] = feat
            nom = str(feat['NOM_SITE']) if feat['NOM_SITE'] else f"ID {fid}"
            item = QtWidgets.QListWidgetItem(nom)
            item.setData(QtCore.Qt.UserRole, fid)
            status = self.is_feature_incomplete(feat)
            if status: inc += 1
            self.set_item_style(item, status)
            self.listSites.addItem(item)
        self.update_title(inc, total)

    def zoom_to_feature(self, feat):
        if self.iface and feat.geometry():
            self.iface.mapCanvas().setExtent(feat.geometry().boundingBox())
            self.iface.mapCanvas().scaleBy(1.2)
            self.iface.mapCanvas().refresh()

    def filter_list(self):
        text = self.txtSearch.text().lower()
        for i in range(self.listSites.count()):
            item = self.listSites.item(i)
            item.setHidden(text not in item.text().lower())

    def refresh_stats(self):
        total = self.listSites.count()
        inc = sum(1 for i in range(total) if self.is_feature_incomplete(self.features_dict[self.listSites.item(i).data(QtCore.Qt.UserRole)]))
        self.update_title(inc, total)

    def update_title(self, inc, total):
        self.setWindowTitle(f"Gestionnaire CEN - {inc} à compléter sur {total}")