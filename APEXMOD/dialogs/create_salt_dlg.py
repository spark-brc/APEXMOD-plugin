"""
/***************************************************************************
 APEXMODDialog
                                 A QGIS plugin
 This plugin displays the result of SM simulation
                             -------------------
        begin                : 2017-08-02
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Seonggyu Park
        email                : seonggyu.park@brc.tamus.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import os.path

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt import QtGui, uic
from qgis.core import QgsProject

from datetime import datetime
from APEXMOD.APEXMOD import *
# from APEXMOD.APEXMOD_dialog import APEXMODDialog


from APEXMOD.pyfolder import write_rt3d

from PyQt5.QtWidgets import (
            QInputDialog, QLineEdit, QDialog, QFileDialog, QSizePolicy,
            QMessageBox)


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/salt.ui'))

class CreateSALT(QDialog, FORM_CLASS):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        #------------------------------------------------------------------------------------------------
        # init conc
        # self.pushButton_porosity_r.clicked.connect(self.loadPorosity)
        # self.pushButton_no3_r.clicked.connect(self.loadNO3)
        # self.pushButton_writeRT3D.clicked.connect(self.test)
        # self.pushButton_rt3d_obs_points.clicked.connect(self.use_obs_points)
        # self.pushButton_rt3d_obs_shapefile.clicked.connect(self.rt3d_obs_shapefile)

        #------------------------------------------------------------------------------------------------

    def time_stamp_start(self, des):
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_rt3d_log.append(time+' -> ' + des + " ... processing")
        self.label_rt3d_status.setText("{} ... ".format(des))
        QCoreApplication.processEvents()

    def time_stamp_end(self, des):
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_rt3d_log.append(time+' -> ' + des + " ... passed")
        self.label_rt3d_status.setText('Step Status: ')
        QCoreApplication.processEvents()

    def loadPorosity(self):
        write_rt3d.loadPorosity(self)

    # init CONC
    def loadNO3(self):
        write_rt3d.loadNO3(self)



    # output settings
    def use_obs_points(self):
        write_rt3d.use_obs_points(self)
        write_rt3d.select_obs_grids(self)
        write_rt3d.create_rt3d_obs(self)
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setIconPixmap(QtGui.QPixmap(':/APEXMOD/pics/modflow_obs.png'))
        msgBox.setMaximumSize(1000, 200)  # resize not working
        msgBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) # resize not working
        msgBox.setWindowTitle("Hello?")
        msgBox.exec_()

    # Select features by manual
    def rt3d_obs_shapefile(self):
        write_rt3d.rt3d_obs_shapefile(self)
        write_rt3d.create_rt3d_obs(self)
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setIconPixmap(QtGui.QPixmap(':/APEXMOD/pics/modflow_obs.png'))
        msgBox.setMaximumSize(1000, 200) # resize not working
        msgBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) # resize not working
        msgBox.setWindowTitle("Hello?")
        msgBox.exec_()



    def test(self):
        write_rt3d.write_rt3d_inputs(self)




    # NOTE: QUESTIONS!! Is this function should be here too? ######
    def dirs_and_paths(self):
        global APEXMOD_path_dict
        # project places
        Projectfolder = QgsProject.instance().readPath("./") 
        proj = QgsProject.instance() 
        Project_Name = QFileInfo(proj.fileName()).baseName()

        # definition of folders
        org_shps = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "GIS/org_shps")
        apexmf_shps = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "GIS/apexmf_shps")
        apexmf_model = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "APEX-MODFLOW")
        Table = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "GIS/Table")
        apexmf_exes = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "apexmf_exes")
        exported_files = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "exported_files")
        scn_folder = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "Scenarios")
        mf_model = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "APEX-MODFLOW/MODFLOW")

        APEXMOD_path_dict = {
                                'org_shps': org_shps,
                                'apexmf_shps': apexmf_shps,
                                'apexmf_model': apexmf_model,
                                'Table': Table,
                                'apexmf_exes': apexmf_exes,
                                'exported_files': exported_files,
                                'Scenarios': scn_folder,
                                'MODFLOW': mf_model
                                }
        return APEXMOD_path_dict




