# -*- coding: utf-8 -*-
from builtins import str
from qgis.PyQt.QtCore import QFileInfo
from qgis.core import QgsProject                      
import os

### Please, someone teaches me how to use a function in APEXMOD main script file.
#  from APEXMOD.APEXMOD import *
def retrieve_ProjHistory(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Define folders and files
    apexmf_model = APEXMOD_path_dict['apexmf_model']
    org_shps = APEXMOD_path_dict['org_shps']
    apexmf_shps = APEXMOD_path_dict['apexmf_shps']
    mf_folder = APEXMOD_path_dict['MODFLOW']
    # retrieve TxtInOut
    if os.path.isfile(os.path.join(apexmf_model, "APEXCONT.DAT")):
        # stdate, eddate = self.define_sim_period()
        self.dlg.tabWidget.setTabEnabled(1, True)
        self.dlg.lineEdit_TxtInOut.setText(apexmf_model)
        self.define_sim_period()
    else:
        self.dlg.textEdit_sm_link_log.append("Missing -> Provide APEX model.")
    # retrieve sub
    if os.path.isfile(os.path.join(org_shps, 'sub_apex.shp')):
        self.dlg.lineEdit_subbasin_shapefile.setText(os.path.join(org_shps, 'sub_apex.shp'))
    else:
        self.dlg.textEdit_sm_link_log.append("Provide sub Shapefile.")
    # retrieve riv
    if os.path.isfile(os.path.join(org_shps, 'riv_apex.shp')):
        self.dlg.lineEdit_river_shapefile.setText(os.path.join(org_shps, 'riv_apex.shp'))
    else:
        self.dlg.textEdit_sm_link_log.append("Provide riv Shapefile.")      
    # retrieve MODFLOW model
    if any(file.endswith(".dis") for file in os.listdir(mf_folder)):
        self.dlg.lineEdit_MODFLOW.setText(mf_folder)
    else:
        self.dlg.textEdit_sm_link_log.append("Provide MODFLOW model")
    # retrieve MODFLOW grid shapefile (MODFLOW)
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("mf_grid (MODFLOW)"):
            # self.dlg.mGroupBox.setCollapsed(False)
            self.dlg.mf_option_1.setChecked(True)
            self.dlg.lineEdit_MODFLOW_grid_shapefile.setText(lyr.source())
    # retrieve mf_obs_points (MODFLOW)
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("mf_obs_points (MODFLOW)"):
            # self.dlg.mGroupBox.setCollapsed(False)
            self.dlg.groupBox_obs_points.setChecked(True)
            self.dlg.lineEdit_mf_obs_points.setText(lyr.source())
        elif lyr.name() == ("mf_obs (APEX-MODFLOW)"):
            self.dlg.lineEdit_mf_obs_shapefile.setText(lyr.source())
    # retrieve MODFLOW model
    if any(file.endswith(".dis") for file in os.listdir(mf_folder)):
        self.dlg.lineEdit_MODFLOW.setText(mf_folder)
        self.dlg.groupBox_MF_options.setEnabled(True)
        self.dlg.mf_option_1.setEnabled(True)
        self.dlg.mf_option_2.setEnabled(True)           
        self.dlg.mf_option_3.setEnabled(False)
        self.dlg.groupBox_river_cells.setEnabled(True)
        self.dlg.river_frame.setEnabled(False)
        self.dlg.radioButton_mf_riv3.setEnabled(False)  
    else:
        self.dlg.mf_option_1.setEnabled(False)
        self.dlg.mf_option_2.setEnabled(False)          
        self.dlg.mf_option_3.setEnabled(True)   
        self.dlg.textEdit_sm_link_log.append("Provide MODFLOW model")
    # if os.path.isfile(os.path.join(apexmf_model, "modflow.mfn")):
    # retrieve linkge files
    linkfiles = ["link_grid_sa", "link_sa_grid", "apexmf_link.txt"]
    if all(os.path.isfile(os.path.join(mf_folder, x)) for x in linkfiles):
        self.dlg.pushButton_execute_linking.setEnabled(False)
        self.dlg.progressBar_sm_link.setValue(100)
        self.dlg.checkBox_filesPrepared.setChecked(1)
        self.dlg.tabWidget.setTabEnabled(2, True)
    else:
        self.dlg.pushButton_execute_linking.setEnabled(True)
        self.dlg.progressBar_sm_link.setValue(0)
        self.dlg.checkBox_filesPrepared.setChecked(0)
    # retrive APEX-MODFLOW result files
    # TODO: check output files for APEX model
    output_files = ["amf_MF_recharge.out", "amf_apex_channel.out"]
    if all(os.path.isfile(os.path.join(mf_folder, x)) for x in output_files):
        self.dlg.tabWidget.setTabEnabled(3, True)
    else:
        self.dlg.tabWidget.setTabEnabled(3, False)

        
def wt_act(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Define folders and files
    apexmf_model = APEXMOD_path_dict['MODFLOW']
    # retrive apexmf_out_MF_obs
    if os.path.isfile(os.path.join(apexmf_model, "modflow.obs")):
        self.dlg.checkBox_mf_obs.setChecked(True)
        self.dlg.groupBox_plot_wt.setEnabled(True)
    else:
        self.dlg.groupBox_plot_wt.setEnabled(False)
# def check_apexmf_model_and_files(self):
#   check_txtinout = os.path.join(APEXMOD_path_dict['apexmf_model'], "file.cio")
#   if os.path.isfile(check_txtinout) is True:
#       self.dlg.lineEdit_TxtInOut.setText(APEXMOD_path_dict['apexmf_model'])
#   check_hrushp = os.path.join(APEXMOD_path_dict['org_shps'], 'hru_apexmf.shp')
#   if os.path.isfile(check_hrushp) is True:
#       self.dlg.lineEdit_hru_shapefile.setText(check_hrushp)