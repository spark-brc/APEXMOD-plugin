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
from PyQt5.QtWidgets import QMessageBox

# try:
#     import deps.pandas as pd
# except AttributeError:
#     msgBox = QMessageBox()
#     msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
#     msgBox.setWindowTitle("APEXMOD")
#     msgBox.setText("Please, restart QGIS to initialize APEXMOD properly.")
#     msgBox.exec_()


def read_sub_no(self):
    for self.layer in list(QgsProject.instance().mapLayers().values()):
        if self.layer.name() == ("sub (APEX)"):
            self.layer = QgsProject.instance().mapLayersByName("sub (APEX)")[0]
            feats = self.layer.getFeatures()
            # get sub number as a list
            unsorted_subno = [str(f.attribute("Subbasin")) for f in feats]
            # Sort this list
            sorted_subno = sorted(unsorted_subno, key=int)
            ## a = sorted(a, key=lambda x: float(x)
            self.dlg.comboBox_sub_number.clear()
            # self.dlg.comboBox_sub_number.addItem('')
            self.dlg.comboBox_sub_number.addItems(sorted_subno) # NOTE: in addItem list should contain string numbers


def read_rch_files(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    rch_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.RCH"):
        rch_files.append(os.path.basename(filename))
    self.dlg.comboBox_rch_files.clear()
    self.dlg.comboBox_rch_files.addItems(rch_files)


def read_rch_vars(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    wd = APEXMOD_path_dict['apexmf_model']
    rch_file = self.dlg.comboBox_rch_files.currentText()

    columns = pd.read_csv(
                        os.path.join(wd, rch_file),
                        delim_whitespace=True,
                        skiprows=8,
                        nrows=1,
                        header=None
                        )
    col_lst = columns.iloc[0].tolist()
    col_lst.insert(2, 'YEAR')
    col_dic = dict((i, j) for i, j in enumerate(col_lst))
    keys = [x for x in range(5, 39)]
    self.col_dic_f = {k: col_dic[k] for k in keys}
    rch_vars = list(self.col_dic_f.values())
    self.dlg.comboBox_rch_vars.clear()
    self.dlg.comboBox_rch_vars.addItems(rch_vars)
    self.dlg.comboBox_rch_vars.setCurrentIndex(3)
    # return rch_vars


def read_strObd(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    if self.dlg.checkBox_stream_obd.isChecked():
        self.dlg.frame_sd_obd.setEnabled(True)
        self.dlg.radioButton_str_obd_line.setEnabled(True)
        self.dlg.radioButton_str_obd_pt.setEnabled(True)
        self.dlg.spinBox_str_obd_size.setEnabled(True)
        try:
            wd = APEXMOD_path_dict['apexmf_model']
            strObd = pd.read_csv(
                                    wd + "\\streamflow.obd",
                                    delim_whitespace=True,
                                    index_col=0,
                                    parse_dates=True)

            strObd_list = list(strObd)
            self.dlg.comboBox_SD_obs_data.clear()
            self.dlg.comboBox_SD_obs_data.addItems(strObd_list)
        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
            msgBox.setWindowTitle("No 'streamflow.obd' file found!")
            msgBox.setText("Please, provide 'streamflow.obd' file!")
            msgBox.exec_()
            self.dlg.checkBox_stream_obd.setChecked(0)  
            self.dlg.frame_sd_obd.setEnabled(False)
            self.dlg.radioButton_str_obd_line.setEnabled(False)
            self.dlg.radioButton_str_obd_pt.setEnabled(False)
            self.dlg.spinBox_str_obd_size.setEnabled(False)
    else:
        self.dlg.comboBox_SD_obs_data.clear()
        self.dlg.frame_sd_obd.setEnabled(False)
        self.dlg.radioButton_str_obd_line.setEnabled(False)
        self.dlg.radioButton_str_obd_pt.setEnabled(False)
        self.dlg.spinBox_str_obd_size.setEnabled(False)


def sd_plot_daily(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    wd_mf = APEXMOD_path_dict['MODFLOW']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()

    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())
    
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_ylabel(rch_var, fontsize=8)
    ax.tick_params(axis='both', labelsize=8)

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                            os.path.join(wd, "streamflow.obd"),
                            # delim_whitespace=True,
                            sep=r'\s+',
                            index_col=0,
                            header=0,
                            parse_dates=True,
                            delimiter="\t",
                            # na_values=-999
                            )
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()


        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            # Based on APEX Time Step condition
            if self.dlg.radioButton_day.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            elif self.dlg.radioButton_month.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="M")
            else:
                df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="A")
            ax.plot(df.index, df[rch_var], c='limegreen', lw=1, label="Simulated")
            df2 = pd.concat([df, strObd[sub_ob]], axis=1)
            df3 = df2.dropna()

            if self.dlg.radioButton_str_obd_pt.isChecked():
                size = float(self.dlg.spinBox_str_obd_size.value())
                ax.scatter(
                            df3.index, df3[sub_ob], c='m', lw=1, alpha=0.5, s=size, marker='x',
                            label="Observed", zorder=3)
            else:
                ax.plot(
                        df3.index, df3[sub_ob], c='m', lw=1.5, alpha=0.5,
                        label="Observed", zorder=3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2)/
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))))
                )
                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (
                    sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2)
                    )

                ## PBIAS
                PBIAS =  100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))
                ax.text(
                    .01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                    fontsize=8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(
                    .01, 0.90, r'$R^2$: ' + "%.4f" % r_squared,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(
                    .99, 0.95, u'PBIAS: ' + "%.4f" % PBIAS,
                    fontsize=8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
            else:
                ax.text(.01,.95, u'Nash–Sutcliffe: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    transform=ax.transAxes)
                ax.text(.01, 0.90, r'$R^2$: '+ u"---",
                    fontsize=8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(.99, 0.95, u'PBIAS: '+ "---",
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
        except:
            ax.text(
                    0.5, 0.5, u"Running the simulation for a warm-up period!",
                    fontsize=12,
                    horizontalalignment='center',
                    weight='extra bold',
                    color='y',
                    transform=ax.transAxes,
                    )
                    # color = colors[i%4])
    else:
        output_rch = pd.read_csv(
                                os.path.join(wd, rch_file),
                                delim_whitespace=True,
                                skiprows=9,
                                usecols=[0, 1, colNum],
                                names=["idx", "sub", rch_var],
                                index_col=0)
        df = output_rch.loc["REACH"]
        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            if self.dlg.radioButton_day.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            elif self.dlg.radioButton_month.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="M")
            else:
                df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="A")     
            ax.plot(df.index, df[rch_var], c = 'g', lw = 1, label = "Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    # Set title
    if self.dlg.radioButton_day.isChecked() and (self.dlg.comboBox_SD_timeStep.currentText() == "Daily"):   
        ax.set_title('Daily Stream Discharge @ ' + str(outletSubNum), fontsize = 10)
    elif self.dlg.radioButton_month.isChecked() and (self.dlg.comboBox_SD_timeStep.currentText() == "Monthly"):
        ax.set_title('Monthly Stream Discharge @ ' + str(outletSubNum), fontsize = 10)
    elif self.dlg.radioButton_year.isChecked() and (self.dlg.comboBox_SD_timeStep.currentText() == "Annual"):
        ax.set_title('Annual Stream Discharge @ ' + str(outletSubNum), fontsize = 10)

    plt.legend(fontsize=8,  loc="lower right", ncol=2, bbox_to_anchor=(1, 1)) # edgecolor="w",
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()          


def sd_plot_monthly(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')        
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()

    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_ylabel(rch_var, fontsize=8)
    ax.tick_params(axis='both', labelsize=8)


    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                            os.path.join(wd, "streamflow.obd"),
                            sep = '\s+',
                            index_col = 0,
                            header = 0,
                            parse_dates=True,
                            delimiter = "\t",
                            )
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()
        
        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            df = df.resample('M').mean()
            strObdm = strObd.resample('M').mean()
            ax.plot(df.index, df[rch_var], c = 'limegreen', lw = 1, label = "Simulated")
            df2 = pd.concat([df, strObdm[sub_ob]], axis = 1)
            df3 = df2.dropna()
            if self.dlg.radioButton_str_obd_pt.isChecked():
                size = float(self.dlg.spinBox_str_obd_size.value())
                ax.scatter(
                            df3.index, df3[sub_ob], c='m', lw=1, alpha=0.5, s=size, marker='x',
                            label="Observed", zorder=3)
            else:
                ax.plot(
                        df3.index, df3[sub_ob], c='m', lw=1.5, alpha=0.5,
                        label="Observed", zorder=3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
    
            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))
                    ))
                )
                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))
                ax.text(.01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(.01, 0.90, r'$R^2$: '+ "%.4f" % r_squared,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(.99, 0.95, u'PBIAS: '+ "%.4f" % PBIAS,
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
            else:
                ax.text(.01,.95, u'Nash–Sutcliffe: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    transform=ax.transAxes)
                ax.text(.01, 0.90, r'$R^2$: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(.99, 0.95, u'PBIAS: '+ "---",
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
        except:         
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)
                    # color = colors[i%4])
    else:
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            df = df.resample('M').mean()
            ax.plot(df.index, df[rch_var], c='g', lw=1, label="Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    ax.set_title('Monthly Stream Discharge @ ' + str(outletSubNum) , fontsize = 10)
    plt.legend(fontsize = 8, edgecolor="w", loc = "lower right", ncol=2, bbox_to_anchor = (1, 1))
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()          


def sd_plot_annual(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')        
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()

    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())

    fig, ax = plt.subplots(figsize = (9,4))
    ax.set_ylabel(r'Stream Discharge $[m^3/s]$', fontsize = 8)
    ax.tick_params(axis='both', labelsize=8)

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                                os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")

        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            dfa = df.resample('A').mean()
            strObda = strObd.resample('A').mean()
            ax.plot(dfa.index, dfa[rch_var], c = 'limegreen', lw = 1, label = "Simulated")
            df2 = pd.concat([dfa, strObda[sub_ob]], axis = 1)
            df3 = df2.dropna()
            if self.dlg.radioButton_str_obd_pt.isChecked():
                size = float(self.dlg.spinBox_str_obd_size.value())
                ax.scatter(
                            df3.index, df3[sub_ob], c='m', lw=1, alpha=0.5, s=size, marker='x',
                            label="Observed", zorder=3)
            else:
                ax.plot(
                        df3.index, df3[sub_ob], c='m', lw=1.5, alpha=0.5,
                        label="Observed", zorder=3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
    
            if (len(df3[sub_ob]) > 1):

                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))

                ax.text(
                    .01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)

                ax.text(
                    .01, 0.90, r'$R^2$: '+ "%.4f" % r_squared,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)

                ax.text(
                    .99, 0.95, u'PBIAS: '+ "%.4f" % PBIAS,
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)

            else:
                ax.text(
                    .01,.95, u'Nash–Sutcliffe: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    transform=ax.transAxes)
    
                ax.text(
                    .01, 0.90, r'$R^2$: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)

                ax.text(
                    .99, 0.95, u'PBIAS: '+ "---",
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
    
        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)
                    # color = colors[i%4])
    else:
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]

        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            dfa = df.resample('A').mean()
            ax.plot(dfa.index, dfa[rch_var], c = 'g', lw = 1, label = "Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    # Set title
    ax.set_title('Annual Stream Discharge @ ' + str(outletSubNum)  , fontsize = 10)
    plt.legend(fontsize = 8, edgecolor="w", loc = "lower right", ncol=2, bbox_to_anchor = (1, 1))
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()

# NOTE: Not yet workable
def sd_plot_month_to_year(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')        
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()

    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())

    fig, ax = plt.subplots(figsize = (9,4))
    ax.set_ylabel(r'Stream Discharge $[m^3/s]$', fontsize = 8)
    ax.tick_params(axis='both', labelsize=8)

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                            os.path.join(wd, "streamflow.obd"),
                            sep = '\s+',
                            index_col = 0,
                            header = 0,
                            parse_dates=True,
                            delimiter = "\t")
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()
        # sub_ob = 'sub_58'
        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="M")
            dfa = df.resample('A').mean()
            strObda = strObd.resample('A').mean()
            ax.plot(dfa.index, dfa[rch_var], c = 'limegreen', lw = 1, label = "Simulated")
            df2 = pd.concat([dfa, strObda[sub_ob]], axis = 1)
            df3 = df2.dropna()
            if self.dlg.radioButton_str_obd_pt.isChecked():
                size = float(self.dlg.spinBox_str_obd_size.value())
                ax.scatter(
                            df3.index, df3[sub_ob], c='m', lw=1, alpha=0.5, s=size, marker='x',
                            label="Observed", zorder=3)
            else:
                ax.plot(
                        df3.index, df3[sub_ob], c='m', lw=1.5, alpha=0.5,
                        label="Observed", zorder=3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))
                    ))
                )
                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))
                ax.text(
                    .01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(
                    .01, 0.90, r'$R^2$: '+ "%.4f" % r_squared,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)
                ax.text(
                    .99, 0.95, u'PBIAS: '+ "%.4f" % PBIAS,
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
            else:
                ax.text(
                    .01,.95, u'Nash–Sutcliffe: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    transform=ax.transAxes)
    
                ax.text(
                    .01, 0.90, r'$R^2$: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    color='limegreen',
                    transform=ax.transAxes)

                ax.text(
                    .99, 0.95, u'PBIAS: '+ "---",
                    fontsize = 8,
                    horizontalalignment='right',
                    color='limegreen',
                    transform=ax.transAxes)
    
        except:
            ax.text(
                    .5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)
                    # color = colors[i%4])
    else:
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]

        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq = "M")
            dfa = df.resample('A').mean()
            ax.plot(dfa.index, dfa[rch_var], c = 'g', lw = 1, label = "Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    # Set title
    ax.set_title('Annual Stream Discharge @ ' + str(outletSubNum)  , fontsize = 10)
    plt.legend(fontsize = 8, edgecolor="w", loc = "lower right", ncol=2, bbox_to_anchor = (1, 1))
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()

"""
Export data only selected
"""
def export_sd_daily(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period() 
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")
    
    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()
    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())

    # Add info
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                            os.path.join(wd, "streamflow.obd"),
                            sep = '\s+',
                            index_col = 0,
                            header = 0,
                            parse_dates=True,
                            delimiter = "\t")
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            # Based on APEX Time Step condition
            if self.dlg.radioButton_day.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            elif self.dlg.radioButton_month.isChecked():
                df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="M")
            else:
                df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="A")

            df2 = pd.concat([df, strObd[sub_ob]], axis=1)
            df3 = df2.dropna()
            if (len(df3[sub_ob]) > 1):

                ## R-squared
                r_squared = (
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2)/
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())**2) * (sum((df3[rch_var]-df3[rch_var].mean())**2))))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) /
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS = 100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))

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
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        df = df.loc[df["sub"] == int(outletSubNum)]
        if self.dlg.radioButton_day.isChecked():
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
        elif self.dlg.radioButton_month.isChecked():
            df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="M")
        else:
            df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq="A")

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

    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()    
    
    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())

    # Add info
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                                os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()
        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            dfm = df.resample('M').mean()
            strObdm = strObd.resample('M').mean()
            df2 = pd.concat([dfm, strObdm[sub_ob]], axis = 1)
            df3 = df2.dropna()
            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2) /
                    ((sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))))
                )
                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS = 100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))
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
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
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
    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()

    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())

    # Add info
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(
                                os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")

        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_rch.index[0] == 1):
            df = output_rch.loc[outletSubNum]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq = "M")
            dfa = df.resample('A').mean()
            strObda = strObd.resample('A').mean()
            df2 = pd.concat([dfa, strObda[sub_ob]], axis = 1)
            df3 = df2.dropna()

            if (len(df3[sub_ob]) > 1):

                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS = 100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))

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
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        try:
            df = output_rch.loc[outletSubNum]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]), freq = "M")
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
    rch_file = self.dlg.comboBox_rch_files.currentText()
    rch_var = self.dlg.comboBox_rch_vars.currentText()

    # rch_vars = self.read_rch_vars()
    rch_vars = self.col_dic_f
    c = ([k for k, v in rch_vars.items() if v == rch_var])
    colNum = c[0] # get flow_out
    outletSubNum = int(self.dlg.comboBox_sub_number.currentText())

    # Add info
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        strObd = pd.read_csv(os.path.join(wd, "streamflow.obd"),
                                sep = '\s+',
                                index_col = 0,
                                header = 0,
                                parse_dates=True,
                                delimiter = "\t")

        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        sub_ob = self.dlg.comboBox_SD_obs_data.currentText()

        try:
        # if (output_rch.index[0] == 1):
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
            dfa = df.resample('A').mean()
            strObda = strObd.resample('A').mean()
            df2 = pd.concat([dfa, strObda[sub_ob]], axis = 1)
            df3 = df2.dropna()

            if (len(df3[sub_ob]) > 1):
                ## R-squared
                r_squared = (
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())*(df3[rch_var]-df3[rch_var].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[sub_ob] - df3[sub_ob].mean())**2)* (sum((df3[rch_var]-df3[rch_var].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[rch_var] - df3[sub_ob])**2) / 
                    sum((df3[sub_ob] - (df3[sub_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[sub_ob] - df3[rch_var]) / sum(df3[sub_ob]))

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
        output_rch = pd.read_csv(
                            os.path.join(wd, rch_file),
                            delim_whitespace=True,
                            skiprows=9,
                            usecols=[0, 1, colNum],
                            names=["idx", "sub", rch_var],
                            index_col=0)
        df = output_rch.loc["REACH"]
        try:
            df = df.loc[df["sub"] == int(outletSubNum)]
            df.index = pd.date_range(startDate, periods=len(df[rch_var]))
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
