# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
from qgis.core import (
                        QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer, QgsRasterLayer,
                        QgsField, QgsRasterBandStats, QgsColorRampShader, QgsRasterShader,
                        QgsSingleBandPseudoColorRenderer, QgsMapSettings, QgsMapRendererCustomPainterJob,
                        QgsRectangle)
from qgis.PyQt import QtCore, QtGui, QtSql
import datetime
import pandas as pd
import os
import glob
from PyQt5.QtGui import QIcon, QColor, QImage, QPainter, QPen, QFont
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant, QCoreApplication, QSize, Qt, QPoint, QRect
import calendar
import processing
from qgis.gui import QgsMapCanvas
import glob
from PIL import Image


def read_salt_dates(self):
    # monthly time step
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    startDate = stdate.strftime("%m-%d-%Y")

    wd = APEXMOD_path_dict['MODFLOW']
    filename = "amf_RT3D_cSalt_monthly.out"
    y = ("Monthly") # Remove unnecssary lines
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
    date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
    onlyDate = [x[1] for x in date] # Only date
    data1 = [x.split() for x in data] # make each line a list
    dataList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()

    self.dlg.comboBox_rt_results_sdate.clear()
    self.dlg.comboBox_rt_results_sdate.addItems(dataList)
    self.dlg.comboBox_rt_results_edate.clear()
    self.dlg.comboBox_rt_results_edate.addItems(dataList)
    self.dlg.comboBox_rt_results_edate.setCurrentIndex(len(dataList)-1)

def create_salt_grid_shps(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Copy mf_grid shapefile to apexmf_results tree
    output_dir = APEXMOD_path_dict['apexmf_shps']
    # Create apexmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("apexmf_results"):
        apexmf_results = root.findGroup("apexmf_results")
    else:
        apexmf_results = root.insertGroup(0, "apexmf_results")
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = input1.dataProvider()
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    # monthly first
    if (
        comp != "solute" and
        self.dlg.radioButton_rt3d_m.isChecked() and
        comp != "nitrate" and
        comp != "phosphorus"
        ):
        name = "salt_{}_mon".format(comp)
        name_ext = name + ".shp"
        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
            rt_shapfile = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(
                input1, rt_shapfile,
                "utf-8", input1.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(rt_shapfile, '{0}'.format(name), 'ogr')
            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            apexmf_results = root.findGroup("apexmf_results")
            QgsProject.instance().addMapLayer(layer, False)
            apexmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Created!")
            msgBox.setText("'{}' layer has been created in 'apexmf_results' group!".format(name))
            msgBox.exec_()

def create_salt_avg_mon_shp(self):

    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    APEXMOD_path_dict = self.dirs_and_paths()
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()

    # Copy mf_grid shapefile to apexmf_results tree
    name = "salt_{}_avg_mon".format(comp)
    name_ext = name + ".shp"
    output_dir = APEXMOD_path_dict['MODFLOW']
    # Check if there is an exsting mf_head shapefile
    if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
        rt_no3_shp = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, rt_no3_shp,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(rt_no3_shp, '{0}'.format(name), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        apexmf_results = root.findGroup("apexmf_results")
        QgsProject.instance().addMapLayer(layer, False)
        apexmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("'{}' layer has been created in 'apexmf_results' group!".format(name))
        msgBox.exec_()
        msgBox = QMessageBox()


def salt_export_result(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "apexmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines

    if self.dlg.radioButton_rt3d_m.isChecked():
        filename = "amf_RT3D_cSalt_monthly.out"
        y = ("Monthly") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
        date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dataList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
        comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1]
        layerName = "salt_{}_mon".format(comp.lower())

    selectedSdate = self.dlg.comboBox_rt_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_rt_results_edate.currentText()
    # Reverse step
    dateSidx = dataList.index(selectedSdate)
    dateEidx = dataList.index(selectedEdate)
    dateList_f = dataList[dateSidx:dateEidx+1]

    layer = QgsProject.instance().mapLayersByName("{}".format(layerName))[0]
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1]

    per = 0
    self.dlg.progressBar_mf_results.setValue(0)

    for selectedDate in dateList_f:
        dateIdx = dataList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]    
        if self.dlg.radioButton_rt3d_m.isChecked():
            # Find year 
            dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
            year = dt.year
            layerN = self.dlg.comboBox_rt_layer.currentText()
            for num, line in enumerate(data1, 1):
                if (
                    (line[0] == "month:" in line) and
                    (line[1] == onlyDate_lookup in line)
                    and (line[3] == str(year) in line)
                    ):
                    ii = num # Starting line
            count = 0
            # while ((data1[count+ii][0] != 'layer:') and (data1[count+ii][1] != layer)):  # why not working?
            while not (data1[count+ii][0] == comp):
                count += 1
            stline = count+ii+2

        # print(stline)
        rt_array = []
        valCount = 0
        while valCount < layer.featureCount():
            for kk in range(len(data1[stline])):
                rt_array.append(float(data1[stline][kk]))
                valCount += 1
            stline += 1

        provider = layer.dataProvider()
        if layer.dataProvider().fields().indexFromName(selectedDate) == -1:
            field = QgsField(selectedDate, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            layer.updateFields()
        mf_hds_idx = provider.fields().indexFromName(selectedDate)
        
        tot_feats = layer.featureCount()
        count = 0        
        # Get features (Find out a way to change attribute values using another field)
        feats = layer.getFeatures()
        layer.startEditing()
        # add row number
        for f, mf_hd in zip(feats, rt_array):
            layer.changeAttributeValue(f.id(), mf_hds_idx, mf_hd)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rt.setValue(provalue)
            QCoreApplication.processEvents()
        layer.commitChanges()
        QCoreApplication.processEvents()

        # Update progress bar 
        per += 1
        progress = round((per / len(dateList_f)) *100)
        self.dlg.progressBar_rt_results.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("{} results were exported successfully!".format(layerName))
    msgBox.exec_()



# NOTE: working on
def get_salt_avg_m_df(self):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Reading ...")
    msgBox.setText("We are going to read the 'amf_RT3D_cSalt_monthly.out' file ...")
    msgBox.exec_()

    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    filename = "amf_RT3D_cSalt_monthly.out"

    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
    date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
    onlyDate = [x[1] for x in date] # Only date
    data1 = [x.split() for x in data] # make each line a list
    dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()

    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1]
    # layerName = "salt_{}_avg_mon".format(comp.lower())

    selectedSdate = self.dlg.comboBox_rt_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_rt_results_edate.currentText()
    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features

    big_df = pd.DataFrame()

    datecount = 0
    for selectedDate in dateList_f:
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        layerN = self.dlg.comboBox_rt_layer.currentText()

        for num, line in enumerate(data1, 1):
            if (
                (line[0] == "month:" in line) and
                (line[1] == onlyDate_lookup in line)
                and (line[3] == str(year) in line)
                ):
                ii = num # Starting line
        count = 0
        # while ((data1[count+ii][0] != 'layer:') and (data1[count+ii][1] != layer)):  # why not working?
        while not (data1[count+ii][0] == comp):
            count += 1
        stline = count+ii+2

        rt_array = []
        valCount = 0
        while valCount < input1.featureCount():
            for kk in range(len(data1[stline])):
                rt_array.append(float(data1[stline][kk]))
                valCount += 1
            stline += 1

        s = pd.Series(rt_array, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%Y-%m-%d"))
        big_df = pd.concat([big_df, s], axis=1)
        datecount +=1
        provalue = round(datecount/len(dateList_f)*100)
        self.dlg.progressBar_rt.setValue(provalue)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    big_df = big_df.T
    big_df.index = pd.to_datetime(big_df.index)
    self.mbig_df = big_df.groupby(big_df.index.month).mean()

    # msgBox = QMessageBox()
    # msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    # msgBox.setWindowTitle("Select!")
    # msgBox.setText("Please, select months then click EXPORT")
    # msgBox.exec_()

def selected_rt_mon(self):
    selected_months = []
    if self.dlg.checkBox_rt_jan.isChecked():
        selected_months.append(1)
    if self.dlg.checkBox_rt_feb.isChecked():
        selected_months.append(2)
    if self.dlg.checkBox_rt_mar.isChecked():
        selected_months.append(3)
    if self.dlg.checkBox_rt_apr.isChecked():
        selected_months.append(4)
    if self.dlg.checkBox_rt_may.isChecked():
        selected_months.append(5)
    if self.dlg.checkBox_rt_jun.isChecked():
        selected_months.append(6)
    if self.dlg.checkBox_rt_jul.isChecked():
        selected_months.append(7)
    if self.dlg.checkBox_rt_aug.isChecked():
        selected_months.append(8)
    if self.dlg.checkBox_rt_sep.isChecked():
        selected_months.append(9)
    if self.dlg.checkBox_rt_oct.isChecked():
        selected_months.append(10)
    if self.dlg.checkBox_rt_nov.isChecked():
        selected_months.append(11)    
    if self.dlg.checkBox_rt_dec.isChecked():
        selected_months.append(12)
    return selected_months


def export_salt_avg_m(self):
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1]
    layerName = "salt_{}_avg_mon".format(comp.lower())
    mbig_df = self.mbig_df
    selected_months = selected_rt_mon(self)
    self.layer = QgsProject.instance().mapLayersByName("{}".format(layerName))[0]
    per = 0
    self.dlg.progressBar_mf_results.setValue(0)
    for m in selected_months:
        m_vals = mbig_df.loc[m, :]
        QCoreApplication.processEvents()
        mon_nam = calendar.month_abbr[m]

        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName(mon_nam) == -1:
            field = QgsField(mon_nam, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        mf_hds_idx = provider.fields().indexFromName(mon_nam)
        
        tot_feats = self.layer.featureCount()
        count = 0        
        # Get features (Find out a way to change attribute values using another field)
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, mf_hd in zip(feats, m_vals):
            self.layer.changeAttributeValue(f.id(), mf_hds_idx, mf_hd)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rt.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()

        # Update progress bar 
        per += 1
        progress = round((per / len(selected_months)) *100)
        self.dlg.progressBar_rt_results.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("{} results were exported successfully!".format(layerName))
    msgBox.exec_()

