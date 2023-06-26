# -*- coding: utf-8 -*-
from builtins import str
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.core import QgsProject
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import glob

# import numpy as np
import os
import pandas as pd
from datetime import datetime
from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QSlider, QMessageBox

from .apexmod_utils import DefineTime, ObjFns


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
            ## a = sorted(a, key=lambda x: float(x)
            self.dlg.comboBox_cha_sub_no.clear()
            # self.dlg.comboBox_cha_sub_no.addItem('')
            self.dlg.comboBox_cha_sub_no.addItems(sorted_subno) # NOTE: in addItem list should contain string numbers
            self.dlg.horizontalSlider_cha_start_year.setMinimum(int(start_year))
            self.dlg.horizontalSlider_cha_start_year.setMaximum(int(end_year))
            self.dlg.horizontalSlider_cha_start_year.setValue(int(start_year))
            self.dlg.horizontalSlider_cha_start_year.setTickInterval(int(1))
            self.dlg.horizontalSlider_cha_start_year.setTickPosition(QSlider.TicksBelow)

def read_cha_vars(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    cha_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.RCH"):
        cha_files.append(os.path.basename(filename))
    columns = pd.read_csv(
                        os.path.join(wd, cha_files[0]),
                        delim_whitespace=True,
                        skiprows=8,
                        nrows=1,
                        header=None
                        )
    col_lst_ = columns.iloc[0].tolist()
    col_lst_.insert(2, 'YEAR')
    col_dic = dict((i, j) for i, j in enumerate(col_lst_))
    keys = [x for x in range(5, len(col_lst_))]
    self.col_dic_f = {k: col_dic[k] for k in keys}
    cha_vars = list(self.col_dic_f.values())
    self.dlg.comboBox_cha_vars.clear()
    self.dlg.comboBox_cha_vars.addItems(cha_vars)
    self.dlg.comboBox_cha_vars.setCurrentIndex(3)
    return col_lst_

def read_cha_sim_data(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    cha_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.RCH"):
        cha_files.append(os.path.basename(filename))
    col_lst = read_cha_vars(self)
    df = pd.read_csv(
                        os.path.join(wd, cha_files[0]),
                        delim_whitespace=True,
                        skiprows=9,
                        usecols=[x for x in range(len(col_lst))],
                        header=None)
    df.columns = col_lst
    df_ = df.loc[df['RCID'] == 'REACH']
    df_.set_index('GIS', inplace=True)
    return df_

def read_cha_obd_files(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    cha_obd_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.obd"):
        if os.path.basename(filename)[:4] == 'cha':
            cha_obd_files.append(os.path.basename(filename))
    self.dlg.comboBox_cha_obd_files.clear()
    self.dlg.comboBox_cha_obd_files.addItems(cha_obd_files)

def get_cha_sims_obds(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    startDate, endDate, duration = DefineTime.get_start_end_time(self)
    current_year = self.dlg.horizontalSlider_cha_start_year.value()

    # sims first
    sub_no = self.dlg.comboBox_cha_sub_no.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()
    cha_df = read_cha_sim_data(self)
    sims = cha_df.loc[int(sub_no), cha_var]
    # Based on APEX Time Step condition
    if self.dlg.radioButton_day.isChecked():
        sims.index = pd.date_range(startDate, periods=len(sims))
    elif self.dlg.radioButton_month.isChecked():
        sims.index = pd.date_range(startDate, periods=len(sims), freq="M")
    else:
        sims.index = pd.date_range(startDate, periods=len(sims), freq="A")
    # obds first
    infile = self.dlg.comboBox_cha_obd_files.currentText()
    obds = pd.read_csv(
                        os.path.join(wd, infile), 
                        sep='\t',
                        comment='#',
                        index_col=0,
                        na_values=[-999, ""],
                        parse_dates=True)
    obd_var = self.dlg.comboBox_cha_obd_gages.currentText()
    obds = obds.loc[:, obd_var]

    if self.dlg.comboBox_cha_time.currentText() == 'Monthly':
        sims = sims.resample('M').mean()
        obds = obds.resample('M').mean()
    if self.dlg.comboBox_cha_time.currentText() == 'Annual':
        sims = sims.resample('A').mean()
        obds = obds.resample('A').mean()
    sims = sims["1/1/{}".format(current_year):endDate]
    obds = obds["1/1/{}".format(current_year):endDate]
    df_ = pd.concat([sims, obds], axis=1)
    df_d = df_.dropna(how='any', axis=0)
    sims_ = df_d.iloc[:, 0].to_numpy()
    obds_ = df_d.iloc[:, 1].to_numpy()
    return sims_, obds_, df_

def cha_sim_obd_plot(self):
    sims, obds, df = get_cha_sims_obds(self)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df.index, df.iloc[:, 0], c='limegreen', lw=1, label="Simulated")
    if self.dlg.radioButton_cha_obd_point.isChecked():
        size = float(self.dlg.spinBox_cha_obd_size.value())
        ax.scatter(
                    df.index, df.iloc[:, 1], c='m', lw=1, alpha=0.5, s=size, marker='x',
                    label="Observed", zorder=3)        
    else:
        ax.plot(
                df.index, df.iloc[:, 1], c='m', lw=1.5, alpha=0.5,
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
        fontsize=8,
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
    plt.legend(fontsize=8, loc="lower right", ncol=2, bbox_to_anchor=(1, 1))
    plt.show()

def cha_sim_obd_with_scatter(self):
    sims, obds, df = get_cha_sims_obds(self)
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(9, 4))
    axes[0].plot(df.index, df.iloc[:, 0], c='limegreen', lw=1, label="Simulated")
    if self.dlg.radioButton_cha_obd_point.isChecked():
        size = float(self.dlg.spinBox_cha_obd_size.value())
        axes[0].scatter(
                    df.index, df.iloc[:, 1], c='m', lw=1, alpha=0.5, s=size, marker='x',
                    label="Observed", zorder=3)        
    else:
        axes[0].plot(
                df.index, df.iloc[:, 1], c='m', lw=1.5, alpha=0.5,
                label="Observed", zorder=3)
    nse = ObjFns.nse(sims, obds)
    rmse = ObjFns.rmse(sims, obds)
    pbias = ObjFns.pbias(sims, obds)
    rsq = ObjFns.rsq(sims, obds)
    axes[0].text(
        .01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % nse,
        fontsize=8,
        horizontalalignment='left',
        color='limegreen',
        transform=axes[0].transAxes)
    axes[0].text(
        .01, 0.90, r'$R^2$: ' + "%.4f" % rsq,
        fontsize=8,
        horizontalalignment='left',
        color='limegreen',
        transform=axes[0].transAxes)
    axes[0].text(
        .99, 0.95, u'PBIAS: ' + "%.4f" % pbias,
        fontsize=8,
        horizontalalignment='right',
        color='limegreen',
        transform=axes[0].transAxes)
    axes[0].text(
        .99, 0.90, u'RMSE: ' + "%.4f" % rmse,
        fontsize=8,
        horizontalalignment='right',
        color='limegreen',
        transform=axes[0].transAxes)
    new_list = sims + obds
    axes[0].legend(fontsize=8, loc="lower right", ncol=2, bbox_to_anchor=(1, 1))
    axes[1].grid(True)
    axes[1].plot([0, max(new_list)], [0, max(new_list)], 'k--', alpha=0.2)
    axes[1].scatter(sims, obds, c=u'#1f77b4', s=size, marker='o', alpha=0.5)
    axes[1].set_xlabel('Simulated', fontsize=10)
    axes[1].set_ylabel('Observed', fontsize=10)
    plt.show()

def cha_plot(self):
    startDate, endDate, duration = DefineTime.get_start_end_time(self)
    current_year = self.dlg.horizontalSlider_cha_start_year.value()
    sub_no = self.dlg.comboBox_cha_sub_no.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()

    cha_df = read_cha_sim_data(self)
    df = cha_df.loc[int(sub_no), cha_var]
    fig, ax = plt.subplots(figsize=(9, 4))
    if self.dlg.radioButton_day.isChecked():
        df.index = pd.date_range(startDate, periods=len(df))
    if self.dlg.radioButton_month.isChecked():
        df.index = pd.date_range(startDate, periods=len(df), freq='M')
    if self.dlg.radioButton_year.isChecked():
        df.index = pd.date_range(startDate, periods=len(df), freq='A')

    if self.dlg.comboBox_cha_time.currentText() == 'Monthly':
        df = df.resample('M').mean()
        ax.set_title('Monthly {} @ {}'.format(cha_var, sub_no), fontsize=10)
    if self.dlg.comboBox_cha_time.currentText() == 'Annual':
        df = df.resample('A').mean()
        ax.set_title('Annual {} @ {}'.format(cha_var, sub_no), fontsize=10)
    df = df["1/1/{}".format(current_year):endDate]

    ax.set_ylabel(cha_var, fontsize=8)
    ax.tick_params(axis='both', labelsize=8)
    ax.plot(df.index, df)
    plt.show()


def read_cha_obd_files(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    cha_obd_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.obd"):
        if os.path.basename(filename)[:3] == 'cha':
            cha_obd_files.append(os.path.basename(filename))
    self.dlg.comboBox_cha_obd_files.clear()
    self.dlg.comboBox_cha_obd_files.addItems(cha_obd_files)

def get_cha_obd_gages(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    infile = self.dlg.comboBox_cha_obd_files.currentText()
    df = pd.read_csv(
                        os.path.join(wd, infile),
                        comment='#',
                        sep='\t',
                        index_col=0,
                        na_values=[-999, ""],
                        parse_dates=True)
    self.dlg.comboBox_cha_obd_gages.clear()
    self.dlg.comboBox_cha_obd_gages.addItems(df.columns.tolist())

"""
Export data only selected
"""
def export_cha(self):
    # Add info
    version = "version 1.4."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    APEXMOD_path_dict = self.dirs_and_paths()
    startDate, endDate, duration = DefineTime.get_start_end_time(self)
    outfolder = APEXMOD_path_dict['exported_files']
    current_year = self.dlg.horizontalSlider_cha_start_year.value()
    sub_no = self.dlg.comboBox_cha_sub_no.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()
    cha_df = read_cha_sim_data(self)
    df = cha_df.loc[int(sub_no), cha_var]
    # Based on APEX Time Step condition
    if self.dlg.radioButton_day.isChecked():
        df.index = pd.date_range(startDate, periods=len(df))
    if self.dlg.radioButton_month.isChecked():
        df.index = pd.date_range(startDate, periods=len(df), freq='M')
    if self.dlg.radioButton_year.isChecked():
        df.index = pd.date_range(startDate, periods=len(df), freq='A')
    if self.dlg.comboBox_cha_time.currentText() == 'Monthly':
        df = df.resample('M').mean()
    if self.dlg.comboBox_cha_time.currentText() == 'Annual':
        df = df.resample('A').mean()
    df = df["1/1/{}".format(current_year):endDate]

    # ------------ Export Data to file -------------- #
    # with open(os.path.join(outfolder, "apexmf_solute(" + str(sub_no) + ")_{}".format(timestep)+".txt"), 'w') as f:

    with open(os.path.join(outfolder, "cha_{}_sub({})_{}.txt".format(cha_var[:-2], sub_no, self.dlg.comboBox_cha_time.currentText())), 'w') as f:
        # f.write("# apexmf_reach(" + str(sub_no) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")

        f.write("# cha_{}_sub({})_{}.txt is created by APEXMOD plugin {} {}\n".format(cha_var, sub_no, self.dlg.comboBox_cha_time.currentText(), version, time))
        df.to_csv(f, index_label="Date", sep='\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
        f.write('\n')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    # msgBox.setText("'apexmf_reach(" + str(sub_no)+")_annual.txt' file is exported to your 'exported_files' folder!")
    msgBox.setText("'cha_{}_sub({})_{}.txt' file was exported to 'exported files' folder.".format(cha_var, sub_no, self.dlg.comboBox_cha_time.currentText()))
    msgBox.exec_()

def export_cha_sims_obds(self):
    # Add info
    version = "version 1.4."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    APEXMOD_path_dict = self.dirs_and_paths()
    outfolder = APEXMOD_path_dict['exported_files']
    sims, obds, df = get_cha_sims_obds(self)
    nse = ObjFns.nse(sims, obds)
    rmse = ObjFns.rmse(sims, obds)
    pbias = ObjFns.pbias(sims, obds)
    rsq = ObjFns.rsq(sims, obds)
    sub_no = self.dlg.comboBox_cha_sub_no.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()
    cha_time = self.dlg.comboBox_cha_time.currentText()
    # ------------ Export Data to file -------------- #
    # with open(os.path.join(outfolder, "apexmf_solute(" + str(sub_no) + ")_{}".format(timestep)+".txt"), 'w') as f:

    with open(os.path.join(outfolder, "cha_{}_sub({})_{}_obd.txt".format(cha_var[:-2], sub_no, cha_time)), 'w') as f:
        # f.write("# apexmf_reach(" + str(sub_no) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")
        f.write("# cha_{}_sub({})_{} with observation.txt is created by APEXMOD plugin {} {}\n".format(cha_var, sub_no, cha_time, version, time))
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
    msgBox.setText("'cha_{}_sub({})_{}_obd.txt' file was exported to 'exported files' folder.".format(cha_var, sub_no, cha_time))
    msgBox.exec_()

def export_sd_daily(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    
    cha_file = self.dlg.comboBox_cha_files.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()
    # cha_vars = self.read_cha_vars()
    cha_vars = self.col_dic_f
    c = ([k for k, v in cha_vars.items() if v == cha_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_cha_sub_no.currentText())

    # Add info
    version = "version 1.4."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                            os.path.join(wd, "streamflow.obd"),
                            sep = '\s+',
                            index_col = 0,
                            header = 0,
                            parse_dates=True,
                            na_values=[-999, ""],
                            delimiter = "\t")
        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        df = output_cha.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_cha.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            # Based on APEX Time Step condition
            if self.dlg.radioButton_day.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[cha_var]))
            elif self.dlg.radioButton_month.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[cha_var]), freq="M")
            else:
                df.index = pd.date_range(startDate, periods=len(df[cha_var]), freq="A")

            df2 = pd.concat([df, strObd[sub_ob]], axis=1)
            df3 = df2.dropna()
            if (len(df3[sub_ob]) > 1):

                ## R-squared
                r_squared = (
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[cha_var]-df3[cha_var].mean())))**2)/
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())**2) * (sum((df3[cha_var]-df3[cha_var].mean())**2))))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[cha_var] - df3[sub_ob])**2) /
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS = 100*(sum(df3[sub_ob] - df3[cha_var]) / sum(df3[sub_ob]))

            # ------------ Export Data to file -------------- #
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!") 

            if self.dlg.radioButton_day.isChecked():
                with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)+")_daily.txt"), 'w') as f:
                    f.write("# apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                            +")_daily.txt is created by APEXMOD plugin "+ version + time + "\n")
                    df3.drop('sub', 1).to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))
                msgBox.setText(
                            "'apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                            + ")_daily.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()
            elif self.dlg.radioButton_month.isChecked():
                with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)+")_monthly.txt"), 'w') as f:
                    f.write("# apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                            + ")_monthly.txt is created by APEXMOD plugin "+ version + time + "\n")
                    df3.drop('sub', 1).to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))
                msgBox.setText(
                            "'apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                            + ")_monthly.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()
            else:
                with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)+")_annual.txt"), 'w') as f:
                    f.write("# apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                            + ")_monthly.txt is created by APEXMOD plugin "+ version + time + "\n")
                    df3.drop('sub', 1).to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))
                msgBox.setText(
                            "'apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                            + ")_annual.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()
        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()
    else:
        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        df = output_cha.loc["REACH"]
        df = df.loc[df["sub"] == int(outletSubNum)]
        if self.dlg.radioButton_day.isChecked():
            df.index = pd.date_range(startDate, periods=len(df[cha_var]))
        elif self.dlg.radioButton_month.isChecked():
            df.index = pd.date_range(startDate, periods=len(df[cha_var]), freq="M")
        else:
            df.index = pd.date_range(startDate, periods=len(df[cha_var]), freq="A")

        # ------------ Export Data to file -------------- #
        with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")_daily"+".txt"), 'w') as f:
            f.write("# apexmf_reach(" + str(outletSubNum) + ")_daily"+".txt is created by APEXMOD plugin "+ version + time + "\n")
            df.drop('sub', 1).to_csv(f, index_label="Date", sep='\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
            f.write('\n')
            f.write("# Statistics\n")
            # f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
            f.write("Nash–Sutcliffe: ---\n")
            f.write("R-squared: ---\n")
            f.write("PBIAS: ---\n")

        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        msgBox.setWindowTitle("Exported!")
        msgBox.setText("'apexmf_reach(" + str(outletSubNum)+")_daily.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()

        # except:
        #     msgBox = QMessageBox()
        #     msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
        #     msgBox.setWindowTitle("Not Ready!")
        #     msgBox.setText("Nothing to write down right now!")
        #     msgBox.exec_()


def export_sd_monthly(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    cha_file = self.dlg.comboBox_cha_files.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()    
    
    # cha_vars = self.read_cha_vars()
    cha_vars = self.col_dic_f
    c = ([k for k, v in cha_vars.items() if v == cha_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_cha_sub_no.currentText())

    # Add info
    version = "version 1.4."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                                os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")
        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        df = output_cha.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()
        try:
        # if (output_cha.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[cha_var]))
            dfm = df.resample('M').mean()
            strObdm = strObd.resample('M').mean()
            df2 = pd.concat([dfm, strObdm[sub_ob]], axis = 1)
            df3 = df2.dropna()
            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[cha_var]-df3[cha_var].mean())))**2) /
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[cha_var]-df3[cha_var].mean())**2))))
                )
                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[cha_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS = 100*(sum(df3[sub_ob] - df3[cha_var]) / sum(df3[sub_ob]))
            # ------------ Export Data to file -------------- #
            with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)+")_monthly.txt"), 'w') as f:
                f.write("# apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                        +")_monthly.txt is created by APEXMOD plugin "+ version + time + "\n")
                df3.drop('sub', 1).to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                f.write('\n')
                f.write("# Statistics\n")
                f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText(
                        "'apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                        + ")_monthly.txt' file is exported to your 'exported_files' folder!")
            msgBox.exec_()
        except:         
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()
    else:
        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        df = output_cha.loc["REACH"]
        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[cha_var]))
            dfm = df.resample('M').mean()

            # ------------ Export Data to file -------------- #
            with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")_monthly"+".txt"), 'w') as f:
                f.write("# apexmf_reach(" + str(outletSubNum) + ")_monthly"+".txt is created by APEXMOD plugin "+ version + time + "\n")
                dfm.drop('sub', 1).to_csv(f, index_label="Date", sep='\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                f.write('\n')
                f.write("# Statistics\n")
                # f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                f.write("Nash–Sutcliffe: ---\n")
                f.write("R-squared: ---\n")
                f.write("PBIAS: ---\n")

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText("'apexmf_reach(" + str(outletSubNum)+")_monthly.txt' file is exported to your 'exported_files' folder!")
            msgBox.exec_()
        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Nothing to write down right now!")
            msgBox.exec_()


def export_sd_mTa(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    cha_file = self.dlg.comboBox_cha_files.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()

    # cha_vars = self.read_cha_vars()
    cha_vars = self.col_dic_f
    c = ([k for k, v in cha_vars.items() if v == cha_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_cha_sub_no.currentText())

    # Add info
    version = "version 1.4."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                                os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")

        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_cha.index[0] == 1):
            df = output_cha.loc[outletSubNum]
            df.index = pd.date_range(startDate, periods=len(df[cha_var]), freq = "M")
            dfa = df.resample('A').mean()
            strObda = strObd.resample('A').mean()
            df2 = pd.concat([dfa, strObda[sub_ob]], axis = 1)
            df3 = df2.dropna()

            if (len(df3[sub_ob]) > 1):

                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[cha_var]-df3[cha_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[cha_var]-df3[cha_var].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[cha_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS = 100*(sum(df3[sub_ob] - df3[cha_var]) / sum(df3[sub_ob]))

            # ------------ Export Data to file -------------- #
            with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)+")_annual.txt"), 'w') as f:
                f.write("# apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                        +")_annual.txt is created by APEXMOD plugin "+ version + time + "\n")
                df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                f.write('\n')
                f.write("# Statistics\n")
                f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText("'apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                        +")_annual.txt' file is exported to your 'exported_files' folder!")
            msgBox.exec_()

        except:         
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()
    else:
        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        try:
            df = output_cha.loc[outletSubNum]
            df.index = pd.date_range(startDate, periods=len(df[cha_var]), freq = "M")
            dfa = df.resample('A').mean()

            # ------------ Export Data to file -------------- #
            with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")_annual"+".txt"), 'w') as f:
                f.write("# apexmf_reach(" + str(outletSubNum) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")
                dfa.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                f.write('\n')
                f.write("# Statistics\n")
                # f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                f.write("Nash–Sutcliffe: ---\n")
                f.write("R-squared: ---\n")
                f.write("PBIAS: ---\n")

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText("'apexmf_reach(" + str(outletSubNum)+")_annual.txt' file is exported to your 'exported_files' folder!")
            msgBox.exec_()
        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Nothing to write down right now!")
            msgBox.exec_()


def export_sd_annual(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    cha_file = self.dlg.comboBox_cha_files.currentText()
    cha_var = self.dlg.comboBox_cha_vars.currentText()

    # cha_vars = self.read_cha_vars()
    cha_vars = self.col_dic_f
    c = ([k for k, v in cha_vars.items() if v == cha_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_cha_sub_no.currentText())

    # Add info
    version = "version 1.4."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")

        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        df = output_cha.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_cha.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[cha_var]))
            dfa = df.resample('A').mean()
            strObda = strObd.resample('A').mean()
            df2 = pd.concat([dfa, strObda[sub_ob]], axis = 1)
            df3 = df2.dropna()

            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[cha_var]-df3[cha_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[cha_var]-df3[cha_var].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[cha_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[sub_ob] - df3[cha_var]) / sum(df3[sub_ob]))

            # ------------ Export Data to file -------------- #
            with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)+")_annual.txt"), 'w') as f:
                f.write("# apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                        +")_annual.txt is created by APEXMOD plugin "+ version + time + "\n")
                df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                f.write('\n')
                f.write("# Statistics\n")
                f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText("'apexmf_reach(" + str(outletSubNum) + ")"+"_ob("+ str(sub_ob)
                        +")_annual.txt' file is exported to your 'exported_files' folder!")
            msgBox.exec_()

        except:         
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()
    else:
        output_cha = pd.read_csv(
                            os.path.join(wd, cha_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", cha_var],
                            index_col=0)
        df = output_cha.loc["REACH"]
        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[cha_var]))
            dfa = df.resample('A').mean()

            # ------------ Export Data to file -------------- #
            with open(os.path.join(outfolder, "apexmf_reach(" + str(outletSubNum) + ")_annual"+".txt"), 'w') as f:
                f.write("# apexmf_reach(" + str(outletSubNum) + ")_annual"+".txt is created by APEXMOD plugin "+ version + time + "\n")
                dfa.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                f.write('\n')
                f.write("# Statistics\n")
                # f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                f.write("Nash–Sutcliffe: ---\n")
                f.write("R-squared: ---\n")
                f.write("PBIAS: ---\n")
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText("'apexmf_reach(" + str(outletSubNum)+")_annual.txt' file is exported to your 'exported_files' folder!")
            msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Nothing to write down right now!")
            msgBox.exec_()
