# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg, NavigationToolbar2QT
import pickle
import numpy as np
import re




class ManualAmpUI(QtGui.QFrame):
    KeyPressed = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(ManualAmpUI, self).__init__()
        self.setWindowTitle("bh_thomoPy/Manual Traveltime Picking")
        self.openmain = OpenMainData(self)
        self.mogs = []
        self.air = []
        self.boreholes = []
        self.models = []
        self.filename = ''
        self.mog = 0
        self.initUI()

        #self.upperFig.UpperTracePickedSignal.connect(self.lowerFig.plot_trace_data)
        self.upperFig.UpperTracePickedSignal.connect(self.update_control_center)
        self.lowerFig.LowerTracePickedSignal.connect(self.upperFig.plot_amplitude)
        self.lowerFig.LowerTracePickedSignal.connect(self.update_control_center)



    def next_trace(self):
        n = int(self.Tnum_Edit.text())
        n += 1

        self.Tnum_Edit.setText(str(n))
        self.update_control_center()

    def prev_trace(self):
        n = int(self.Tnum_Edit.text())
        n -= 1
        self.Tnum_Edit.setText(str(n))
        self.update_control_center()

    def update_control_center(self):
        n = int(self.Tnum_Edit.text())-1

        ind = self.openmain.mog_combo.currentIndex()
        self.mog = self.mogs[ind]

        if len(self.mogs) == 0:
            return
        else:
            self.xRx_label.setText(str(self.mog.data.Rx_x[n]))
            self.xTx_label.setText(str(self.mog.data.Tx_x[n]))
            self.yRx_label.setText(str(self.mog.data.Rx_y[n]))
            self.yTx_label.setText(str(self.mog.data.Tx_y[n]))
            self.zRx_label.setText(str(np.round(self.mog.data.Rx_z[n], 3)))
            self.zTx_label.setText(str(self.mog.data.Tx_z[n]))
            self.ntrace_label.setText(str(self.mog.data.ntrace))

        self.upperFig.plot_amplitude()

    def update_settings_edits(self):
        self.value_tmin_edit.setText(str(np.round(self.mog.data.timestp[0], 4)))
        self.value_tmax_edit.setText(str(np.round(self.mog.data.timestp[-1], 4)))
        self.value_z_surf_edit.setText(str(self.mog.Rx.fdata[0, 2]))
        self.num_tx_freq_edit.setText(str(self.mog.data.rnomfreq))

    def reinit_trace(self):
        n = int(self.Tnum_Edit.text()) - 1

        self.mog.amp_done[n] = 0
        self.mog.amp_tmin[n] = -1.0
        self.mog.amp_tmin[n] = -1.0

        self.update_control_center()

    def next_trace_to_pick(self):
        ind = np.where(self.mog.amp_done == 0)[0]
        to_pick = ind[0] + 1
        self.Tnum_Edit.setText(str(to_pick))
        self.update_control_center()

    def intermediate_saves(self):
        if float(self.Tnum_Edit.text()) % 50 == 0:
            save_file = open(self.filename, 'wb')
            pickle.dump((self.boreholes, self.mogs, self.air, self.models), save_file)
            print('saved')

    def reinit_tnum(self):
        self.Tnum_Edit.setText('1')

    def plot_stats(self):
        ind = self.openmain.mog_combo.currentIndex()
        mog = self.mogs[ind]
        self.statsFig1 = StatsFig1()
        self.statsFig1.plot_stats(mog, self.air)
        self.statsFig1.showMaximized()

    def savefile(self):
        save_file = open(self.filename, 'wb')
        pickle.dump((self.boreholes, self.mogs, self.air, self.models), save_file)
        dialog = QtGui.QMessageBox.information(self, 'Success', "Database was saved successfully"
                                                ,buttons=QtGui.QMessageBox.Ok)

    def import_tt_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Import')
        self.load_tt_file(filename)
    def load_tt_file(self, filename):
        try:
            file = open(filename, 'r')
        except:
            try:
                file = open(filename + ".dat", 'r')
            except:
                try:
                    file = open(filename + ".DAT", 'r')
                except:
                    dialog = QtGui.QMessageBox.warning(self, 'Warning', "Could not import {} file".format(filename),buttons= QtGui.QMessageBox.Ok)

        info_tt = np.loadtxt(filename)
        for row in info_tt:
            trc_number = int(float(row[0]))
            tt = float(row[1])
            et = float(row[2])
            self.mog.tt_done[trc_number - 1] = 1
            self.mog.tt[trc_number - 1] = tt
            self.mog.et[trc_number - 1] = et


        self.update_control_center()


    def initUI(self):
        blue_palette = QtGui.QPalette()
        blue_palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.darkCyan)

        #------ Creation of the Manager for the Upper figure -------#
        self.upperFig = UpperFig(self)
        self.uppertool = NavigationToolbar2QT(self.upperFig, self)
        self.uppermanager = QtGui.QWidget()
        uppermanagergrid = QtGui.QGridLayout()
        uppermanagergrid.addWidget(self.uppertool, 0, 0)
        uppermanagergrid.addWidget(self.upperFig, 1, 0)
        uppermanagergrid.setContentsMargins(0, 0, 0, 0)
        uppermanagergrid.setVerticalSpacing(3)
        self.uppermanager.setLayout(uppermanagergrid)

        #------ Creation of the Manager for the Lower figure -------#
        self.lowerFig = LowerFig(self)
        self.lowermanager = QtGui.QWidget()
        lowermanagergrid = QtGui.QGridLayout()
        lowermanagergrid.addWidget(self.lowerFig, 0, 0)
        self.lowermanager.setLayout(lowermanagergrid)

        #------- Widgets Creation -------#
        #--- Buttons ---#
        btn_load = QtGui.QPushButton("Load Curved Rays")
        btn_Prev = QtGui.QPushButton("Previous Trace")
        btn_Next = QtGui.QPushButton("Next Trace")
        btn_Next_Pick = QtGui.QPushButton("Next Trace to Pick")
        btn_Reini = QtGui.QPushButton("Reinitialize Trace")
        btn_Upper = QtGui.QPushButton("Activate Picking")
        btn_Stats = QtGui.QPushButton("Statistics")
        btn_fit = QtGui.QPushButton("Fit Spectra")

        #- Buttons' Actions -#
        btn_Next.clicked.connect(self.next_trace)
        btn_Prev.clicked.connect(self.prev_trace)
        btn_Upper.clicked.connect(self.upper_trace_isClicked)
        btn_Stats.clicked.connect(self.plot_stats)
        btn_Reini.clicked.connect(self.reinit_trace)
        btn_Next_Pick.clicked.connect(self.next_trace_to_pick)

        #--- Label ---#
        trc_Label                       = MyQLabel("Trace number :", ha= 'right')
        t_min_label                     = MyQLabel("t min", ha= 'right')
        t_max_label                     = MyQLabel("t max", ha= 'right')
        ang_min_label                   = MyQLabel("Minimum angle", ha= 'right')
        z_surf_label                    = MyQLabel("Z surface", ha= 'right')
        position_label                  = MyQLabel(("Position Tx--Rx"), ha='center')
        x_label                         = MyQLabel("x", ha= 'center')
        y_label                         = MyQLabel("y", ha= 'center')
        z_label                         = MyQLabel("z", ha= 'center')
        Tx_label                        = MyQLabel("Tx:", ha= 'right')
        Rx_label                        = MyQLabel("Rx:", ha= 'right')
        centroid_freq_label             = MyQLabel('Centroid freq.: ', ha= 'right')
        centroid_var_label              = MyQLabel('Var. Centroid: ', ha= 'right')
        freq1_label                     = MyQLabel('MHz', ha= 'center')
        freq2_label                     = MyQLabel('MHz', ha= 'center')
        trace_label                     = MyQLabel("traces", ha= 'center')

        tx_freq_label                   = MyQLabel("Tx Frequency [MHz]", ha='right')
        f_min_label                     = MyQLabel("Min F centroid", ha='right')
        f_max_label                     = MyQLabel("Max F centroid", ha='right')
        auto_pick_label                 = MyQLabel("Window - Auto pick", ha= 'right')

        self.num_freq1_label            = MyQLabel('0', ha= 'center')
        self.num_freq2_label            = MyQLabel('0', ha= 'center')
        self.xTx_label                  = MyQLabel("", ha= 'center')
        self.yTx_label                  = MyQLabel("", ha= 'center')
        self.zTx_label                  = MyQLabel("", ha= 'center')
        self.xRx_label                  = MyQLabel("", ha= 'center')
        self.yRx_label                  = MyQLabel("", ha= 'center')
        self.zRx_label                  = MyQLabel("", ha= 'center')
        self.ntrace_label               = MyQLabel("", ha= 'center')




        #--- Edits ---#
        self.Tnum_Edit = QtGui.QLineEdit('1')
        self.num_tx_freq_edit = QtGui.QLineEdit()
        self.value_f_min_edit = QtGui.QLineEdit('1')
        self.value_f_max_edit = QtGui.QLineEdit('175')
        self.value_window_edit = QtGui.QLineEdit('30')
        self.value_tmin_edit = QtGui.QLineEdit()
        self.value_tmax_edit = QtGui.QLineEdit()
        self.value_ang_min_edit = QtGui.QLineEdit('45')
        self.value_z_surf_edit = QtGui.QLineEdit()

        #- Edits' Disposition -#
        self.Tnum_Edit.setAlignment(QtCore.Qt.AlignCenter)
        self.num_tx_freq_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_f_min_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_f_max_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_window_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_tmin_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_tmax_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_ang_min_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.value_z_surf_edit.setAlignment(QtCore.Qt.AlignCenter)

        #- Edits' Disposition -#
        self.Tnum_Edit.setFixedWidth(100)
        self.Tnum_Edit.setAlignment(QtCore.Qt.AlignHCenter)

        #- Edits' Actions -#
        self.Tnum_Edit.editingFinished.connect(self.update_control_center)


        #--- Actions ---#
        openAction = QtGui.QAction('Open main data file', self)
        openAction.triggered.connect(self.openmain.show)

        saveAction = QtGui.QAction('Save', self)
        saveAction.triggered.connect(self.savefile)

        importAction = QtGui.QAction('Import ...', self)
        importAction.triggered.connect(self.import_tt_file)



        #--- ToolBar ---#
        self.tool = QtGui.QMenuBar()

        fileMenu = self.tool.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(importAction)


        optionMenu = self.tool.addMenu('&Options')
        radiationMenu = optionMenu.addMenu('&Radiation Pattern')
        centroidMenu = optionMenu.addMenu('&Centroid f (S transf.)')
        hybridMenu = optionMenu.addMenu('&Hybrid data')
        spectrumMenu = optionMenu.addMenu('&Spectrum fitting')
        unitsMenu = optionMenu.addMenu('&Units of frequency')

        sinAction = QtGui.QAction('&Sin (theta)', self)
        sin2Action = QtGui.QAction('&Sin2 (theta)', self)

        showspectrumAction = QtGui.QAction('&Show frequency spectrum', self)
        showspectrumtimeAction = QtGui.QAction('&Show time - frequency spectrum', self)

        firstcycleAction = QtGui.QAction('&Evaluate at start of 1st cycle', self)
        firsthalfcycleAction = QtGui.QAction('&Evaluate at 1st half-cycle peak', self)
        maxenergyAction = QtGui.QAction('&Evaluate at maximum of energy', self)
        maxenergyAction = QtGui.QAction('&Evaluate at maximum of amplitude', self)

        #sinAction.setCheckable(True)
        #sin2Action.setCheckable(True)

        #sinAction.setChecked(True)

        #radiationMenu.addAction(sinAction)
        #radiationMenu.addAction(sin2Action)

        radiationActionGroup = QtGui.QActionGroup(self)
        radiationActionGroup.addAction(sinAction)
        radiationActionGroup.addAction(sin2Action)

        #radiationMenu.addAction(radiationActionGroup)



        #--- Checkboxes ---#
        self.weight_check = QtGui.QCheckBox('Weighting 1/(S/N)')
        self.process_check = QtGui.QCheckBox("Process picked tt traces")
        self.Wave_check = QtGui.QCheckBox("Wavelet tranf. denoising")
        self.ap_win_check = QtGui.QCheckBox("Use AP Window")
        self.hybrid_check = QtGui.QCheckBox("Genrerate hybrid Data")


        #--- Text Edits ---#
        info_Tedit = QtGui.QTextEdit()
        info_Tedit.setReadOnly(True)

        #--- ComboBox ---#
        self.option_combo = QtGui.QComboBox()

        #- ComboBox Items -#
        items = ['Centroid freq. (fft)', 'Centroid freq. (S-transform)', 'Peak-to-peak amplutide', 'Maximum absolute amplitude' ]
        self.option_combo.addItems(items)


        #------- subWidgets -------#
        #--- freq1 subwidget ---#
        sub_freq1_widget = QtGui.QWidget()
        sub_freq1_grid = QtGui.QGridLayout()
        sub_freq1_grid.addWidget(self.num_freq1_label, 0, 0)
        sub_freq1_grid.addWidget(freq1_label, 0, 1)
        sub_freq1_grid.setContentsMargins(0, 0, 0, 0)
        sub_freq1_widget.setLayout(sub_freq1_grid)

        #--- freq2 subwidget ---#
        sub_freq2_widget = QtGui.QWidget()
        sub_freq2_grid = QtGui.QGridLayout()
        sub_freq2_grid.addWidget(self.num_freq2_label, 0, 0)
        sub_freq2_grid.addWidget(freq2_label, 0, 1)
        sub_freq2_grid.setContentsMargins(0, 0, 0, 0)
        sub_freq2_widget.setLayout(sub_freq2_grid)

        #--- Trace Subwidget ---#
        Sub_Trace_Widget = QtGui.QWidget()
        Sub_Trace_Grid = QtGui.QGridLayout()
        Sub_Trace_Grid.addWidget(trc_Label, 0, 0)
        Sub_Trace_Grid.addWidget(self.Tnum_Edit, 0, 1)
        Sub_Trace_Grid.setContentsMargins(0, 0, 0, 0)
        Sub_Trace_Grid.setAlignment(QtCore.Qt.AlignCenter)
        Sub_Trace_Widget.setLayout(Sub_Trace_Grid)

        #--- Info Subwidget ---#
        Sub_Info_widget = QtGui.QWidget()
        Sub_Info_grid = QtGui.QGridLayout()
        Sub_Info_grid.addWidget(position_label, 0, 1, 1, 3)
        Sub_Info_grid.addWidget(x_label, 2, 1)
        Sub_Info_grid.addWidget(y_label, 2, 2)
        Sub_Info_grid.addWidget(z_label, 2, 3)
        Sub_Info_grid.addWidget(Tx_label, 3, 0)
        Sub_Info_grid.addWidget(self.xTx_label, 3, 1)
        Sub_Info_grid.addWidget(self.yTx_label, 3, 2)
        Sub_Info_grid.addWidget(self.zTx_label, 3, 3)
        Sub_Info_grid.addWidget(Rx_label, 4, 0)
        Sub_Info_grid.addWidget(self.xRx_label, 4, 1)
        Sub_Info_grid.addWidget(self.yRx_label, 4, 2)
        Sub_Info_grid.addWidget(self.zRx_label, 4, 3)
        Sub_Info_grid.addWidget(self.ntrace_label, 5, 1)
        Sub_Info_grid.addWidget(trace_label, 5, 2)
        Sub_Info_grid.addWidget(centroid_freq_label, 8, 0)
        Sub_Info_grid.addWidget(sub_freq1_widget, 8, 1)
        Sub_Info_grid.addWidget(centroid_var_label, 9, 0)
        Sub_Info_grid.addWidget(sub_freq2_widget, 9, 1)
        Sub_Info_widget.setLayout(Sub_Info_grid)
        Sub_Info_widget.setStyleSheet("background: white")

        #--- Buttons SubWidget ---#
        sub_button_widget = QtGui.QWidget()
        sub_button_grid = QtGui.QGridLayout()
        sub_button_grid.addWidget(btn_load, 1, 0, 1, 4)
        sub_button_grid.addWidget(btn_Upper, 2, 0, 1, 4)
        sub_button_grid.addWidget(Sub_Trace_Widget, 3, 1, 1, 2)
        sub_button_grid.addWidget(btn_Prev, 4, 0, 1, 2)
        sub_button_grid.addWidget(btn_Next, 4, 2, 1, 2)
        sub_button_grid.addWidget(btn_Next_Pick, 5, 0, 1, 4)
        sub_button_grid.addWidget(btn_Reini, 6, 0, 1, 4)
        sub_button_grid.addWidget(btn_Stats, 7, 0, 1, 4)
        sub_button_grid.addWidget(btn_fit, 8, 0, 1, 4)
        sub_button_widget.setLayout(sub_button_grid)

        #--- Info Groupbox ---#
        info_group = QtGui.QGroupBox('Infos')
        info_grid = QtGui.QGridLayout()
        info_grid.addWidget(Sub_Info_widget)
        info_group.setLayout(info_grid)

        #--- Settings GroupBox ---#
        settings_group = QtGui.QGroupBox('Settings')
        sub_settings_grid = QtGui.QGridLayout()
        sub_settings_grid.addWidget(self.hybrid_check, 0, 0)
        sub_settings_grid.addWidget(self.option_combo, 0, 1)
        sub_settings_grid.addWidget(self.weight_check, 1, 0)
        sub_settings_grid.addWidget(self.process_check, 2, 0)
        sub_settings_grid.addWidget(self.ap_win_check, 3, 0)
        sub_settings_grid.addWidget(self.Wave_check, 4, 0)
        sub_settings_grid.addWidget(self.num_tx_freq_edit, 1, 2)
        sub_settings_grid.addWidget(self.value_f_min_edit, 2, 2)
        sub_settings_grid.addWidget(self.value_f_max_edit, 3, 2)
        sub_settings_grid.addWidget(self.value_window_edit, 4, 2)
        sub_settings_grid.addWidget(tx_freq_label, 1, 1)
        sub_settings_grid.addWidget(f_min_label, 2, 1)
        sub_settings_grid.addWidget(f_max_label, 3, 1)
        sub_settings_grid.addWidget(auto_pick_label, 4, 1)
        sub_settings_grid.addWidget(self.value_tmin_edit, 1, 4)
        sub_settings_grid.addWidget(self.value_tmax_edit, 2, 4)
        sub_settings_grid.addWidget(self.value_ang_min_edit, 3, 4)
        sub_settings_grid.addWidget(self.value_z_surf_edit, 4, 4)
        sub_settings_grid.addWidget(t_min_label, 1, 3)
        sub_settings_grid.addWidget(t_max_label, 2, 3)
        sub_settings_grid.addWidget(ang_min_label, 3, 3)
        sub_settings_grid.addWidget(z_surf_label, 4, 3)
        settings_group.setLayout(sub_settings_grid)




        #--- Control Center SubWidget ---#
        Control_Center_GroupBox = QtGui.QGroupBox("Control Center")
        Control_Center_Grid = QtGui.QGridLayout()
        Control_Center_Grid.addWidget(info_group, 0, 0)
        Control_Center_Grid.addWidget(settings_group, 1, 0, 1, 2)
        Control_Center_Grid.addWidget(sub_button_widget, 0, 1)
        Control_Center_GroupBox.setLayout(Control_Center_Grid)


        #--- Master Grid Disposition ---#
        master_grid = QtGui.QGridLayout()
        master_grid.addWidget(self.tool, 0, 0, 1, 3)
        master_grid.addWidget(self.uppermanager, 1, 0, 1, 3)
        master_grid.addWidget(self.lowermanager, 2, 0, 1, 2)
        master_grid.addWidget(Control_Center_GroupBox, 2, 2)
        master_grid.setRowStretch(1, 100)
        master_grid.setColumnStretch(1, 100)
        master_grid.setContentsMargins(0, 0, 0, 0)
        master_grid.setVerticalSpacing(0)
        self.setLayout(master_grid)

    def upper_trace_isClicked(self):
        if self.sender().isFlat():
            self.sender().setFlat(False)
            self.upperFig.isTracingOn = False
        else:
            self.sender().setFlat(True)
            self.upperFig.isTracingOn = True

    def lower_trace_isClicked(self):
        if self.sender().isFlat():
            self.sender().setFlat(False)
            self.lowerFig.isTracingOn = False
        else:
            self.sender().setFlat(True)
            self.lowerFig.isTracingOn = True

class OpenMainData(QtGui.QWidget):
    def __init__(self, tt, parent=None):
        super(OpenMainData, self).__init__()
        self.setWindowTitle("Choose Data")
        self.database_list = []
        self.tt = tt
        self.initUI()

    def openfile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open Database')

        self.load_file(filename)

    def load_file(self, filename):
        self.tt.filename = filename
        rname = filename.split('/')
        rname = rname[-1]
        if '.p' in rname:
            rname = rname[:-2]
        if '.pkl' in rname:
            rname = rname[:-4]
        if '.pickle' in rname:
            rname = rname[:-7]
        file = open(filename, 'rb')

        self.tt.boreholes, self.tt.mogs, self.tt.air, self.tt.models = pickle.load(file)

        self.database_edit.setText(rname)
        for mog in self.tt.mogs:

            self.mog_combo.addItem(mog.name)


    def cancel(self):
        self.close()

    def ok(self):
        self.tt.update_control_center()
        self.tt.update_settings_edits()
        self.tt.upperFig.plot_amplitude()

        self.close()

    def initUI(self):

        #-------  Widgets --------#
        #--- Edit ---#
        self.database_edit = QtGui.QLineEdit()
        #- Edit Action -#
        self.database_edit.setReadOnly(True)
        #--- Buttons ---#
        self.btn_database = QtGui.QPushButton('Choose Database')
        self.btn_ok = QtGui.QPushButton('Ok')
        self.btn_cancel = QtGui.QPushButton('Cancel')

        #- Buttons' Actions -#
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_database.clicked.connect(self.openfile)
        self.btn_ok.clicked.connect(self.ok)

        #--- Combobox ---#
        self.mog_combo = QtGui.QComboBox()

        #- Combobox's Action -#
        self.mog_combo.activated.connect(self.tt.update_control_center)

        master_grid = QtGui.QGridLayout()
        master_grid.addWidget(self.database_edit, 0, 0, 1, 2)
        master_grid.addWidget(self.btn_database, 1, 0, 1, 2)
        master_grid.addWidget(self.mog_combo, 2, 0, 1, 2)
        master_grid.addWidget(self.btn_ok, 3, 0)
        master_grid.addWidget(self.btn_cancel, 3 ,1)
        self.setLayout(master_grid)


class UpperFig(FigureCanvasQTAgg):

    UpperTracePickedSignal = QtCore.pyqtSignal(bool)

    def __init__(self, tt):
        fig_width, fig_height = 4, 4
        fig = mpl.figure.Figure(figsize=(fig_width, fig_height), facecolor= 'white')
        super(UpperFig, self).__init__(fig)
        self.initFig()
        self.trc_number = 0
        self.tt = tt
        self.mpl_connect('button_press_event', self.onclick)
        #self.mpl_connect('key_press_event', self.press)
        self.isTracingOn = False


    def initFig(self):
        self.ax = self.figure.add_axes([0.05, 0.13, 0.935, 0.85])


        self.ax.yaxis.set_ticks_position('left')
        self.ax.xaxis.set_ticks_position('bottom')
        self.ax.set_ylabel('Amplitude')

        self.trace,  = self.ax.plot([],
                                    [],
                                    color='b')

        self.pick_amp_tmin  = self.ax.axvline(-100,
                                        ymin=0,
                                        ymax=1,
                                        color='g')

        self.pick_amp_tmax  = self.ax.axvline(-100,
                                        ymin=0,
                                        ymax=1,
                                        color='g')

    def plot_amplitude(self):

        n = int(self.tt.Tnum_Edit.text())

        self.trc_number = n-1

        trace = self.tt.mog.data.rdata[:, self.trc_number]

        self.ax.set_xlim(self.tt.mog.data.timestp[0], self.tt.mog.data.timestp[-1])
        self.ax.set_ylim(min(trace.flatten()), max(trace.flatten()))

        self.pick_amp_tmin.set_xdata(self.tt.mog.amp_tmin[self.trc_number])
        self.pick_amp_tmax.set_xdata(self.tt.mog.amp_tmax[self.trc_number])

        self.trace.set_ydata(trace)
        self.trace.set_xdata(self.tt.mog.data.timestp)
        self.draw()


    def onclick(self, event):

        if self.isTracingOn is False:
            return

        self.x, self.y = event.x, event.y

        if event.button == 1:

            if self.x != None and self.y != None:

                self.tt.mog.amp_tmin[self.trc_number] = event.xdata

                self.tt.update_control_center()
                self.UpperTracePickedSignal.emit(True)

        elif event.button == 2:

            self.tt.next_trace()

        elif event.button == 3:

            if self.x != None and self.y != None:

                self.tt.mog.amp_tmax[self.trc_number] = event.xdata

                self.tt.update_control_center()
                self.UpperTracePickedSignal.emit(True)



        self.draw()


class LowerFig(FigureCanvasQTAgg):
    LowerTracePickedSignal = QtCore.pyqtSignal(bool)
    def __init__(self, tt):
        fig_width, fig_height = 4, 4
        fig = mpl.figure.Figure(figsize=(fig_width, fig_height), facecolor= 'white')
        super(LowerFig, self).__init__(fig)
        self.initFig()
        self.tt = tt
        self.mpl_connect('button_press_event', self.onclick)
        self.isTracingOn = False

    def initFig(self):
        self.ax = self.figure.add_axes([0.07, 0.05, 0.9, 0.85])
        self.ax.yaxis.set_ticks_position('left')
        self.ax.xaxis.set_ticks_position('bottom')




    def onclick(self, event):
        if self.isTracingOn is False:
            return

        self.x, self.y = event.x, event.y

        if event.button == 1:
            if self.x != None and self.y != None:

                y_lim = self.ax.get_ylim()
                x_lim = self.ax.get_xlim()

                if self.tt.tt_picking_radio.isChecked():

                    if self.tt.main_data_radio.isChecked():
                        print('Traveltime being picked')
                        self.tt.mog.tt[self.trc_number] = event.ydata
                        self.tt.mog.tt_done[self.trc_number] = 1
                        self.picked_tt_circle.set_ydata(self.tt.mog.tt[self.trc_number])
                    elif self.tt.t0_before_radio.isChecked():
                        print('t0_before being picked')
                        self.tt.air[self.tt.mog.av].tt[self.trc_number] = event.ydata
                        self.tt.air[self.tt.mog.av].tt_done[self.trc_number] = 1
                        self.picked_tt_circle.set_ydata(self.tt.air[self.tt.mog.av].tt[self.trc_number])

                    elif self.tt.t0_after_radio.isChecked():
                        self.tt.air[self.tt.mog.ap].tt[self.trc_number] = event.ydata
                        self.tt.air[self.tt.mog.ap].tt_done[self.trc_number] = 1
                        self.picked_tt_circle.set_ydata(self.tt.air[self.tt.mog.av].tt[self.trc_number])

                elif self.tt.trace_selec_radio.isChecked():

                    idx = np.argmin((np.abs(np.arange(self.tt.mog.data.ntrace) - event.xdata)))
                    self.tt.Tnum_Edit.setText(str(idx + 1))
                    self.tt.update_control_center()

                self.ax.set_ylim(y_lim[0], y_lim[-1])
                self.LowerTracePickedSignal.emit(True)

        elif event.button == 2:
            if self.tt.jump_checkbox.isChecked():

                self.tt.next_trace_to_pick()
            else:
                self.tt.next_trace()


        elif event.button == 3:
            if self.x != None and self.y != None:

                if self.tt.main_data_radio.isChecked():
                    self.tt.mog.et[self.trc_number] =  np.abs(self.tt.mog.tt[self.trc_number] -event.ydata)
                elif self.tt.t0_before_radio.isChecked():
                    self.tt.air[self.tt.mog.av].et[self.trc_number] = np.abs(self.tt.air[self.tt.mog.av].tt[self.trc_number] -event.ydata)
                elif self.tt.t0_after_radio.isChecked():
                    self.tt.air[self.tt.mog.ap].et[self.trc_number] = np.abs(self.tt.air[self.tt.mog.ap].tt[self.trc_number] -event.ydata)

                self.LowerTracePickedSignal.emit(True)


        self.draw()


class StatsFig1(FigureCanvasQTAgg):
    def __init__(self, parent = None):

        fig = mpl.figure.Figure(figsize= (100, 100), facecolor='white')
        super(StatsFig1, self).__init__(fig)
        self.initFig()

    def initFig(self):


        self.ax1 = self.figure.add_axes([0.1, 0.1, 0.2, 0.25])
        self.ax2 = self.figure.add_axes([0.4, 0.1, 0.2, 0.25])
        self.ax3 = self.figure.add_axes([0.7, 0.1, 0.2, 0.25])
        self.ax4 = self.figure.add_axes([0.1, 0.55, 0.2, 0.25])
        self.ax5 = self.figure.add_axes([0.4, 0.55, 0.2, 0.25])
        self.ax6 = self.figure.add_axes([0.7, 0.55, 0.2, 0.25])

    def plot_stats(self, mog, airshots):

        done = (mog.tt_done + mog.in_vect.astype(int)) - 1
        ind = np.nonzero(done == 1)[0]
        print(ind)

        tt, t0 = mog.getCorrectedTravelTimes(airshots)
        print(tt)
        et = mog.et[ind]
        tt = tt[ind]


        hyp = np.sqrt((mog.data.Tx_x[ind]-mog.data.Rx_x[ind])**2
                      + (mog.data.Tx_y[ind] - mog.data.Rx_y[ind] )**2
                      + (mog.data.Tx_z[ind] -  mog.data.Rx_z[ind] )**2)
        dz = mog.data.Rx_z[ind] - mog.data.Tx_z[ind]

        theta = 180/ np.pi * np.arcsin(dz/hyp)

        vapp = hyp/(tt-t0[ind])

        #n = np.arange(len(ind)-1)
        #n = n[ind]
        ind2 = np.less(vapp, 0)
        ind2 = np.nonzero(ind2)[0]

        self.ax4.plot(hyp, tt, marker='o', ls= 'None')
        self.ax5.plot(theta, hyp/tt, marker='o', ls= 'None')
        self.ax2.plot(theta, vapp, marker='o', ls= 'None')
        self.ax6.plot(t0)
        self.ax1.plot(hyp, et, marker='o', ls= 'None')
        self.ax3.plot(theta, et, marker='o', ls= 'None')





        self.figure.suptitle('{}'.format(mog.name), fontsize=20)
        mpl.axes.Axes.set_ylabel(self.ax4, ' Time [{}]'.format(mog.data.tunits))
        mpl.axes.Axes.set_xlabel(self.ax4, 'Straight Ray Length[{}]'.format(mog.data.cunits))

        mpl.axes.Axes.set_ylabel(self.ax1, 'Standard Deviation')
        mpl.axes.Axes.set_xlabel(self.ax1, 'Straight Ray Length[{}]'.format(mog.data.cunits))

        mpl.axes.Axes.set_ylabel(self.ax5, 'Apparent Velocity [{}/{}]'.format(mog.data.cunits, mog.data.tunits))
        mpl.axes.Axes.set_xlabel(self.ax5, 'Angle w/r to horizontal[°]')
        mpl.axes.Axes.set_title(self.ax5, 'Velocity before correction')

        mpl.axes.Axes.set_ylabel(self.ax2, 'Apparent Velocity [{}/{}]'.format(mog.data.cunits, mog.data.tunits))
        mpl.axes.Axes.set_xlabel(self.ax2, 'Angle w/r to horizontal[°]')
        mpl.axes.Axes.set_title(self.ax2, 'Velocity after correction')

        mpl.axes.Axes.set_ylabel(self.ax6, ' Time [{}]'.format(mog.data.tunits))
        mpl.axes.Axes.set_xlabel(self.ax6, 'Shot Number')
        mpl.axes.Axes.set_title(self.ax6, '$t_0$ drift in air')

        mpl.axes.Axes.set_ylabel(self.ax3, 'Standard Deviation')
        mpl.axes.Axes.set_xlabel(self.ax3, 'Angle w/r to horizontal[°]')



#--- Class For Alignment ---#
class  MyQLabel(QtGui.QLabel):
    def __init__(self, label, ha='left',  parent=None):
        super(MyQLabel, self).__init__(label,parent)
        if ha == 'center':
            self.setAlignment(QtCore.Qt.AlignCenter)
        elif ha == 'right':
            self.setAlignment(QtCore.Qt.AlignRight)
        else:
            self.setAlignment(QtCore.Qt.AlignLeft)


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    manual_ui = ManualAmpUI()
    manual_ui.openmain.load_file('save test.p')
    manual_ui.update_control_center()
    manual_ui.update_settings_edits()
    manual_ui.showMaximized()
    #manual_ui.load_tt_file('C:\\Users\\Utilisateur\\Documents\\MATLAB\\t0302tt')

    sys.exit(app.exec_())