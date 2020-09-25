from builtins import str
import os
import os.path
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtCore import QVariant, QCoreApplication
import processing
from processing.tools import dataobjects
from qgis.core import (
                    QgsVectorLayer, QgsField, QgsProject, QgsFeatureIterator,
                    QgsFeatureRequest, QgsLayerTreeLayer, QgsExpression, QgsFeature,
                    QgsProcessingFeedback)
import glob
import subprocess
import shutil
from datetime import datetime
import csv


# deleting existing river_grid
def deleting_river_grid(self):
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("river_grid (APEX-MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

# Used for both SWAT and SWAT+
def river_grid(self): #step 1
    APEXMOD_path_dict = self.dirs_and_paths()

    # Initiate rive_grid shapefile
    # if there is an existing river_grid shapefile, it will be removed
    for self.lyr in list(QgsProject.instance().mapLayers().values()):
        if self.lyr.name() == ("river_grid (APEX-MODFLOW)"):
            QgsProject.instance().removeMapLayers([self.lyr.id()])
    if self.dlg.radioButton_mf_riv1.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (APEX)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv1 (MODFLOW)")[0]
    elif self.dlg.radioButton_mf_riv2.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (APEX)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
    elif self.dlg.radioButton_mf_riv3.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (APEX)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv3 (MODFLOW)")[0]
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setMaximumSize(1000, 200) # resize not working
        msgBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) # resize not working
        msgBox.setWindowTitle("Hello?")
        msgBox.setText("Please, select one of the river options!")
        msgBox.exec_()

    name = "river_grid"
    name_ext = "river_grid.shp"
    output_dir = APEXMOD_path_dict['apexmf_shps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    # runinng the actual routine:
    params = { 
        'INPUT' : input1,
        'OVERLAY' : input2, 
        'OUTPUT' : output_file,
        'OVERWRITE': True
    }
    processing.run('qgis:intersection', params)
    
    # defining the outputfile to be loaded into the canvas        
    river_grid_shapefile = os.path.join(output_dir, name_ext)
    self.layer = QgsVectorLayer(river_grid_shapefile, '{0} ({1})'.format("river_grid","APEX-MODFLOW"), 'ogr')    
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("APEX-MODFLOW")   
    QgsProject.instance().addMapLayer(self.layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(self.layer))

# 
def river_grid_delete_NULL(self):
    layer = QgsProject.instance().mapLayersByName("river_grid (APEX-MODFLOW)")[0]
    provider = layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression("grid_id IS NULL" )
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    request2 = QgsFeatureRequest().setFilterExpression("subbasin IS NULL" )
    request2.setSubsetOfAttributes([])
    request2.setFlags(QgsFeatureRequest.NoGeometry)

    layer.startEditing()
    for f in layer.getFeatures(request):
        layer.deleteFeature(f.id())
    for f in layer.getFeatures(request2):
        layer.deleteFeature(f.id())
    layer.commitChanges()


# SWAT+
# Create a field for filtering rows on area
def create_river_grid_filter(self):
    self.layer = QgsProject.instance().mapLayersByName("river_grid (APEX-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    field = QgsField("ol_length", QVariant.Int)
    #field = QgsField("ol_area", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()

    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['ol_length'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


def delete_river_grid_with_threshold(self):
    self.layer = QgsProject.instance().mapLayersByName("river_grid (APEX-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression('"rgrid_len" < 0.5')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
    self.layer.commitChanges()


def rgrid_len(self):

    self.layer = QgsProject.instance().mapLayersByName("river_grid (APEX-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    field = QgsField("rgrid_len", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()
    
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['rgrid_len'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


def calculate_sub_area(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'SUB areas' ... processing")
    self.dlg.label_StepStatus.setText("Calculating 'SUB areas' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("sub_area") == -1:
        # field = QgsField("hru_area", QVariant.Int)
        field = QgsField("sub_area", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            feat['sub_area'] = round(area)
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'sub_area' already exists ...")        
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'SUB areas' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def sub_grid(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Intersecting SUBs by GRIDs ... processing")
    self.dlg.label_StepStatus.setText("Intersecting SUBs by GRIDs ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    APEXMOD_path_dict = self.dirs_and_paths()
    input1 = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
    input2 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    name = "sub_grid"
    name_ext = "sub_grid.shp"
    output_dir = APEXMOD_path_dict['apexmf_shps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    params = {
        'INPUT': input1,
        'OVERLAY': input2,
        'OUTPUT': output_file
    }
    processing.run("native:intersection", params)
    # defining the outputfile to be loaded into the canvas        
    sub_grid_shapefile = os.path.join(output_dir, name_ext)
    layer = QgsVectorLayer(sub_grid_shapefile, '{0} ({1})'.format("sub_grid","APEX-MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("APEX-MODFLOW")   
    QgsProject.instance().addMapLayer(layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Intersecting SUBs by GRIDs ... passed")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()


# Create a field for filtering rows on area
def create_sub_grid_filter(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating overlapping sizes ... processing")
    # self.dlg.textEdit_sm_link_log.append('              ⮡     *** BE PATIENT!!! This step takes the most time! ***    ')

    self.dlg.label_StepStatus.setText("Calculating overlapping sizes ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("sub_grid (APEX-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("ol_area") == -1:
        field = QgsField("ol_area", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        # 
        tot_feats = self.layer.featureCount()
        count = 0

        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            #score = scores[i]
            feat['ol_area'] = round(area)
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        self.dlg.progressBar_step.setValue(100)
        QCoreApplication.processEvents()
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating overlapping sizes... processing")
        self.dlg.textEdit_sm_link_log.append('              ⮡     *** HOORAY!!! Almost there! ***    ')      
        self.dlg.label_StepStatus.setText('Step Status: ')
        QCoreApplication.processEvents()


def delete_sub_grid_with_zero(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Deleting small objects ... processing")
    self.dlg.label_StepStatus.setText("Deleting small objects ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("sub_grid (APEX-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if self.dlg.groupBox_threshold.isChecked():
        threshold = self.dlg.horizontalSlider_ol_area.value()
        request = QgsFeatureRequest().setFilterExpression('"ol_area" < {}'.format(threshold))
    else:
        request = QgsFeatureRequest().setFilterExpression('"ol_area" < 900')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    tot_feats = self.layer.featureCount()
    count = 0
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
        count += 1
        provalue = round(count/tot_feats*100)
        self.dlg.progressBar_step.setValue(provalue)
        QCoreApplication.processEvents()
    self.layer.commitChanges()
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Deleting small objects ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()





""" 
/********************************************************************************************
 *                                                                                          *
 *                              Export GIS Table for original SWAT                          *
 *                                                                                          *
 *******************************************************************************************/
"""




def export_rgrid_len(self):
    APEXMOD_path_dict = self.dirs_and_paths()  
    ### sort by sub_id and then by grid and save down ### 
    #read in the sub shapefile
    layer = QgsProject.instance().mapLayersByName("river_grid (APEX-MODFLOW)")[0]

    # Get the index numbers of the fields
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    subbasin_index = layer.dataProvider().fields().indexFromName("Subbasin")
    ol_length_index = layer.dataProvider().fields().indexFromName("ol_length")
    
    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_index))
    
    info_number = len(l_sorted) # number of lines
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "link_river_grid"
    output_dir = APEXMOD_path_dict['Table']   
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the sub number to the file
        second_row = ["grid_id subbasin rgrid_len"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        for item in l_sorted:
            # Write item to outcsv. the order represents the output order
            writer.writerow([item[grid_id_index], item[subbasin_index], item[ol_length_index]])


def export_sub_grid(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    #read in the sub shapefile
    layer = QgsProject.instance().mapLayersByName("sub_grid (APEX-MODFLOW)")[0]
    # Get the index numbers of the fields
    sub_id_index = layer.dataProvider().fields().indexFromName("Subbasin")
    sub_area_index = layer.dataProvider().fields().indexFromName("sub_area")
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    overlap_area_index = layer.dataProvider().fields().indexFromName("ol_area")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_index, sub_id_index))
    #l.sort(key=itemgetter(6))
    #add a counter as index for the sub id
    for filename in glob.glob(str(APEXMOD_path_dict['MODFLOW'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).
    cell_size = delr * delc
    number_of_grids = nrow * ncol
    for i in l_sorted:     
        i.append(str(int(cell_size))) # area of the grid

    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "link_sa_grid"
    output_dir = APEXMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the sub number to the file
        second_row = [str(number_of_grids)] # prints the total number of grid cells
        third_row = ["grid_id grid_area sub_id overlap_area sub_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([
                item[grid_id_index], item[overlap_area_index + 1],
                item[sub_id_index], item[overlap_area_index], item[sub_area_index]])


def export_grid_sub(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    #read in the sub shapefile
    layer = QgsProject.instance().mapLayersByName("sub_grid (APEX-MODFLOW)")[0]

    # Get max number of sub id
    sub_max = [f.attribute("Subbasin") for f in layer.getFeatures()]

    # Get the index numbers of the fields
    sub_id_index = layer.dataProvider().fields().indexFromName("Subbasin")
    sub_area_index = layer.dataProvider().fields().indexFromName("sub_area")
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    overlap_area_index = layer.dataProvider().fields().indexFromName("ol_area")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(sub_id_index, grid_id_index))

    #l.sort(key=itemgetter(6))
    #add a counter as index for the sub id
    for filename in glob.glob(str(APEXMOD_path_dict['MODFLOW'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:
        i.append(str(int(cell_size))) # area of the grid
        


    # It seems we need just total number of DHRUs not the one used in study area
    # sub_number = len(sub_id_unique) # number of subs
    sub_number = max(sub_max) # number of subs
    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "link_grid_sa"
    output_dir = APEXMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dnumber of lines with information
        second_row = [str(sub_number)] # prints the total number of sub
        third_row = [str(nrow)] # prints the row number to the file
        fourth_row = [str(ncol)] # prints the column number to the file     
        fifth_row = ["grid_id grid_area sub_id overlap_area sub_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        writer.writerow(fourth_row)
        writer.writerow(fifth_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[grid_id_index], item[overlap_area_index + 1],
                item[sub_id_index], item[overlap_area_index], item[sub_area_index]])


# NOTE: Not used for APEX-MODFLOW
# def run_CreateSWATMF(self):
#     APEXMOD_path_dict = self.dirs_and_paths()
#     output_dir = APEXMOD_path_dict['Table']
#     #Out_folder_temp = self.dlg.lineEdit_output_folder.text()
#     #apexmf = os.path.normpath(output_dir + "/" + "SWATMF_files")
#     name = "CreateSWATMF.exe"
#     exe_file = os.path.normpath(os.path.join(output_dir, name))
#     #os.startfile(File_Physical)    
#     p = subprocess.Popen(exe_file , cwd = output_dir) # cwd -> current working directory    
#     p.wait()


def copylinkagefiles(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    source_dir = APEXMOD_path_dict['Table']
    dest_dir = APEXMOD_path_dict['MODFLOW']
    files = os.listdir(source_dir)
    for f in files:
        fullname_file = os.path.join(source_dir, f)
        shutil.copy(fullname_file, dest_dir)

