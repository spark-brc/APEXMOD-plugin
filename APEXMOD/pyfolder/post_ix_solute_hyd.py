# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
from qgis.core import (
                        QgsProject
                        )
# from qgis.PyQt import QtCore, QtGui, QtSql
from datetime import datetime
import pandas as pd
import os
import glob
from PyQt5.QtGui import QIcon, QColor, QImage, QPainter, QPen, QFont
from PyQt5.QtWidgets import QSlider, QMessageBox
from qgis.PyQt.QtCore import QVariant, QCoreApplication, QSize, Qt, QPoint, QRect
import calendar
# import processing
from qgis.gui import QgsMapCanvas
import glob
from PIL import Image
import matplotlib.pyplot as plt


def read_sub_no(self):
    stdate, eddate = self.define_sim_period()
    start_year = stdate.strftime("%Y")
    end_year = eddate.strftime("%Y")
    for self.layer in list(QgsProject.instance().mapLayers().values()):
        if self.layer.name() == ("sub (APEX)"):
            self.layer = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
            feats = self.layer.getFeatures()
            # get sub number as a list
            unsorted_subno = [str(f.attribute("Subbasin")) for f in feats]
            # Sort this list
            sorted_subno = sorted(unsorted_subno, key=int)
            self.dlg.comboBox_sub_no_solute.clear()
            self.dlg.comboBox_sub_no_solute.addItems(sorted_subno) # NOTE: in addItem list should contain string numbers
            self.dlg.comboBox_solute_time.clear()
            self.dlg.comboBox_solute_time.addItems(['Daily', 'Monthly', 'Annual'])
            self.dlg.horizontalSlider_solute_start_year.setMinimum(int(start_year))
            self.dlg.horizontalSlider_solute_start_year.setMaximum(int(end_year))
            self.dlg.horizontalSlider_solute_start_year.setValue(int(start_year))
            self.dlg.horizontalSlider_solute_start_year.setTickInterval(int(1))
            self.dlg.horizontalSlider_solute_start_year.setTickPosition(QSlider.TicksBelow)

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
    comps = [i.lower() for i in comps_dic.values()]
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
    self.dlg.comboBox_solutes_solute.clear()
    self.dlg.comboBox_solutes_solute.addItems(fullnams)


def read_solute_df(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd_mf = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m/%d/%Y")
    comp = self.dlg.comboBox_solutes_solute.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    y = ("Groundwater/Surface", "for", "--Calculated", "Positive:", "Negative:", "Day:", "subarea") # Remove unnecssary lines
    if comp == 'nitrate':
        infile = "amf_apex_rivno3.out"
        with open(os.path.join(wd_mf, infile), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
        df = pd.DataFrame({'subs':[int(x.split()[0]) for x in data], 'rates':[float(x.split()[1]) for x in data]})
    if comp == 'phosphorus':
        infile = "amf_apex_rivP.out"
        with open(os.path.join(wd_mf, infile), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
        df = pd.DataFrame({'subs':[int(x.split()[0]) for x in data], 'rates':[float(x.split()[1]) for x in data]})
    if (
        comp == "sulfate" or comp == "calcium" or comp == "magnesium" or comp == "sodium" or
        comp == "potassium" or comp == "chloride" or comp == "carbonate" or comp == "bicarbonate"):
        infile = "amf_apex_rivSalt.out"
        with open(os.path.join(wd_mf, infile), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
        df = pd.DataFrame({'subs':[int(x.split()[0]) for x in data], 'rates':[float(x.split()[1]) for x in data]})
    sub_no = self.dlg.comboBox_sub_no_solute.currentText()
    df = df.loc[df['subs']==int(sub_no)]
    df.index = pd.date_range(startDate, periods=len(df['subs']))
    if self.dlg.comboBox_solute_time.currentText() == 'Monthly':
        df = df.resample('M').mean()
    if self.dlg.comboBox_solute_time.currentText() == 'Annual':
        df = df.resample('A').mean()
    return df

def solute_plot(self):
    stdate, eddate = self.define_sim_period()
    endDate = eddate.strftime("%m/%d/%Y")
    current_year = self.dlg.horizontalSlider_solute_start_year.value()
    df = read_solute_df(self)
    df = df["1/1/{}".format(current_year):endDate]
    comp = self.dlg.comboBox_solutes_solute.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()
    # df = self.read_solute_df()

    # sub_no = self.dlg.comboBox_sub_no_solute.currentText()
    # df = df.loc[df['subs']==int(sub_no)]
    # df.index = pd.date_range(startDate, periods=len(df['subs']))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_ylabel(comp + ' (kg/day)', fontsize=8)
    ax.tick_params(axis='both', labelsize=8)
    ax.plot(df.index, df.rates)
    plt.show()

def export_solute_df(self):
    # Add info
    version = "version 1.2."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    endDate = eddate.strftime("%m/%d/%Y")
    outfolder = APEXMOD_path_dict['exported_files']
    current_year = self.dlg.horizontalSlider_solute_start_year.value()
    timestep = self.dlg.comboBox_solute_time.currentText()
    sub_no = self.dlg.comboBox_sub_no_solute.currentText()
    df = read_solute_df(self)
    df = df["1/1/{}".format(current_year):endDate]
    comp = self.dlg.comboBox_solutes_solute.currentText().replace('(', '').replace(')', '').strip().split()[1].lower()

    # ------------ Export Data to file -------------- #
    # with open(os.path.join(outfolder, "apexmf_solute(" + str(sub_no) + ")_{}".format(timestep)+".txt"), 'w') as f:

    with open(os.path.join(outfolder, "apexriv_{}_sub({})_{}.txt".format(comp, sub_no, timestep)), 'w') as f:
        # f.write("# apexmf_reach(" + str(sub_no) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")

        f.write("# apexriv_{}_sub({})_{}.txt is created by APEXMOD plugin {} {}\n".format(comp, sub_no, timestep, version, time))
        df.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
        f.write('\n')
        # f.write("# Statistics\n")
        # # f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
        # f.write("Nash–Sutcliffe: ---\n")
        # f.write("R-squared: ---\n")
        # f.write("PBIAS: ---\n")
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    # msgBox.setText("'apexmf_reach(" + str(sub_no)+")_annual.txt' file is exported to your 'exported_files' folder!")
    msgBox.setText("'apexriv_{}_sub({})_{}.txt' file was exported to 'exported files' folder.".format(comp, sub_no, timestep))
    msgBox.exec_()


