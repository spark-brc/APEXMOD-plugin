from builtins import str
from builtins import range
import os
import os.path
import operator
import math, datetime
from qgis.core import (
                        QgsVectorLayer, QgsField,
                        QgsProject, QgsFeatureIterator, QgsVectorFileWriter,
                        QgsLayerTreeLayer)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from .apexmod_utils import DefineTime

def config_sets(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    outfd = APEXMOD_path_dict['MODFLOW']
    flags = []
    if self.dlg.radioButton_drain_act.isChecked():
        flags.append(1)
    if self.dlg.radioButton_drain_inact.isChecked():
        flags.append(0)
    if self.dlg.radioButton_ActRT3D.isChecked():
        flags.append(1)
    if self.dlg.radioButton_NoRT3D.isChecked():
        flags.append(0)
    if self.dlg.checkBox_mf_obs.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    with open(os.path.join(outfd, "apexmf_link.txt"), 'w', newline="") as f:
        f.write("{}\tflag for routing DRAIN cell outflow rates to APEX subareas (DRAIN package must be active)\n".format(flags[0]))
        f.write("{}\tflag for running RT3D for groundwater reactive transport\n".format(flags[1]))
        f.write("{}\tflag for reading in MODFLOW observation cells from 'modflow.obs'\n".format(flags[2]))

def print_output_options(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    outfd = APEXMOD_path_dict['MODFLOW']
    flags = []
    if self.dlg.checkBox_apex_dp_sub.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    if self.dlg.checkBox_mf_recharge.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    if self.dlg.checkBox_channel_depth.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    if self.dlg.checkBox_river_stage.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    if self.dlg.checkBox_gw_sw_grid.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    if self.dlg.checkBox_gw_sw_sub.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    if self.dlg.checkBox_printing_m_a.isChecked():
        flags.append(1)
    else:
        flags.append(0)
    with open(os.path.join(outfd, "apexmf_link.txt"), 'a', newline="") as f:
        f.write("Optional output for APEX-MODFLOW (0=no; 1=yes)\n")
        f.write("{}\tAPEX Percolation and Recharge (mm) (for each SUB)\n".format(flags[0]))
        f.write("{}\tMODFLOW Recharge (m3/day) (for each MODFLOW Cell)\n".format(flags[1]))
        f.write("{}\tAPEX Channel Depth (m) (for each APEX subarea)\n".format(flags[2]))
        f.write("{}\tMODFLOW River Stage (m) (for each MODFLOW River Cell)\n".format(flags[3]))
        f.write("{}\tGroundwater/Surface Water Exchange (m3/day) (for each MODFLOW River Cell)\n".format(flags[4]))
        f.write("{}\tGroundwater/Surface Water Exchange (m3/day) (for each APEX subarea)'\n".format(flags[5]))
        f.write("{}\tFlag for writing monthly and annual average output for APEX-MODFLOW variables'\n".format(flags[6]))

def print_specific_days(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    outfd = APEXMOD_path_dict['MODFLOW']
    stdate, eddate, sim_period = DefineTime.get_start_end_time(self)
    # Obtain time step
    step = self.dlg.spinBox_freq_apexmf_output.value()

    lines = []
    if step != 1:
        lines.append(str(int(math.floor(sim_period / step) + 1))+"\n")
        lines.append(str(1)+"\n")  # force to include the first day
        for i in range(step, sim_period+1, step):
            lines.append(str(i)+"\n")
    else:
        lines.append(str(int(math.floor(sim_period / step)))+"\n")
        for i in range(step, sim_period+1, step):
            lines.append(str(i)+"\n")
    with open(os.path.join(outfd, "apexmf_link.txt"), 'a', newline="") as f:
        f.write("# == Write APEX-MODFLOW output only on specified days == \n")
        # f.write(str(info)+'\n')
        for line in lines:
            f.write(str(line))

def groundwater_delay(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    outfd = APEXMOD_path_dict['MODFLOW']
    lines = []
    info2 = "# == Groundwater delay == \n"
    lines.append(info2)

    if self.dlg.radioButton_gw_delay_multi.isChecked():
        lines.append("1\t0 = read in a single value for all SUBs; 1 = read in one value for each subarea\n")
        input1 = QgsProject.instance().mapLayersByName("gw_delay")[0]
        data = [i.attributes() for i in input1.getFeatures()]
        sub_idx = input1.dataProvider().fields().indexFromName("Subbasin")
        data_sort = sorted(data, key=operator.itemgetter(sub_idx))
        for i in data_sort:
            lines.append(str(i[1]) + "\n")
    else:
        gwd = self.dlg.spinBox_gw_delay_single.value()
        lines.append("0\t0 = read in a single value for all SUBs; 1 = read in one value for each subarea\n")
        lines.append(str(gwd) + "\tGW_DELAY : Groundwater delay [days]\n")
    with open(os.path.join(outfd, "apexmf_link.txt"), 'a', newline="") as f:
        for line in lines:
            f.write(str(line))

def write_apexmf_link(self):
    config_sets(self)
    print_output_options(self)
    print_specific_days(self)
    groundwater_delay(self)

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("Your configuration settings have been exported to your APEX-MODFLOW model!")
    msgBox.exec_()
