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
        self.setFixedSize(self.size())
        self.iface = iface # Pour le zoom
        self.layer = None
        self.features_dict = {}
        
        # 1. Config ComboBox RNX
        self.dict_rnx = {
            "-- À renseigner --": "NULL",
            "Aucun lien avec une RNX": "0",
            "Inclus dans le périmètre RNX": "INCLUS",
            "Adjacent à une RNX": "ADJ",
            "Partiellement superposé": "SUPERP"
        }
        self.cbLienRNX.clear()
        self.cbLienRNX.addItems(self.dict_rnx.keys())

        # 2. Config ComboBox Militaire (Sécurité Tristate)
        self.dict_militaire = {
            "-- À renseigner --": "NULL",
            "Oui": "OUI",
            "Non": "NON"
        }
        self.cbMilitaire.clear()
        self.cbMilitaire.addItems(self.dict_militaire.keys())

        # --- CONNEXIONS ---
        self.txtSearch.textChanged.connect(self.filter_list)
        self.listSites.itemSelectionChanged.connect(self.on_selection_changed)
        self.btnApply.clicked.connect(self.save_current_feature)

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

            if self.is_feature_incomplete(feat):
                inc += 1
                self.set_item_style(item, True)
            else:
                self.set_item_style(item, False)
            self.listSites.addItem(item)
        self.update_title(inc, total)

    def on_selection_changed(self):
        """Action déclenchée au clic dans la liste : Affichage + Zoom."""
        items = self.listSites.selectedItems()
        if not items: return
        
        # Faire remonter l'ascenseur du formulaire en haut à chaque nouveau site
        self.scrollArea.verticalScrollBar().setValue(0)
        
        fid = items[0].data(QtCore.Qt.UserRole)
        feat = self.features_dict.get(fid)
        
        if feat:
            # Remplissage formulaire
            # Champ 1 : RNX Combo
            v_rnx = str(feat['site_lien_rnx'])
            self.cbLienRNX.setCurrentText(next((k for k, v in self.dict_rnx.items() if v == v_rnx), "-- À renseigner --"))
            
            # Champ 2 : SpinBox Surface (CORRIGÉ)
            v_surf = feat['site_rnx_surface_m2']
            self.spinRNX.setValue(int(str(v_surf)) if v_surf and str(v_surf) != 'NULL' else 0)
            
            # Champ 3 : Militaire Combo
            v_mil = str(feat['terrain_militaire']).upper() if feat['terrain_militaire'] else "NULL"
            self.cbMilitaire.setCurrentText(next((k for k, v in self.dict_militaire.items() if v == v_mil), "-- À renseigner --"))

            # ZOOM AUTOMATIQUE
            self.zoom_to_feature(feat)

    def zoom_to_feature(self, feat):
        """Centre la carte sur le site sélectionné."""
        if self.iface and feat.geometry():
            canvas = self.iface.mapCanvas()
            canvas.setExtent(feat.geometry().boundingBox())
            canvas.scaleBy(1.2)
            canvas.refresh()

    def save_current_feature(self):
        items = self.listSites.selectedItems()
        if not items or not self.layer: return

        fid = items[0].data(QtCore.Qt.UserRole)
        
        # Récupération valeurs interface
        c_rnx = self.dict_rnx[self.cbLienRNX.currentText()]
        v_surf = self.spinRNX.value()
        c_mil = self.dict_militaire[self.cbMilitaire.currentText()]
        c_mil = None if c_mil == "NULL" else c_mil

        self.layer.startEditing()
        idx_rnx = self.layer.fields().indexFromName('site_lien_rnx')
        idx_surf = self.layer.fields().indexFromName('site_rnx_surface_m2') # CORRIGÉ
        idx_mil = self.layer.fields().indexFromName('terrain_militaire')

        if idx_rnx != -1: self.layer.changeAttributeValue(fid, idx_rnx, c_rnx)
        if idx_surf != -1: self.layer.changeAttributeValue(fid, idx_surf, v_surf) # CORRIGÉ
        if idx_mil != -1: self.layer.changeAttributeValue(fid, idx_mil, c_mil)

        if self.layer.commitChanges():
            self.features_dict[fid]['site_lien_rnx'] = c_rnx
            self.features_dict[fid]['site_rnx_surface_m2'] = v_surf # CORRIGÉ
            self.features_dict[fid]['terrain_militaire'] = c_mil
            
            self.set_item_style(items[0], self.is_feature_incomplete(self.features_dict[fid]))
            self.refresh_stats()
            QtWidgets.QMessageBox.information(self, "Succès", "Données sauvegardées.")
        else:
            self.layer.rollBack()
            QtWidgets.QMessageBox.warning(self, "Erreur", "Erreur lors de l'écriture GeoPackage.")

    def is_feature_incomplete(self, feat):
        """Un site est rouge si Militaire est inconnu OU si surface est à 0."""
        # On peut aussi ajouter str(feat['site_lien_rnx']) == "NULL" si besoin
        return (feat['terrain_militaire'] is None or 
                feat['site_rnx_surface_m2'] == 0 or 
                str(feat['site_lien_rnx']) == "NULL")

    def set_item_style(self, item, inc):
        font = item.font()
        item.setForeground(QtGui.QColor('red' if inc else 'black'))
        font.setBold(inc)
        item.setFont(font)

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