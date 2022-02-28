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
import numpy as np
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
from .apexmod_utils import ObjFns



def get_sub_no(self):
    for self.layer in list(QgsProject.instance().mapLayers().values()):
        if self.layer.name() == ("sub (APEX)"):
            self.layer = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
            feats = self.layer.getFeatures()
            # get sub number as a list
            unsorted_subno = [str(f.attribute("Subbasin")) for f in feats]
            # Sort this list
            self.sorted_subno = sorted(unsorted_subno, key=int)

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
    version = "version 1.3."
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


def read_salt_ions_channel(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd_mf = APEXMOD_path_dict['SALINITY']
    startDate = stdate.strftime("%m/%d/%Y")
    start_year = stdate.strftime("%Y")
    end_year = eddate.strftime("%Y")
    self.dlg.comboBox_salt_time.addItems(['Daily', 'Monthly', 'Annual'])
    get_sub_no(self)
    self.dlg.comboBox_salt_sub.clear()
    self.dlg.comboBox_salt_sub.addItems(self.sorted_subno)
    self.dlg.horizontalSlider_salt_start_year.setMinimum(int(start_year))
    self.dlg.horizontalSlider_salt_start_year.setMaximum(int(end_year))
    self.dlg.horizontalSlider_salt_start_year.setValue(int(start_year))
    self.dlg.horizontalSlider_salt_start_year.setTickInterval(int(1))
    self.dlg.horizontalSlider_salt_start_year.setTickPosition(QSlider.TicksBelow)

    infile = 'salt.output.channels'

    salt_ions_df = pd.read_csv(
                os.path.join(wd_mf, infile),
                delim_whitespace=True,
                skiprows=4,
                index_col=0)
    # drop unnecessary cols
    salt_ions_df.drop(['year', 'day', 'area(ha)'], axis=1, inplace=True)            
    # rename cols
    salt_ions = ['SO4', 'Ca2', 'Mg2', 'Na', 'K','Cl','CO3', 'HCO3']
    salt_types = ['_load', '_conc']
    salt_vars = []
    for st in salt_types:
        for si in salt_ions:
            salt_vars.append(si+st)
    salt_ions = ['Q_runoff', 'Q_total'] + salt_ions
    salt_vars = ['Q_runoff', 'Q_total'] + salt_vars
    salt_ions_df.columns = salt_vars
    self.dlg.comboBox_salt_vars.clear()
    self.dlg.comboBox_salt_vars.addItems(salt_ions)    
    return salt_ions_df

def salt_plot(self, salt_ions_df):
    stdate, eddate = self.define_sim_period()
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    current_year = self.dlg.horizontalSlider_salt_start_year.value()
    sub_no = self.dlg.comboBox_salt_sub.currentText()
    salt_var = self.dlg.comboBox_salt_vars.currentText()
    if self.dlg.radioButton_salt_mass.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
        salt_var = salt_var + '_load'
    if self.dlg.radioButton_salt_conc.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
        salt_var = salt_var + '_conc'    
    df = salt_ions_df.loc[int(sub_no), salt_var]
    df.index = pd.date_range(startDate, periods=len(df))
    if self.dlg.comboBox_salt_time.currentText() == 'Monthly':
        df = df.resample('M').mean()
    if self.dlg.comboBox_salt_time.currentText() == 'Annual':
        df = df.resample('A').mean()
    df = df["1/1/{}".format(current_year):endDate]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_ylabel(salt_var, fontsize=8)
    ax.tick_params(axis='both', labelsize=8)
    ax.plot(df.index, df)
    plt.show()

def salt_stacked_plot(self, salt_ions_df):
    stdate, eddate = self.define_sim_period()
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    current_year = self.dlg.horizontalSlider_salt_start_year.value()
    sub_no = self.dlg.comboBox_salt_sub.currentText()
    salt_var = self.dlg.comboBox_salt_vars.currentText()

    if salt_var == 'Q_runoff' or salt_var == 'Q_total':
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setWindowTitle("No flow!")
        msgBox.setText("Please, select a salt ion!")
        msgBox.exec_()
    else:
        if self.dlg.radioButton_salt_mass.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
            load_cols = salt_ions_df.columns.tolist()[2:10]
            df = salt_ions_df.loc[int(sub_no), load_cols]
        if self.dlg.radioButton_salt_conc.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
            conc_cols = salt_ions_df.columns.tolist()[10:]
            df = salt_ions_df.loc[int(sub_no), conc_cols]
        df.index = pd.date_range(startDate, periods=len(df))
        if self.dlg.comboBox_salt_time.currentText() == 'Monthly':
            df = df.resample('M').mean()
        if self.dlg.comboBox_salt_time.currentText() == 'Annual':
            df = df.resample('A').mean()
        df = df["1/1/{}".format(current_year):endDate]
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.stackplot(
            df.index, df.iloc[:, 0], df.iloc[:, 1], df.iloc[:, 2], df.iloc[:, 3],
            df.iloc[:, 4], df.iloc[:, 5], df.iloc[:, 6], df.iloc[:, 7], labels=df.columns.tolist()
            )
        ax.legend(loc='upper left',
                    bbox_to_anchor=(-0.05, 1.1),
                    fontsize=8,
                    ncol=8)
        plt.show()

def export_salt_ion(self, salt_ions_df):
    # Add info
    version = "version 1.3."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    APEXMOD_path_dict = self.dirs_and_paths()
    outfolder = APEXMOD_path_dict['exported_files']

    stdate, eddate = self.define_sim_period()
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    current_year = self.dlg.horizontalSlider_salt_start_year.value()
    sub_no = self.dlg.comboBox_salt_sub.currentText()
    salt_var = self.dlg.comboBox_salt_vars.currentText()
    if self.dlg.radioButton_salt_mass.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
        salt_var = salt_var + '_load'
    if self.dlg.radioButton_salt_conc.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
        salt_var = salt_var + '_conc'    
    df = salt_ions_df.loc[int(sub_no), salt_var]
    df.index = pd.date_range(startDate, periods=len(df))
    if self.dlg.comboBox_salt_time.currentText() == 'Monthly':
        df = df.resample('M').mean()
    if self.dlg.comboBox_salt_time.currentText() == 'Annual':
        df = df.resample('A').mean()
    df = df["1/1/{}".format(current_year):endDate]

    # ------------ Export Data to file -------------- #
    # with open(os.path.join(outfolder, "apexmf_solute(" + str(sub_no) + ")_{}".format(timestep)+".txt"), 'w') as f:

    with open(os.path.join(outfolder, "salt_{}_sub({})_{}.txt".format(salt_var, sub_no, self.dlg.comboBox_salt_time.currentText())), 'w') as f:
        # f.write("# apexmf_reach(" + str(sub_no) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")

        f.write("# salt_{}_sub({})_{}.txt is created by APEXMOD plugin {} {}\n".format(salt_var, sub_no, self.dlg.comboBox_salt_time.currentText(), version, time))
        df.to_csv(f, index_label="Date", sep='\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
        f.write('\n')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    # msgBox.setText("'apexmf_reach(" + str(sub_no)+")_annual.txt' file is exported to your 'exported_files' folder!")
    msgBox.setText("'salt_{}_sub({})_{}.txt' file was exported to 'exported files' folder.".format(salt_var, sub_no, self.dlg.comboBox_salt_time.currentText()))
    msgBox.exec_()


def export_salt_mass_conc(self, salt_ions_df):
    # Add info
    version = "version 1.3."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    APEXMOD_path_dict = self.dirs_and_paths()
    outfolder = APEXMOD_path_dict['exported_files']
    stdate, eddate = self.define_sim_period()
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    current_year = self.dlg.horizontalSlider_salt_start_year.value()
    sub_no = self.dlg.comboBox_salt_sub.currentText()
    salt_var = self.dlg.comboBox_salt_vars.currentText()
    if salt_var == 'Q_runoff' or salt_var == 'Q_total':
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setWindowTitle("No flow!")
        msgBox.setText("Please, select a salt ion!")
        msgBox.exec_()
    else:
        if self.dlg.radioButton_salt_mass.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
            load_cols = salt_ions_df.columns.tolist()[2:10]
            df = salt_ions_df.loc[int(sub_no), load_cols]
            salt_var = 'mass'
        if self.dlg.radioButton_salt_conc.isChecked() and not (salt_var == 'Q_runoff' or salt_var == 'Q_total'):
            conc_cols = salt_ions_df.columns.tolist()[10:]
            df = salt_ions_df.loc[int(sub_no), conc_cols]
            salt_var = 'conc'
        df.index = pd.date_range(startDate, periods=len(df))
        if self.dlg.comboBox_salt_time.currentText() == 'Monthly':
            df = df.resample('M').mean()
        if self.dlg.comboBox_salt_time.currentText() == 'Annual':
            df = df.resample('A').mean()
        df = df["1/1/{}".format(current_year):endDate]

    # ------------ Export Data to file -------------- #
    # with open(os.path.join(outfolder, "apexmf_solute(" + str(sub_no) + ")_{}".format(timestep)+".txt"), 'w') as f:

    with open(os.path.join(outfolder, "salt_{}_sub({})_{}.txt".format(salt_var, sub_no, self.dlg.comboBox_salt_time.currentText())), 'w') as f:
        # f.write("# apexmf_reach(" + str(sub_no) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")

        f.write("# salt_{}_sub({})_{}.txt is created by APEXMOD plugin {} {}\n".format(salt_var, sub_no, self.dlg.comboBox_salt_time.currentText(), version, time))
        df.to_csv(f, index_label="Date", sep='\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
        f.write('\n')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    # msgBox.setText("'apexmf_reach(" + str(sub_no)+")_annual.txt' file is exported to your 'exported_files' folder!")
    msgBox.setText("'salt_{}_sub({})_{}.txt' file was exported to 'exported files' folder.".format(salt_var, sub_no, self.dlg.comboBox_salt_time.currentText()))
    msgBox.exec_()

def read_salt_obd_files(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    salt_obd_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.obd"):
        if os.path.basename(filename)[:4] == 'salt':
            salt_obd_files.append(os.path.basename(filename))
    self.dlg.comboBox_salt_obd_files.clear()
    self.dlg.comboBox_salt_obd_files.addItems(salt_obd_files)

def get_salt_obd_gages(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    infile = self.dlg.comboBox_salt_obd_files.currentText()
    df = pd.read_csv(
                        os.path.join(wd, infile), 
                        sep='\t',
                        index_col=0,
                        na_values=[-999, ""],
                        parse_dates=True)
    self.dlg.comboBox_salt_obd_gages.clear()
    self.dlg.comboBox_salt_obd_gages.addItems(df.columns.tolist())


def get_salt_sims_obds(self, salt_ions_df):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    stdate, eddate = self.define_sim_period()
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    current_year = self.dlg.horizontalSlider_salt_start_year.value()

    # sims first
    sub_no = self.dlg.comboBox_salt_sub.currentText()
    salt_var = self.dlg.comboBox_salt_vars.currentText()
    if self.dlg.radioButton_salt_mass.isChecked():
        # load_cols = salt_ions_df.columns.tolist()[2:10]
        salt_var = salt_var + '_load'
    if self.dlg.radioButton_salt_conc.isChecked():
        # load_cols = salt_ions_df.columns.tolist()[2:10]
        salt_var = salt_var + '_conc'
    sims = salt_ions_df.loc[int(sub_no), salt_var]
    sims.index = pd.date_range(startDate, periods=len(sims))

    # obds first
    infile = self.dlg.comboBox_salt_obd_files.currentText()
    obds = pd.read_csv(
                        os.path.join(wd, infile), 
                        sep='\t',
                        index_col=0,
                        na_values=[-999, ""],
                        parse_dates=True)
    obd_var = self.dlg.comboBox_salt_obd_gages.currentText()
    obds = obds.loc[:, obd_var]

    if self.dlg.comboBox_salt_time.currentText() == 'Monthly':
        sims = sims.resample('M').mean()
        obds = obds.resample('M').mean()
    if self.dlg.comboBox_salt_time.currentText() == 'Annual':
        sims = sims.resample('A').mean()
        obds = obds.resample('A').mean()
    sims = sims["1/1/{}".format(current_year):endDate]
    obds = obds["1/1/{}".format(current_year):endDate]


    df_ = pd.concat([sims, obds], axis=1)
    df_d = df_.dropna(how='any', axis=0)
    sims_ = df_d.iloc[:, 0].to_numpy()
    obds_ = df_d.iloc[:, 1].to_numpy()
    return sims_, obds_, df_
    
    
def salt_sim_obd_plot(self, salt_ions_df):
    sims, obds, df = get_salt_sims_obds(self, salt_ions_df)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df.index, df.iloc[:, 0], c='limegreen', lw=1, label="Simulated")
    if self.dlg.radioButton_salt_obd_pts.isChecked():
        size = float(self.dlg.spinBox_salt_obd_size.value())
        ax.scatter(
                    df.index, df.iloc[:, 1], c='m', lw=1, alpha=0.5, s=size, marker='x',
                    label="Observed", zorder=3)        
    else:
        ax.plot(
                df.index, df.iloc[:, 1], c='m',  marker='x', lw=1.5, alpha=0.5,
                label="Observed", zorder=3)
    nse = ObjFns.nse(sims, obds)
    rmse = ObjFns.rmse(sims, obds)
    pbias = ObjFns.pbias(sims, obds)
    rsq = ObjFns.rsq(sims, obds)
    ax.text(
        .01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % nse,
        fontsize=8,
        horizontalalignment='left',
        color='limegreen',
        transform=ax.transAxes)
    ax.text(
        .01, 0.90, r'$R^2$: ' + "%.4f" % rsq,
        fontsize = 8,
        horizontalalignment='left',
        color='limegreen',
        transform=ax.transAxes)
    ax.text(
        .99, 0.95, u'PBIAS: ' + "%.4f" % pbias,
        fontsize=8,
        horizontalalignment='right',
        color='limegreen',
        transform=ax.transAxes)
    ax.text(
        .99, 0.90, u'RMSE: ' + "%.4f" % rmse,
        fontsize=8,
        horizontalalignment='right',
        color='limegreen',
        transform=ax.transAxes)
    plt.legend(fontsize=8,  loc="lower right", ncol=2, bbox_to_anchor=(1, 1))
    plt.show() 

def export_salt_sims_obds(self, salt_ions_df):
    # Add info
    version = "version 1.3."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    APEXMOD_path_dict = self.dirs_and_paths()
    outfolder = APEXMOD_path_dict['exported_files']
    sims, obds, df = get_salt_sims_obds(self, salt_ions_df)

    nse = ObjFns.nse(sims, obds)
    rmse = ObjFns.rmse(sims, obds)
    pbias = ObjFns.pbias(sims, obds)
    rsq = ObjFns.rsq(sims, obds)


    sub_no = self.dlg.comboBox_salt_sub.currentText()
    salt_var = self.dlg.comboBox_salt_vars.currentText()
    salt_time = self.dlg.comboBox_salt_time.currentText()


    # ------------ Export Data to file -------------- #
    # with open(os.path.join(outfolder, "apexmf_solute(" + str(sub_no) + ")_{}".format(timestep)+".txt"), 'w') as f:

    with open(os.path.join(outfolder, "salt_{}_sub({})_{}_obd.txt".format(salt_var, sub_no, salt_time)), 'w') as f:
        # f.write("# apexmf_reach(" + str(sub_no) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")

        f.write("# salt_{}_sub({})_{} with observation.txt is created by APEXMOD plugin {} {}\n".format(salt_var, sub_no, salt_time, version, time))
        df.to_csv(f, index_label="Date", sep='\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8', na_rep='-999')
        f.write('\n')
        f.write("# Statistics\n")
        f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(nse) + "\n"))
        f.write("R-squared: " + str('{:.4f}'.format(rsq) + "\n"))
        f.write("PBIAS: " + str('{:.4f}'.format(pbias) + "\n"))
        f.write("RMSE: " + str('{:.4f}'.format(rmse) + "\n"))

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("'salt_{}_sub({})_{}_obd.txt' file was exported to 'exported files' folder.".format(salt_var, sub_no, salt_time))
    msgBox.exec_()