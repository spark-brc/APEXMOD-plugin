from builtins import zip
from builtins import str
from builtins import range
import os
import os.path
import processing
from qgis.core import (
                QgsVectorLayer, QgsField, QgsFeatureIterator, QgsVectorFileWriter,
                QgsProject, QgsLayerTreeLayer, QgsFeatureRequest)
from qgis.PyQt import QtCore, QtGui, QtSql
import glob
import posixpath
import ntpath
import shutil
import distutils.dir_util
from datetime import datetime
from qgis.PyQt.QtCore import QVariant, QSettings, QFileInfo, QCoreApplication
from PyQt5.QtWidgets import (
    QAction, QDialog, QFormLayout,
    QMessageBox, QFileDialog
)

def select_apex_model(self):
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Select APEX model folder (TxtInOut)!"
    options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
    directory = QFileDialog.getExistingDirectory(None,
        title, path, options)
    if directory:
        proj = QgsProject.instance()
        Project_Name = QFileInfo(proj.fileName()).baseName()
        Out_folder_temp = QgsProject.instance().readPath("./")
        Out_folder = os.path.normpath(Out_folder_temp + "/" + Project_Name + "/" + "APEX-MODFLOW")
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Copying orginal APEX inputs ... processing")
        self.dlg.progressBar_step.setValue(0)
        QCoreApplication.processEvents()

        count = 0
        filelist =  os.listdir(directory)
        for i in filelist:
            shutil.copy2(os.path.join(directory, i), Out_folder)
            count += 1
            provalue = round(count/len(filelist)*100)
            self.dlg.label_StepStatus.setText(i)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        file_check = os.path.abspath(os.path.join(Out_folder, "APEXCONT.DAT"))
        if os.path.isfile(file_check) is True: 
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Copied!")
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setText("The APEX model has been successfully copied")
            msgBox.exec_()
            self.define_sim_period()
            self.dlg.lineEdit_TxtInOut.setText(Out_folder)

            time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Copying orginal APEX inputs ... passed")
            self.dlg.label_StepStatus.setText('Step Status: ')
            self.dlg.progressBar_step.setValue(0)
            QCoreApplication.processEvents()
        else:
            msgBox = QMessageBox()
            msgBox.setText("There was a problem copying the APEX model")
            msgBox.exec_()


def sub_shapefile(self):
    APEXMOD_path_dict = self.dirs_and_paths() 
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Choose SUB Shapefile!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Shapefiles (*.shp);;All files (*.*)"
        )
    if inFileName:
        settings.setValue('/APEXMOD/LastInputPath', os.path.dirname(str(inFileName)))           
        output_dir = APEXMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'
        
        inName = 'sub_org'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(output_dir, inName + suffix)
            else:
                outfile = posixpath.join(output_dir, inName + suffix)                    
            shutil.copy(f, outfile)
        if os.name == 'nt':
            sub_obj = ntpath.join(output_dir, inName + ".shp")
        else:
            sub_obj = posixpath.join(output_dir, inName + ".shp")
        # time stamp
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Checking SUB geometries ... processing")
        self.dlg.label_StepStatus.setText("Checking 'SUB' ... ")
        QCoreApplication.processEvents()
        # fixgeometries
        sub_shp_file = 'sub_apex.shp'
        sub_shp_f = os.path.join(output_dir, sub_shp_file)
        params = {
            'INPUT': sub_obj,
            'OUTPUT': sub_shp_f
        }
        processing.run('native:fixgeometries', params)
        layer = QgsVectorLayer(sub_shp_f, '{0} ({1})'.format("sub","APEX"), 'ogr')

        # Put in the group          
        root = QgsProject.instance().layerTreeRoot()
        swat_group = root.findGroup("APEX") 
        QgsProject.instance().addMapLayer(layer, False)
        swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_subbasin_shapefile.setText(sub_shp_f)

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Checking SUB geometries ... passed")
        self.dlg.label_StepStatus.setText("Step Status: ")
        QCoreApplication.processEvents()   


# River shapefile
def riv_shapefile(self):
    APEXMOD_path_dict = self.dirs_and_paths() 
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Choose RIV Shapefile!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Shapefiles (*.shp);;All files (*.*)"
        )
    if inFileName:
        settings.setValue('/APEXMOD/LastInputPath', os.path.dirname(str(inFileName)))           
        output_dir = APEXMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'
        inName = 'riv_org'
                        
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1] 
            if os.name == 'nt':         
                outfile = ntpath.join(output_dir, inName + suffix)
            else:
                outfile = posixpath.join(output_dir, inName + suffix)                               
            shutil.copy(f, outfile)         
        if os.name == 'nt':
            riv_obj = ntpath.join(output_dir, inName + ".shp")
        else:
            riv_obj = posixpath.join(output_dir, inName + ".shp")
        # time stamp
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Checking RIV geometries ... processing")
        self.dlg.label_StepStatus.setText("Checking 'RIV' ... ")
        QCoreApplication.processEvents()
        # fix geometries
        riv_shp_file = 'riv_apex.shp'
        riv_shp_f = os.path.join(output_dir, riv_shp_file)
        params = {
            'INPUT': riv_obj,
            'OUTPUT': riv_shp_f
        }
        processing.run('native:fixgeometries', params)                
        layer = QgsVectorLayer(riv_shp_f, '{0} ({1})'.format("riv","APEX"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        swat_group = root.findGroup("APEX") 
        QgsProject.instance().addMapLayer(layer, False)
        swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_river_shapefile.setText(riv_shp_f)
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Checking RIV geometries ... passed")
        self.dlg.label_StepStatus.setText("Step Status: ")
        QCoreApplication.processEvents()


def select_mf_model(self):
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Select MODFLOW model folder!"
    options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
    directory = QFileDialog.getExistingDirectory(None,
        title, path, options)
    if directory:
        APEXMOD_path_dict = self.dirs_and_paths() 
        proj = QgsProject.instance()
        Project_Name = QFileInfo(proj.fileName()).baseName()
        Out_folder = APEXMOD_path_dict['MODFLOW']
        #distutils.dir_util.remove_tree(Out_folder)
        distutils.dir_util.copy_tree(directory, Out_folder)
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Copying orginal MODFLOW inputs ... processing")
        self.dlg.progressBar_step.setValue(0)
        QCoreApplication.processEvents()
        count = 0
        filelist =  os.listdir(directory)
        for i in filelist:
            shutil.copy2(os.path.join(directory, i), Out_folder)
            count += 1
            provalue = round(count/len(filelist)*100)
            self.dlg.label_StepStatus.setText(i)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        file_check = ".dis" 
        if any(file.endswith(file_check) for file in os.listdir(Out_folder)):   
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Copied!")
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setText("The MODFlOW model has been successfully copied!")
            msgBox.exec_()
            self.dlg.lineEdit_MODFLOW.setText(Out_folder)
            self.mf_model()
            time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Copying orginal MODFLOW inputs ... passed")
            self.dlg.label_StepStatus.setText('Step Status: ')
            self.dlg.progressBar_step.setValue(0)
            QCoreApplication.processEvents()                
        else:
            msgBox = QMessageBox()
            msgBox.setText("There was a problem copying the folder")
            msgBox.exec_()


def import_mf_grid(self):
    # Initiate function
    APEXMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Choose MODFLOW Grid Shapefile!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Shapefiles (*.shp);;All files (*.*)"
        )
    if inFileName:
        settings.setValue('/APEXMOD/LastInputPath', os.path.dirname(str(inFileName)))
        output_dir = APEXMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Importing MODFLOW object ... processing")
        self.dlg.label_StepStatus.setText("Importing 'MODFLOW object' ... ")
        self.dlg.progressBar_step.setValue(0)
        QCoreApplication.processEvents()

        # inName = os.path.splitext(inFile)[0]
        inName = 'mf_grid_org'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(output_dir, inName + suffix)
            else:
                outfile = posixpath.join(output_dir, inName + suffix)
            shutil.copy(f, outfile)

        if os.name == 'nt':
            mf_grid_obj = ntpath.join(output_dir, inName + ".shp")
        else:
            mf_grid_obj = posixpath.join(output_dir, inName + ".shp")    
        
        # fix geometries
        mf_grid_shp_file = 'mf_grid.shp'
        mf_grid_shp_f = os.path.join(output_dir, mf_grid_shp_file)
        params = {
            'INPUT': mf_grid_obj,
            'OUTPUT': mf_grid_shp_f
        }
        processing.run('native:fixgeometries', params)
        layer = QgsVectorLayer(mf_grid_shp_f, '{0} ({1})'.format("mf_grid","MODFLOW"), 'ogr')        

        # if there is an existing mf_grid shapefile, it will be removed
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("mf_grid (MODFLOW)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        swat_group = root.findGroup("MODFLOW")  
        QgsProject.instance().addMapLayer(layer, False)
        swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_MODFLOW_grid_shapefile.setText(mf_grid_shp_f) 

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Importing MODFLOW object ... passed")
        self.dlg.label_StepStatus.setText("Step Status: ")
        self.dlg.progressBar_step.setValue(100)
        QCoreApplication.processEvents()


def load_str_obd(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Provide 'streamflow.obd' file!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Observation data (*.obd *.OBD);; All files (*.*)"
        )
    if inFileName:
        settings.setValue('/APEXMOD/LastInputPath', os.path.dirname(str(inFileName)))           
        output_dir = APEXMOD_path_dict['apexmf_model']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'

        # inName = os.path.splitext(inFile)[0]
        inName = 'streamflow'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(output_dir, inName + '.obd')
            else:
                outfile = posixpath.join(output_dir, inName + '.obd')             
            shutil.copy(f, outfile)


def load_mf_obd(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/APEXMOD/LastInputPath'):
        path = str(settings.value('/APEXMOD/LastInputPath'))
    else:
        path = ''
    title = "Provide 'modflow.obd' file!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Observation data (*.obd *.OBD);; All files (*.*)"
        )
    if inFileName:
        settings.setValue('/APEXMOD/LastInputPath', os.path.dirname(str(inFileName)))           
        output_dir = APEXMOD_path_dict['apexmf_model']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'
        # inName = os.path.splitext(inFile)[0]
        inName = 'modflow'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(output_dir, inName + '.obd')
            else:
                outfile = posixpath.join(output_dir, inName + '.obd')             
            shutil.copy(f, outfile)








