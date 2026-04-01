# -*- coding: utf-8 -*-
import os
from qgis.PyQt import uic, QtWidgets, QtCore, QtGui
from qgis.core import QgsRectangle

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
        
        # Dictionnaires génériques Oui/Non/Projet
        self.dict_doc_pres = {"-- À renseigner --": "NULL", "Oui": "OUI", "Non": "NON", "En projet": "PRJ"}
        self.dict_doc_eval = {"-- À renseigner --": "NULL", "Favorable": "FAV", "Défavorable": "DEF", "En cours": "ENC"}
        self.dict_oui_non = {"-- À renseigner --": "NULL", "Oui": "OUI", "Non": "NON"}

        # Remplissage des ComboBox
        combos = {
            self.cbLienRNX: self.dict_rnx, self.cbMilitaire: self.dict_militaire,
            self.cbType_milieu: self.dict_type_milieu, self.cbNatureInpn: self.dict_nature,
            self.cbGeolInpn: self.dict_geol, self.cbCodeGeol: self.dict_code_geol,
            self.cbCartoHab: self.dict_carto, self.cbTypoHab: self.dict_typo,
            self.cbDocPres: self.dict_doc_pres, self.cbDocEval: self.dict_doc_eval,
            self.cbOuverture: self.dict_oui_non, self.cbSensibilite: self.dict_oui_non,
            self.cbNonDiffusion: self.dict_oui_non
        }
        for cb, d in combos.items():
            cb.clear()
            cb.addItems(d.keys())

        # --- CONNEXIONS ---
        self.txtSearch.textChanged.connect(self.filter_list)
        self.listSites.itemSelectionChanged.connect(self.on_selection_changed)
        self.btnApply.clicked.connect(self.save_current_feature)

        # Connexions surbrillance (excluant les textes longs)
        widgets_val = [
            self.cbLienRNX, self.cbMilitaire, self.cbType_milieu, self.cbNatureInpn,
            self.cbGeolInpn, self.cbCodeGeol, self.cbCartoHab, self.cbTypoHab,
            self.cbDocPres, self.cbDocEval, self.cbOuverture, self.cbSensibilite,
            self.cbNonDiffusion, self.spinRNX, self.spinContrats, self.spinAgri, 
            self.spinSurfContrat, self.spinLibreEvo, self.spinSurfDoc
        ]
        for w in widgets_val:
            if isinstance(w, QtWidgets.QComboBox): w.currentIndexChanged.connect(self.check_field_validity)
            else: w.valueChanged.connect(self.check_field_validity)
        
        self.txtGestionnaire.textChanged.connect(self.check_field_validity)
        self.txtDocNom.textChanged.connect(self.check_field_validity)

    def apply_highlight(self, widget, is_invalid):
        if is_invalid:
            widget.setStyleSheet("background-color: #ffe6e6; border: 1px solid #ff4d4d; border-radius: 3px;")
        else:
            widget.setStyleSheet("")

    def check_field_validity(self):
        self.apply_highlight(self.cbLienRNX, self.cbLienRNX.currentText() == "-- À renseigner --")
        self.apply_highlight(self.spinRNX, self.spinRNX.value() == 0)
        self.apply_highlight(self.cbMilitaire, self.cbMilitaire.currentText() == "-- À renseigner --")
        self.apply_highlight(self.txtGestionnaire, self.txtGestionnaire.text().strip() == "")
        self.apply_highlight(self.cbDocPres, self.cbDocPres.currentText() == "-- À renseigner --")
        self.apply_highlight(self.cbSensibilite, self.cbSensibilite.currentText() == "-- À renseigner --")

    def on_selection_changed(self):
        items = self.listSites.selectedItems()
        if not items: return
        
        self.scrollArea.verticalScrollBar().setValue(0)
        fid = items[0].data(QtCore.Qt.UserRole)
        feat = self.features_dict.get(fid)
        
        if feat:
            self.blockSignals(True)
            
            # Helper pour retrouver le texte d'un dictionnaire par sa valeur
            def get_key(dico, val): return next((k for k, v in dico.items() if v == str(val)), "-- À renseigner --")

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

            # Textes (simples)
            self.txtGestionnaire.setText(str(feat['gestionnaire_site']) if feat['gestionnaire_site'] else "")
            self.txtDocNom.setText(str(feat['doc_gestion_nom']) if feat['doc_gestion_nom'] else "")
            self.txtUrlInpn.setText(str(feat['url_fiche_inpn']) if feat['url_fiche_inpn'] else "")
            self.txtUrlCen.setText(str(feat['url_fiche_cen']) if feat['url_fiche_cen'] else "")
            self.txtUrlPhoto.setText(str(feat['url_site_photo']) if feat['url_site_photo'] else "")

            # Textes (multi-lignes QTextEdit)
            self.txtDescription.setPlainText(str(feat['description_site']) if feat['description_site'] else "")
            self.txtRemqSensibilite.setPlainText(str(feat['remq_sensibilite']) if feat['remq_sensibilite'] else "")

            # SpinBoxes
            def set_spin(w, val): w.setValue(int(float(str(val))) if val and str(val) != 'NULL' else 0)
            set_spin(self.spinRNX, feat['site_rnx_surface_m2'])
            set_spin(self.spinContrats, feat['nbre_contrat_agri'])
            set_spin(self.spinAgri, feat['nb_agri'])
            set_spin(self.spinSurfContrat, feat['surf_contra_m2'])
            set_spin(self.spinLibreEvo, feat['surf_libre_evolution_m2'])
            set_spin(self.spinSurfDoc, feat['surf_doc_gestion_m2'])

            # Dates
            for f, w in [('doc_gestion_date_ini', self.dateIni), ('doc_gestion_date_maj', self.dateMaj), ('doc_gestion_date_fin', self.dateFin)]:
                val = feat[f]
                w.setDate(val if val and val.isValid() else QtCore.QDate.currentDate())

            self.blockSignals(False)
            self.check_field_validity()
            self.zoom_to_feature(feat)

    def save_current_feature(self):
        items = self.listSites.selectedItems()
        if not items or not self.layer: return
        fid = items[0].data(QtCore.Qt.UserRole)

        data = {
            'site_lien_rnx': self.dict_rnx[self.cbLienRNX.currentText()],
            'site_rnx_surface_m2': self.spinRNX.value(),
            'terrain_militaire': self.dict_militaire[self.cbMilitaire.currentText()],
            'nbre_contrat_agri': self.spinContrats.value(),
            'nb_agri': self.spinAgri.value(),
            'surf_contra_m2': self.spinSurfContrat.value(),
            'code_milieu_princ': self.dict_type_milieu[self.cbType_milieu.currentText()],
            'nature_site_inpn': self.dict_nature[self.cbNatureInpn.currentText()],
            'geol_site_inpn': self.dict_geol[self.cbGeolInpn.currentText()],
            'code_geol': self.dict_code_geol[self.cbCodeGeol.currentText()],
            'carto_habitats': self.dict_carto[self.cbCartoHab.currentText()],
            'typo_carto_habitat': self.dict_typo[self.cbTypoHab.currentText()],
            'gestionnaire_site': self.txtGestionnaire.text(),
            'surf_libre_evolution_m2': self.spinLibreEvo.value(),
            'doc_gestion_presence': self.dict_doc_pres[self.cbDocPres.currentText()],
            'doc_gestion_nom': self.txtDocNom.text(),
            'doc_gestion_evaluation': self.dict_doc_eval[self.cbDocEval.currentText()],
            'doc_gestion_date_ini': self.dateIni.date(),
            'doc_gestion_date_maj': self.dateMaj.date(),
            'doc_gestion_date_fin': self.dateFin.date(),
            'surf_doc_gestion_m2': self.spinSurfDoc.value(),
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
            if idx != -1: self.layer.changeAttributeValue(fid, idx, val if val != "NULL" else None)

        if self.layer.commitChanges():
            for f, v in data.items(): self.features_dict[fid][f] = v
            self.set_item_style(items[0], self.is_feature_incomplete(self.features_dict[fid]))
            self.refresh_stats()
            QtWidgets.QMessageBox.information(self, "Succès", "Données sauvegardées.")
        else:
            self.layer.rollBack()
            QtWidgets.QMessageBox.warning(self, "Erreur", "La sauvegarde a échoué.")

    def is_feature_incomplete(self, feat):
        # Logique simplifiée : Rouge si des champs clés sont vides ou par défaut
        return (str(feat['terrain_militaire']) == "NULL" or 
                feat['site_rnx_surface_m2'] == 0 or 
                str(feat['sensibilite']) == "NULL")

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