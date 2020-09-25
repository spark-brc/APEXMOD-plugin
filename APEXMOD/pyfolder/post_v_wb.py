# -*- coding: utf-8 -*-
from builtins import str
from builtins import range
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer,
    QgsField)
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtCore import QCoreApplication
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
import glob

# try:
#     import deps.pandas as pd
# except AttributeError:
#     msgBox = QMessageBox()
#     msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
#     msgBox.setWindowTitle("APEXMOD")
#     msgBox.setText("Please, restart QGIS to initialize APEXMOD properly.")
#     msgBox.exec_()


def read_dws_files(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    dws_files = []
    for filename in glob.glob(str(APEXMOD_path_dict['apexmf_model'])+"/*.DWS"):
        dws_files.append(os.path.basename(filename))
    self.dlg.comboBox_dws_files.clear()
    self.dlg.comboBox_dws_files.addItems(dws_files)


def read_std_dates(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    dws_file = self.dlg.comboBox_dws_files.currentText()

    startDate = stdate.strftime("%m-%d-%Y")
    df = pd.read_csv(
                os.path.join(wd, dws_file),
                delim_whitespace=True,
                skiprows=8,
                )
    df.index = pd.date_range(startDate, periods=len(df)) 
    if self.dlg.radioButton_std_day.isChecked():
        self.dlg.doubleSpinBox_std_w_exag.setEnabled(False)
        dateList = df.index.strftime("%m-%d-%Y").tolist()
        self.dlg.comboBox_std_sdate.clear()
        self.dlg.comboBox_std_sdate.addItems(dateList)
        self.dlg.comboBox_std_edate.clear()
        self.dlg.comboBox_std_edate.addItems(dateList)
        self.dlg.comboBox_std_edate.setCurrentIndex(len(dateList)-1)
    elif self.dlg.radioButton_std_month.isChecked():
        self.dlg.doubleSpinBox_std_w_exag.setEnabled(True)
        dfm = df.resample('M').mean()
        dfmList = dfm.index.strftime("%b-%Y").tolist()
        self.dlg.comboBox_std_sdate.clear()
        self.dlg.comboBox_std_sdate.addItems(dfmList)
        self.dlg.comboBox_std_edate.clear()
        self.dlg.comboBox_std_edate.addItems(dfmList)
        self.dlg.comboBox_std_edate.setCurrentIndex(len(dfmList)-1)
    elif self.dlg.radioButton_std_year.isChecked():
        self.dlg.doubleSpinBox_std_w_exag.setEnabled(True)
        dfa = df.resample('A').mean()
        dfaList = dfa.index.strftime("%Y").tolist()
        self.dlg.comboBox_std_sdate.clear()
        self.dlg.comboBox_std_sdate.addItems(dfaList)
        self.dlg.comboBox_std_edate.clear()
        self.dlg.comboBox_std_edate.addItems(dfaList)
        self.dlg.comboBox_std_edate.setCurrentIndex(len(dfaList)-1)


def plot_wb_day(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    startDate = stdate.strftime("%m-%d-%Y")

    dws_file = self.dlg.comboBox_dws_files.currentText()
    df = pd.read_csv(
                os.path.join(wd, dws_file),
                delim_whitespace=True,
                skiprows=8,
                )    

    df.index = pd.date_range(startDate, periods=len(df))
    df = df[['RFV', 'ET', 'Q', 'SSF', 'PRK', 'DPRK', 'RSSF', 'SW']]
    df['DP'] = df['RFV'] - df['ET'] - df['Q'] - df['SSF']

    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    dff = df[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    
    # == Precipitation ============================================================
    axes[0].stackplot(dff.index, dff.RFV, color='slateblue')
    axes[0].set_ylim((dff.RFV.max() + dff.RFV.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    # Title
    if self.dlg.checkBox_std_title.isChecked():
        axes[0].set_title('Water Balance - Daily [mm]', fontsize=12, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].stackplot(dff.index, dff.SW, color='lightgreen')
    axes[1].set_ylim(
        (dff.RSSF + dff.SSF + dff.Q).max(),
        (dff.RSSF + dff.SSF + dff.Q + dff.SW).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    axes[2].stackplot(
        dff.index, dff.RSSF, dff.SSF, dff.Q, dff.SW,
        colors=['darkgreen', 'forestgreen', 'limegreen', 'lightgreen', 'b', 'dodgerblue', 'skyblue'])
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    axes[2].stackplot(dff.index, (dff.SW*-1), (dff.DP*-1), (dff.SW*-1))
    axes[2].set_ylim(
        -1*(dff.SW + dff.DP).max(),
        (dff.RSSF + dff.SSF + dff.Q).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].stackplot(dff.index, dff.SW + dff.DP + dff.SW, color=['skyblue'])
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.SW + dff.DP + dff.SW).max()),
        ((dff.SW + dff.DP + dff.SW).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(Rectangle((0, 0), 0.1, 0.1, fc=c, alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def plot_wb_dToM_A(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']

    startDate = stdate.strftime("%m-%d-%Y")
    dws_file = self.dlg.comboBox_dws_files.currentText()
    df = pd.read_csv(
                os.path.join(wd, dws_file),
                delim_whitespace=True,
                skiprows=8,
                )    
    df.index = pd.date_range(startDate, periods=len(df))
    df = df[['RFV', 'ET', 'Q', 'SSF', 'PRK', 'DPRK', 'RSSF', 'SW']]
    df['DP'] = df['RFV'] - df['ET'] - df['Q'] - df['SSF'] + df['PRK'] + df['DPRK']
    df['RSSF'] = df['RSSF'] + 0.001

    # FIXME: hard code
    df['GW'] = 208 + df['RFV']*0.5
    df['SWGW'] = 0 + df['RSSF']*0.3
    df['SW'] = (df['RFV']*0.2) + (df['RSSF']*0.3) + (df['GW']/40)
    # --------------------------------------------

    df.index = pd.date_range(startDate, periods=len(df))
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    if self.dlg.radioButton_std_month.isChecked():
        dfm = df.resample('M').mean()
        dff = dfm[ssdate:sedate]
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = df.resample('A').mean()
        dff = dfa[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    width = -20
    widthExg = float(self.dlg.doubleSpinBox_std_w_exag.value())
    # == Precipitation ============================================================
    axes[0].bar(
        dff.index, dff.RFV, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.1,
        color='slateblue')
    axes[0].set_ylim((dff.RFV.max() + dff.RFV.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_std_title.isChecked():
        if self.dlg.radioButton_std_month.isChecked():
            axes[0].set_title('Water Balance - Monthly Average [mm]', fontsize=12, fontweight='semibold')
        elif self.dlg.radioButton_std_year.isChecked():
            axes[0].set_title('Water Balance - Annual Average [mm]', fontsize=12, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=dff.RSSF + dff.SSF + dff.Q,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='lightgreen')
    axes[1].set_ylim(
        (dff.RSSF + dff.SSF + dff.Q).max(),
        (dff.RSSF + dff.SSF + dff.Q + dff.SW).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    # gwq -> Groundwater discharge to stream
    axes[2].bar(
        dff.index, dff.RSSF, width * widthExg,
        bottom=0,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='darkgreen')
    # latq -> lateral flow to stream
    axes[2].bar(
        dff.index, dff.SSF, width * widthExg,
        bottom=dff.RSSF,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='forestgreen')
    # surq -> surface runoff to stream
    axes[2].bar(
        dff.index, dff.Q, width * widthExg,
        bottom=dff.SSF + dff.RSSF,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='limegreen')
    # Soil water
    axes[2].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=dff.RSSF + dff.SSF + dff.Q,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='lightgreen')
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    # swgw -> seepage to aquifer
    axes[2].bar(
        dff.index, dff.SWGW*-1, width * widthExg,
        bottom = 0,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='b')
    # perco -> recharge to aquifer
    axes[2].bar(
        dff.index, dff.DP*-1, width * widthExg,
        bottom=dff.SWGW*-1,
        # bottom=0,        
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='dodgerblue')
    # gw -> groundwater volume
    axes[2].bar(
        dff.index, dff.GW*-1, width * widthExg,
        bottom=(dff.DP*-1) + (dff.SWGW*-1),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    axes[2].set_ylim(
        -1*(dff.SWGW + dff.DP).max(),
        (dff.RSSF + dff.SSF + dff.Q).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].bar(
        dff.index, dff.GW, width * widthExg,
        bottom=(dff.DP) + (dff.SWGW),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.GW + dff.DP + dff.SWGW).max()),
        ((dff.GW + dff.DP + dff.SWGW).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(
                Rectangle(
                    (0, 0), 0.1, 0.1, fc=c,
                    # ec = 'k',
                    alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            # ,handlelength = 3, handleheight = 1.5,
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            # labelspacing = 1.5,
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def plot_wb_m_mToA(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    startDate = stdate
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)):
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq='M')
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    if self.dlg.radioButton_std_month.isChecked():
        dff = data[ssdate:sedate]
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = data.resample('A').mean()
        dff = dfa[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    width = -20
    widthExg = float(self.dlg.doubleSpinBox_std_w_exag.value())
    # == Precipitation ============================================================
    axes[0].bar(
        dff.index, dff.RFV,
        width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.1,
        color='slateblue')
    axes[0].set_ylim((dff.RFV.max() + dff.RFV.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_std_title.isChecked():
        if self.dlg.radioButton_std_month.isChecked():
            axes[0].set_title('Water Balance - Monthly Total [mm]', fontsize=10, fontweight='semibold')
        elif self.dlg.radioButton_std_year.isChecked():
            axes[0].set_title('Water Balance - Annual Average Monthly Total [mm]', fontsize=10, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=dff.RSSF + dff.SSF + dff.Q,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='lightgreen')
    axes[1].set_ylim(
        (dff.RSSF + dff.SSF + dff.Q).max(),
        (dff.RSSF + dff.SSF + dff.Q + dff.SW).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    # gwq -> Groundwater discharge to stream
    axes[2].bar(
        dff.index, dff.RSSF, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='darkgreen')
    # latq -> lateral flow to stream
    axes[2].bar(
        dff.index, dff.SSF, width * widthExg,
        bottom=dff.RSSF,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='forestgreen')
    # surq -> surface runoff to stream
    axes[2].bar(
        dff.index, dff.Q, width * widthExg,
        bottom=dff.SSF + dff.RSSF,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='limegreen')
    # Soil water
    axes[2].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=dff.RSSF + dff.SSF + dff.Q,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='lightgreen')
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    # swgw -> seepage to aquifer
    axes[2].bar(
        dff.index, dff.SW*-1, width * widthExg,
        # bottom = df.latq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='b')
    # perco -> recharge to aquifer
    axes[2].bar(
        dff.index, dff.DP*-1, width * widthExg,
        bottom=dff.SW*-1,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='dodgerblue')
    # gw -> groundwater volume
    axes[2].bar(
        dff.index, dff.SW*-1, width * widthExg,
        bottom=(dff.DP*-1) + (dff.SW*-1),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    axes[2].set_ylim(
        -1*(dff.SW + dff.DP).max(),
        (dff.RSSF + dff.SSF + dff.Q).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=(dff.DP) + (dff.SW),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.SW + dff.DP + dff.SW).max()),
        ((dff.SW + dff.DP + dff.SW).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(
                Rectangle(
                    (0, 0), 0.1, 0.1, fc=c,
                    # ec = 'k',
                    alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            # ,handlelength = 3, handleheight = 1.5,
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            # labelspacing = 1.5,
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def plot_wb_year(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    dates = []
    bword = "HRU"
    for line in lines:
        try:
            date = line.split()[0]
            if (date == bword):  # Stop looping
                break
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq="A")
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    dff = data[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    width = -20
    widthExg = float(self.dlg.doubleSpinBox_std_w_exag.value())
    # == Precipitation ============================================================
    axes[0].bar(
        dff.index, dff.RFV, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.1,
        color='slateblue')
    axes[0].set_ylim((dff.RFV.max() + dff.RFV.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_std_title.isChecked():
        axes[0].set_title('Water Balance - Annual Total [mm]', fontsize=10, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=dff.RSSF + dff.SSF + dff.Q,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='lightgreen')
    axes[1].set_ylim(
        (dff.RSSF + dff.SSF + dff.Q).max(),
        (dff.RSSF + dff.SSF + dff.Q + dff.SW).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    # gwq -> Groundwater discharge to stream
    axes[2].bar(
        dff.index, dff.RSSF, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='darkgreen')
    # latq -> lateral flow to stream
    axes[2].bar(
        dff.index, dff.SSF, width * widthExg,
        bottom=dff.RSSF,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='forestgreen')
    # surq -> surface runoff to stream
    axes[2].bar(
        dff.index, dff.Q, width * widthExg,
        bottom=dff.SSF + dff.RSSF,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='limegreen')
    # Soil water
    axes[2].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=dff.RSSF + dff.SSF + dff.Q,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='lightgreen')
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    # swgw -> seepage to aquifer
    axes[2].bar(
        dff.index, dff.SW*-1, width * widthExg,
        # bottom = df.latq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='b')
    # perco -> recharge to aquifer
    axes[2].bar(
        dff.index, dff.DP*-1, width * widthExg,
        bottom=dff.SW*-1,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='dodgerblue')
    # gw -> groundwater volume
    axes[2].bar(
        dff.index, dff.SW*-1, width * widthExg,
        bottom=(dff.DP*-1) + (dff.SW*-1),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    axes[2].set_ylim(
        -1*(dff.SW + dff.DP).max(),
        (dff.RSSF + dff.SSF + dff.Q).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].bar(
        dff.index, dff.SW, width * widthExg,
        bottom=(dff.DP) + (dff.SW),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.SW + dff.DP + dff.SW).max()),
        ((dff.SW + dff.DP + dff.SW).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(
                Rectangle(
                    (0, 0), 0.1, 0.1, fc=c,
                    # ec = 'k',
                    alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            # ,handlelength = 3, handleheight = 1.5,
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            # labelspacing = 1.5,
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def export_wb_d(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']

    startDate = stdate.strftime("%m-%d-%Y")
    dws_file = self.dlg.comboBox_dws_files.currentText()
    df = pd.read_csv(
                os.path.join(wd, dws_file),
                delim_whitespace=True,
                skiprows=8,
                )    
    df.index = pd.date_range(startDate, periods=len(df))
    df = df[['RFV', 'ET', 'Q', 'SSF', 'PRK', 'DPRK', 'RSSF', 'SW']]
    df['DP'] = df['RFV'] - df['ET'] - df['Q'] - df['SSF'] + df['PRK'] + df['DPRK']
    df['RSSF'] = df['RSSF'] + 0.001

    # FIXME: hard code
    df['GW'] = 208 + df['RFV']*0.5
    df['SWGW'] = 0 + df['RSSF']*0.3
    df['SW'] = (df['RFV']*0.2) + (df['RSSF']*0.3) + (df['GW']/40)

    # --------------------------------------------
    df.index = pd.date_range(startDate, periods=len(df))
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    # Add info
    from datetime import datetime
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    if self.dlg.radioButton_std_day.isChecked():
        dff = df[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_daily.txt"), 'w') as f:
            f.write("# Daily water balance [mm] - APEXMOD Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', line_terminator='\n', encoding='utf-8')
        msgBox.setText("'wb_daily.txt' file is exported to your 'exported_files' folder!")
    elif self.dlg.radioButton_std_month.isChecked():
        dfm = df.resample('M').mean()
        dff = dfm[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_monthly_average.txt"), 'w') as f:
            f.write("# Monthly average water balance [mm] - APEXMOD Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', line_terminator='\n', encoding='utf-8')
        msgBox.setText("'wb_monthly_average.txt' file is exported to your 'exported_files' folder!")
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = df.resample('A').mean()
        dff = dfa[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_annual_average.txt"), 'w') as f:
            f.write("# Annual average water balance [mm] - APEXMOD Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', line_terminator='\n', encoding='utf-8')
        msgBox.setText("'wb_annual_average.txt' file is exported to your 'exported_files' folder!")
    msgBox.exec_()


def export_wb_m(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)):
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq='M')
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    # Add info
    from datetime import datetime
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    if self.dlg.radioButton_std_month.isChecked():
        dff = data[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_monthly_total.txt"), 'w') as f:
            f.write("# Monthly total water balance [mm] - APEXMOD Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', line_terminator='\n', encoding='utf-8')
        msgBox.setText("'wb_monthly_total.txt' file is exported to your 'exported_files' folder!")
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = data.resample('A').mean()
        dff = dfa[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_annual_avg_monthly_total.txt"), 'w') as f:
            f.write("# Annual average monthly total water balance [mm] - APEXMOD Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', line_terminator='\n', encoding='utf-8')
        msgBox.setText("'wb_annual_avg_monthly_total.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()

    
def export_wb_a(self):
    APEXMOD_path_dict = self.dirs_and_paths()
    stdate, eddate = self.define_sim_period()
    wd = APEXMOD_path_dict['apexmf_model']
    outfolder = APEXMOD_path_dict['exported_files']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    dates = []
    bword = "HRU"
    for line in lines:
        try:
            date = line.split()[0]
            if (date == bword):  # Stop looping
                break
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq="A")
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    dff = data[ssdate:sedate]
    # Add info
    from datetime import datetime
    version = "version 1.0."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    with open(os.path.join(outfolder, "wb_annual_total.txt"), 'w') as f:
        f.write("# Annual total water balance [mm] - APEXMOD Plugin " + version + time + "\n")
        dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', line_terminator='\n', encoding='utf-8')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/APEXMOD/pics/am_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("'wb_annual_total.txt' file is exported to your 'exported_files' folder!")
    msgBox.exec_()
