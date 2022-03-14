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
import numpy as np
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

def comps_dic():
    comps_dic = {
        'NO3': 'Nitrate',
        'P': 'Phosphorus',
        'SO4': 'Sulfate',
        'Ca2': 'Calcium',
        'Mg2': 'Magnesium',
        'Na': 'Sodium',
        'K': 'Potassium',
        'Cl': 'Chloride',
        'CO3': 'Carbonate',
        'HCO3': 'Bicarbonate'}
    
    # available comps list
    comps =  [i.lower() for i in comps_dic.values()]
    new_comps = []
    for i in comps:
        if i == 'nitrate' or i == 'phosphorus':
            i = 'rt3d_' + i
        else:
            i = 'salt_' + i
        new_comps.append(i)
    suffixs = ['_mon', '_yr', '_avg_mon']

    new_comps2 = []
    for comp in new_comps:
        for suf in suffixs:
            new_comps2.append(comp + suf)
    return comps_dic, new_comps2

def get_compNames(self):
    comps, new_comps2 = comps_dic()
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['MODFLOW']
    # find number of species
    for filename in glob.glob(wd + "/*.btn"):            
        with open(os.path.join(wd, filename), "r") as f:
            lines = f.readlines()
    for num, line in enumerate(lines, 1):
        if line.startswith("'NCOMP,"):
            lNumComp = num
        if line.startswith("'SPECIES"):
            lNumSpecies = num
    data = [i.replace('\n', '').split() for i in lines]
    nComp = data[lNumComp][0]
    compNams = []
    for i in range(lNumSpecies, lNumSpecies+ int(nComp)):
        compNams.append(data[i][0].replace("'", ""))
    fullnams = []
    for i in compNams:
        for j in comps.keys():
            if i == j:
                val = comps.get(j)
                fullnams.append('{} ({})'.format(j, val))
    fullnams = ["Select Solute"] + fullnams
    self.dlg.comboBox_solutes.clear()
    self.dlg.comboBox_solutes.addItems(fullnams)


def read_mf_nOflayers(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read the number of layers
    for filename in glob.glob(str(APEXMOD_path_dict['MODFLOW'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nlayer = int(data[0][0])
    lyList = [str(i+1) for i in range(nlayer)]
    self.dlg.comboBox_rt_layer.clear()
    self.dlg.comboBox_rt_layer.addItems(lyList)

def read_rt3d_dates(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    filename = "amf_RT3D_cNO3_monthly.out"
    # Open "swatmf_out_MF_head" file
    y = ("Monthly") # Remove unnecssary lines
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
    date = [x.strip().split() for x in data if x.strip().startswith("month:")]  # Collect only lines with dates
    onlyDate = [x[1] for x in date] # Only date
    # data1 = [x.split() for x in data] # make each line a list
    dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
    self.dlg.comboBox_rt_results_sdate.clear()
    self.dlg.comboBox_rt_results_sdate.addItems(dateList)
    self.dlg.comboBox_rt_results_edate.clear()
    self.dlg.comboBox_rt_results_edate.addItems(dateList)
    self.dlg.comboBox_rt_results_edate.setCurrentIndex(len(dateList)-1)

def create_rt3d_shps(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Create apexmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("apexmf_results"):
        apexmf_results = root.findGroup("apexmf_results")
    else:
        apexmf_results = root.insertGroup(0, "apexmf_results")
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = input1.dataProvider()
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    name = "rt3d_{}_mon".format(comp)
    name_ext = name + ".shp"
    output_dir = APEXMOD_path_dict['apexmf_shps']
    # Check if there is an exsting mf_head shapefile
    if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
        mf_hd_shapfile = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, mf_hd_shapfile,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(mf_hd_shapfile, '{0}'.format(name), 'ogr')
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

# NOTE: percolation in sub
def create_rt3d_perc_shps(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Create apexmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("apexmf_results"):
        apexmf_results = root.findGroup("apexmf_results")
    else:
        apexmf_results = root.insertGroup(0, "apexmf_results")
    input1 = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
    provider = input1.dataProvider()
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    if self.dlg.radioButton_rt3d_d.isChecked():
        name = "rt3d_{}_perc_day".format(comp)
    elif self.dlg.radioButton_rt3d_m.isChecked():
        name = "rt3d_{}_perc_mon".format(comp)
    elif self.dlg.radioButton_rt3d_y.isChecked():
        name = "rt3d_{}_perc_year".format(comp)
    name_ext = name + ".shp"
    output_dir = APEXMOD_path_dict['apexmf_shps']
    # Check if there is an exsting mf_head shapefile
    if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
        mf_hd_shapfile = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, mf_hd_shapfile,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(mf_hd_shapfile, '{0}'.format(name), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        apexmf_results = root.findGroup("apexmf_results")
        QgsProject.instance().addMapLayer(layer, False)
        apexmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

        input2 = QgsProject.instance().mapLayersByName(name)[0]
        fields = input2.dataProvider()
        fdname = [
                    fields.fields().indexFromName(field.name()) for field in fields.fields()
                    if not field.name() == 'Subbasin']
        fields.deleteAttributes(fdname)
        input2.updateFields()
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("'{}' layer has been created in 'apexmf_results' group!".format(name))
        msgBox.exec_()

def read_perc_dates(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    self.layer = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
    tot_feats = self.layer.featureCount()
    wd = APEXMOD_path_dict['MODFLOW']
    infile = "amf_apex_percno3.out"
    y = ("APEX", "Subarea,", "NO3")
    with open(os.path.join(wd, infile), "r") as f:
        data1 = [x.split()[2].strip() for x in f if x.strip() and not x.strip().startswith(y)]
    date_length = int(len(data1)/75)
    temp_df = pd.DataFrame({'temp': [i*0 for i in range(0, date_length)]})
    temp_df.index = pd.date_range(stdate, periods=date_length)
    dateList = temp_df.index.strftime("%m-%d-%Y").tolist()
    if self.dlg.radioButton_rt3d_m.isChecked(): 
        temp_df = temp_df.resample('M').mean()
        dateList = temp_df.index.strftime("%m-%d-%Y").tolist()
    elif self.dlg.radioButton_rt3d_y.isChecked(): 
        temp_df = temp_df.resample('A').mean()
        dateList = temp_df.index.strftime("%m-%d-%Y").tolist()
    
    self.dlg.comboBox_rt_results_sdate.clear()
    self.dlg.comboBox_rt_results_sdate.addItems(dateList)
    self.dlg.comboBox_rt_results_edate.clear()
    self.dlg.comboBox_rt_results_edate.addItems(dateList)
    self.dlg.comboBox_rt_results_edate.setCurrentIndex(len(dateList)-1)





def get_percno3_df(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    self.layer = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
    tot_feats = self.layer.featureCount()
    wd = APEXMOD_path_dict['MODFLOW']
    infile = "amf_apex_percno3.out"
    y = ("APEX", "Subarea,", "NO3")
    with open(os.path.join(wd, infile), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]
    data1 = [x.split()[2] for x in data]
    data_array = np.reshape(data1, (tot_feats, int(len(data1)/tot_feats)), order='F')
    column_names = ["{:03d}".format(int(x.split()[0])) for x in data[0:tot_feats]]
    df_ = pd.DataFrame(data_array.T, columns=column_names)
    df_.sort_index(axis=1, inplace=True)
    df_.index = pd.date_range(stdate, periods=len(df_))
    df_ = df_.astype(float)
    # dateList = df_.index.strftime("%m-%d-%Y").tolist()
    if self.dlg.radioButton_rt3d_m.isChecked(): 
        df_ = df_.resample('M').mean()
        # dateList = df_.index.strftime("%b-%Y").tolist()
    elif self.dlg.radioButton_rt3d_y.isChecked(): 
        df_ = df_.resample('A').mean()
        # dateList = df_.index.strftime("%Y").tolist()

    return df_


def export_perc_no3(self):
    df = get_percno3_df(self)

    
    selectedSdate = self.dlg.comboBox_rt_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_rt_results_edate.currentText()

    df = df[selectedSdate:selectedEdate]

    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    if self.dlg.radioButton_rt3d_d.isChecked():
        name = "rt3d_{}_perc_day".format(comp)
    elif self.dlg.radioButton_rt3d_m.isChecked():
        name = "rt3d_{}_perc_mon".format(comp)
    elif self.dlg.radioButton_rt3d_y.isChecked():
        name = "rt3d_{}_perc_year".format(comp)
    input1 = QgsProject.instance().mapLayersByName(name)[0]


    per = 0
    self.dlg.progressBar_mf_results.setValue(0)
    for selectedDate in df.index.tolist():
        QCoreApplication.processEvents()
        selectedDate = selectedDate.strftime("%m-%d-%Y")

        provider = input1.dataProvider()
        if provider.fields().indexFromName(selectedDate) == -1:
            field = QgsField(selectedDate, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            input1.updateFields()
        mf_hds_idx = provider.fields().indexFromName(selectedDate)
        
        tot_feats = input1.featureCount()
        count = 0        
        # Get features (Find out a way to change attribute values using another field)
        feats = input1.getFeatures()
        input1.startEditing()
        # add row number
        perc_list =  df.loc[selectedDate].tolist()
        for f, mf_hd in zip(feats, perc_list):
            input1.changeAttributeValue(f.id(), mf_hds_idx, mf_hd)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rt.setValue(provalue)
            QCoreApplication.processEvents()
        input1.commitChanges()
        QCoreApplication.processEvents()

        # Update progress bar 
        per += 1
        progress = round((per / len(df.index.tolist())) *100)
        self.dlg.progressBar_rt_results.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("rt_nitrate_perc results were exported successfully!")
    msgBox.exec_()






def read_mf_nitrate_dates(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Create apexmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("apexmf_results"):
        apexmf_results = root.findGroup("apexmf_results")
    else:
        apexmf_results = root.insertGroup(0, "apexmf_results")
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = input1.dataProvider()
    comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    '''
    if self.dlg.checkBox_head.isChecked() and self.dlg.radioButton_mf_results_d.isChecked():
        filename = "swatmf_out_MF_head"
        # Open "swatmf_out_MF_head" file
        y = ("MODFLOW", "--Calculated", "daily") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        # data1 = [x.split() for x in data] # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y")  # Change startDate format
        dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_sdate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.clear()
        self.dlg.comboBox_mf_results_edate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.setCurrentIndex(len(dateList)-1)
        # Copy mf_grid shapefile to apexmf_results tree
        name = "mf_rch_daily"
        name_ext = "mf_rch_daily.shp"
        output_dir = APEXMOD_path_dict['apexmf_shps']
        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == ("mf_rch_daily") for lyr in QgsProject.instance().mapLayers().values()):
            mf_rch_shapfile = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(input1, mf_rch_shapfile,
                "utf-8", input1.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(mf_rch_shapfile, '{0}'.format("mf_rch_daily"), 'ogr')
            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            apexmf_results = root.findGroup("apexmf_results")   
            QgsProject.instance().addMapLayer(layer, False)
            apexmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Created!")
            msgBox.setText("'mf_rch_daily.shp' file has been created in 'apexmf_results' group!")
            msgBox.exec_()
    '''
    # if comp != "Select" and self.dlg.radioButton_rt3d_m.isChecked():
    if comp == "nitrate" and self.dlg.radioButton_rt3d_m.isChecked():
        filename = "amf_RT3D_cNO3_monthly.out"
        # Open "swatmf_out_MF_head" file
        y = ("Monthly") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("month:")]  # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        # data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
        self.dlg.comboBox_rt_results_sdate.clear()
        self.dlg.comboBox_rt_results_sdate.addItems(dateList)
        self.dlg.comboBox_rt_results_edate.clear()
        self.dlg.comboBox_rt_results_edate.addItems(dateList)
        self.dlg.comboBox_rt_results_edate.setCurrentIndex(len(dateList)-1)
        # Copy mf_grid shapefile to apexmf_results tree
        name = "rt3d_{}_mon".format(comp)
        name_ext = name + ".shp"
        output_dir = APEXMOD_path_dict['apexmf_shps']
        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
            mf_hd_shapfile = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(
                input1, mf_hd_shapfile,
                "utf-8", input1.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(mf_hd_shapfile, '{0}'.format(name), 'ogr')
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

    elif self.dlg.radioButton_rt3d_y.isChecked():
        filename = "swatmf_out_RT_cno3_yearly"
        # Open "swatmf_out_MF_head" file
        y = ("Yearly") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        # data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='A').strftime("%Y").tolist()
        self.dlg.comboBox_rt_results_sdate.clear()
        self.dlg.comboBox_rt_results_sdate.addItems(dateList)
        self.dlg.comboBox_rt_results_edate.clear()
        self.dlg.comboBox_rt_results_edate.addItems(dateList)
        self.dlg.comboBox_rt_results_edate.setCurrentIndex(len(dateList)-1)
        # Copy mf_grid shapefile to apexmf_results tree
        name = "mf_nitrate_yearly"
        name_ext = "mf_nitrate_yearly.shp"
        output_dir = APEXMOD_path_dict['apexmf_shps']
        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
            mf_hd_shapfile = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(
                input1, mf_hd_shapfile,
                "utf-8", input1.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(mf_hd_shapfile, '{0}'.format(name), 'ogr')
            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            apexmf_results = root.findGroup("apexmf_results")   
            QgsProject.instance().addMapLayer(layer, False)
            apexmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Created!")
            msgBox.setText("'mf_nitrate_yearly.shp' file has been created in 'apexmf_results' group!")
            msgBox.exec_()
    else:
        self.dlg.comboBox_rt_results_sdate.clear()
        self.dlg.comboBox_rt_results_edate.clear()

        
def export_rt_cno3(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    # if self.dlg.radioButton_mf_results_d.isChecked():
    #     filename = "swatmf_out_MF_head"
    #     self.layer = QgsProject.instance().mapLayersByName("mf_rch_daily")[0]
    #     with open(os.path.join(wd, filename), "r") as f:
    #         data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
    #     date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
    #     onlyDate = [x[1] for x in date] # Only date
    #     data1 = [x.split() for x in data] # make each line a list
    #     sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
    #     dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
    if self.dlg.radioButton_rt3d_m.isChecked() and not self.dlg.mGroupBox_rt_avg.isChecked():
        comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1]
        layerName = "rt3d_{}_mon".format(comp.lower())
        filename = "amf_RT3D_cNO3_monthly.out"
        self.layer = QgsProject.instance().mapLayersByName(layerName)[0]
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
        date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq='M').strftime("%b-%Y").tolist()
    elif self.dlg.radioButton_mf_results_y.isChecked():
        filename = "swatmf_out_MF_head_yearly"
        self.layer = QgsProject.instance().mapLayersByName("rt_nitrate_yearly")[0]
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'A').strftime("%Y").tolist()
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()
    
    selectedSdate = self.dlg.comboBox_rt_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_rt_results_edate.currentText()
    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features

    per = 0
    self.dlg.progressBar_mf_results.setValue(0)
    for selectedDate in dateList_f:
        QCoreApplication.processEvents()
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        # if self.dlg.radioButton_mf_results_d.isChecked():
        #     for num, line in enumerate(data1, 1):
        #         if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
        #             ii = num # Starting line
        if self.dlg.radioButton_rt3d_m.isChecked():
            # Find year 
            dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
            year = dt.year
            layerN = self.dlg.comboBox_rt_layer.currentText()
            for num, line in enumerate(data1, 1):
                if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                    ii = num # Starting line
            count = 0
            # while ((data1[count+ii][0] != 'layer:') and (data1[count+ii][1] != layer)):  # why not working?
            while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
                count += 1
            stline = count+ii+1
        elif self.dlg.radioButton_mf_results_y.isChecked():
            layerN = self.dlg.comboBox_rt_layer.currentText()
            for num, line in enumerate(data1, 1):
                if line[0] == "year:" in line and line[1] == onlyDate_lookup in line:
                    ii = num # Starting line
            count = 0
            while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
                count += 1
            stline = count+ii+1

        mf_hds = []
        hdcount = 0
        while hdcount < input1.featureCount():
            for kk in range(len(data1[stline])):
                mf_hds.append(float(data1[stline][kk]))
                hdcount += 1
            stline += 1

        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName(selectedDate) == -1:
            field = QgsField(selectedDate, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        mf_hds_idx = provider.fields().indexFromName(selectedDate)
        
        tot_feats = self.layer.featureCount()
        count = 0        
        # Get features (Find out a way to change attribute values using another field)
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, mf_hd in zip(feats, mf_hds):
            self.layer.changeAttributeValue(f.id(), mf_hds_idx, mf_hd)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rt.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
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
    msgBox.setText("rt_nitrate results were exported successfully!")
    msgBox.exec_()


def get_rt_cno3_avg_m_df(self):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Reading ...")
    msgBox.setText("We are going to read the 'amf_RT3D_cNO3_monthly.out' file ...")
    msgBox.exec_()

    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    filename = "amf_RT3D_cNO3_monthly.out"
    # self.layer = QgsProject.instance().mapLayersByName("rt3d_nitrate_avg_mon")[0]
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
    date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
    onlyDate = [x[1] for x in date] # Only date
    data1 = [x.split() for x in data] # make each line a list
    dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()

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
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
        count = 0
        # while ((data1[count+ii][0] != 'layer:') and (data1[count+ii][1] != layer)):  # why not working?
        while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
            count += 1
        stline = count+ii+1
        mf_hds = []
        hdcount = 0
        while hdcount < input1.featureCount():
            for kk in range(len(data1[stline])):
                mf_hds.append(float(data1[stline][kk]))
                hdcount += 1
            stline += 1
        s = pd.Series(mf_hds, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%Y-%m-%d"))
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

def create_rt_avg_mon_shp(self):
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    APEXMOD_path_dict = self.dirs_and_paths()

    # Copy mf_grid shapefile to apexmf_results tree
    name = "rt3d_nitrate_avg_mon"
    name_ext = "rt3d_nitrate_avg_mon.shp"
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
        msgBox.setText("'rt3d_nitrate_avg_mon.shp' file has been created in 'apexmf_results' group!")
        msgBox.exec_()
        msgBox = QMessageBox()

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


def export_rt_cno3_avg_m(self):
    # comp = self.dlg.comboBox_solutes.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    mbig_df = self.mbig_df
    selected_months = selected_rt_mon(self)
    self.layer = QgsProject.instance().mapLayersByName("rt3d_nitrate_avg_mon")[0]
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
    msgBox.setText("rt_nitrate_m results were exported successfully!")
    msgBox.exec_()

def read_vector_maps(self):
    comp_dic, comps = comps_dic()
    layers = [lyr.name() for lyr in list(QgsProject.instance().mapLayers().values())]
    perc_layers = [
        "rt3d_nitrate_perc_day",
        "rt3d_nitrate_perc_mon",
        "rt3d_nitrate_perc_year",
        "rt3d_phosphorus_perc_day",
        "rt3d_phosphorus_perc_mon",
        "rt3d_phosphorus_perc_year",
    ]
    available_layers = [
                'mf_head_mon',
                'mf_head_yr',
                'mf_recharge_mon',
                'mf_recharge_yr',
                ]
    available_layers = available_layers + perc_layers+ comps 

    self.dlg.comboBox_vector_lyrs.clear()
    self.dlg.comboBox_vector_lyrs.addItems(available_layers)
    for i in range(len(available_layers)):
        self.dlg.comboBox_vector_lyrs.model().item(i).setEnabled(False)
    for i in available_layers:
        for j in layers:
            if i == j:
                idx = available_layers.index(i)
                self.dlg.comboBox_vector_lyrs.model().item(idx).setEnabled(True)
    self.dlg.mColorButton_min_rmap.defaultColor()
    self.dlg.mColorButton_max_rmap.defaultColor()


def cvt_vtr(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    selectedVector = self.dlg.comboBox_vector_lyrs.currentText()
    layer = QgsProject.instance().mapLayersByName(str(selectedVector))[0]

    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    for filename in glob.glob(str(APEXMOD_path_dict['MODFLOW'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (y spacing)
        delc = float(data[3][1]) # is the cell width along columns (x spacing).

    # get extent
    ext = layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)

    fdnames = [
                field.name() for field in layer.dataProvider().fields() if not (
                field.name() == 'fid' or
                field.name() == 'id' or
                field.name() == 'xmin' or
                field.name() == 'xmax' or
                field.name() == 'ymin' or
                field.name() == 'ymax' or
                field.name() == 'grid_id' or
                field.name() == 'row' or
                field.name() == 'col' or
                field.name() == 'elev_mf'
                )
                    ]

    # Create apexmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("apexmf_results"):
        apexmf_results = root.findGroup("apexmf_results")
    else:
        apexmf_results = root.insertGroup(0, "apexmf_results")
    
    if root.findGroup(selectedVector):
        rastergroup = root.findGroup(selectedVector)
    else:
        rastergroup = apexmf_results.insertGroup(0, selectedVector)
    per = 0
    self.dlg.progressBar_cvt_vtr.setValue(0)
    for fdnam in fdnames:
        QCoreApplication.processEvents()
        nodata = float(self.dlg.lineEdit_nodata.text())
        mincolor = self.dlg.mColorButton_min_rmap.color().name()
        maxcolor = self.dlg.mColorButton_max_rmap.color().name()
        name = fdnam
        name_ext = "{}.tif".format(name)
        output_dir = APEXMOD_path_dict['apexmf_shps']
        # create folder for each layer output
        rasterpath = os.path.join(output_dir, selectedVector)
        if not os.path.exists(rasterpath):
            os.makedirs(rasterpath)
        output_raster = os.path.join(rasterpath, name_ext)
        params = {
            'INPUT': layer,
            'FIELD': fdnam,
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': nodata,
            'DATA_TYPE': 5, #Float32
            'OUTPUT': output_raster
        }
        processing.run("gdal:rasterize", params)
        rasterlayer = QgsRasterLayer(output_raster, '{0} ({1})'.format(fdnam, selectedVector))
        QgsProject.instance().addMapLayer(rasterlayer, False)
        rastergroup.insertChildNode(0, QgsLayerTreeLayer(rasterlayer))
        stats = rasterlayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, ext, 0)
        rmin = stats.minimumValue
        rmax = stats.maximumValue
        fnc = QgsColorRampShader()
        lst = [QgsColorRampShader.ColorRampItem(rmin, QColor(mincolor)), QgsColorRampShader.ColorRampItem(rmax, QColor(maxcolor))]
        fnc.setColorRampItemList(lst)
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        fnc.setClassificationMode(QgsColorRampShader.Quantile)
        fnc.classifyColorRamp()

        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(rasterlayer.dataProvider(), 1, shader)
        rasterlayer.setRenderer(renderer)
        rasterlayer.triggerRepaint()
        # create image
        img = QImage(QSize(800, 800), QImage.Format_ARGB32_Premultiplied)
        # set background color
        # bcolor = QColor(255, 255, 255, 255)
        bcolor = QColor(255, 255, 255, 0)
        img.fill(bcolor.rgba())
        # create painter
        p = QPainter()
        p.begin(img)
        p.setRenderHint(QPainter.Antialiasing)

        # create map settings
        ms = QgsMapSettings()
        ms.setBackgroundColor(bcolor)

        # set layers to render
        flayer = QgsProject.instance().mapLayersByName(rasterlayer.name())
        ms.setLayers([flayer[0]])

        # set extent
        rect = QgsRectangle(ms.fullExtent())
        rect.scale(1.1)
        ms.setExtent(rect)

        # set ouptut size
        ms.setOutputSize(img.size())

        # setup qgis map renderer
        render = QgsMapRendererCustomPainterJob(ms, p)
        render.start()
        render.waitForFinished()
        
        # get timestamp
        p.drawImage(QPoint(), img)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        p.setPen(pen)

        font = QFont()
        font.setFamily('Times')
        # font.setBold(True)
        font.setPointSize(18)
        p.setFont(font)
        # p.setBackground(QColor('sea green')) doesn't work    
        p.drawText(QRect(0, 0, 800, 800), Qt.AlignRight | Qt.AlignBottom, fdnam)
        p.end()

        # save the image
        img.save(os.path.join(rasterpath, '{:03d}_{}.jpg'.format(per, fdnam)))
        
        # Update progress bar         
        per += 1
        progress = round((per / len(fdnames)) *100)
        self.dlg.progressBar_cvt_vtr.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    duration = self.dlg.doubleSpinBox_ani_r_time.value()

    # filepaths
    fp_in = os.path.join(rasterpath, '*.jpg')
    fp_out = os.path.join(rasterpath, '{}.gif'.format(selectedVector))

    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
    fimg, *fimgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    fimg.save(fp=fp_out, format='GIF', append_images=fimgs,
            save_all=True, duration=duration*1000, loop=0, transparency=0)
    
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Coverted!")
    msgBox.setText("Fields from {} were converted successfully!".format(selectedVector))
    msgBox.exec_()

    questionBox = QMessageBox()
    questionBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    reply = QMessageBox.question(
                    questionBox, 'Open?', 
                    'Do you want to open the animated gif file?', QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        os.startfile(os.path.join(rasterpath, '{}.gif'.format(selectedVector)))
