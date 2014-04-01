#!/usr/bin/python
#view data version 2.0

import wx
from configobj import ConfigObj

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import numpy
import copy

import qrange

from fitlibrary import *

latest_data_sets_dir = '/home/xinxing/Programs/viewdata2.0/latest_data_sets.INI'
data_dir = '/home/xinxing/Programs/data'
setting_dir = '/home/xinxing/Programs/viewdata2.0/setting.INI'

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size = (1300, 600))
        self.saved_settings = ConfigObj(setting_dir)
        data_dir = self.saved_settings['DIR']['data_dir']
#        del self.saved_settings['DIR']

        self.mainpanel = wx.Panel(self, size =(1300, 600))
        
        self.plotpanel = PlotPanel(self.mainpanel)
#        self.plotpanel.SetBackgroundColour('blue')
        self.controlpanel = ControlPanel(self.mainpanel)
        self.controlpanel.SetBackgroundColour('grey')
       
        self.replot = wx.Button(self.mainpanel, label = 'replot')
        self.Bind(wx.EVT_BUTTON, self.evt_press_replot, self.replot)
        
        self.vSizer = wx.BoxSizer(wx.VERTICAL)
        self.vSizer.Add(self.replot, 0, wx.EXPAND | wx.ALL, 5)
        self.vSizer.Add(self.controlpanel, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.plotpanel, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(self.vSizer, 0, wx.EXPAND | wx.ALL, 5)
        self.mainpanel.SetSizerAndFit(mainSizer)

        menuBar = wx.MenuBar()
        filemenu = wx.Menu()
        load_setting = filemenu.Append(wx.ID_OPEN, "&Load setting", "Load previous setting")
        self.Bind(wx.EVT_MENU, self.on_load, load_setting)
        
        save_setting = filemenu.Append(wx.ID_SAVE, "&Save setting", "Save currnet setting as new")
        self.Bind(wx.EVT_MENU, self.on_save, save_setting)
        
        save_setting_as = filemenu.Append(wx.ID_SAVEAS, "&Override setting as", "Save currnet setting as")
        self.Bind(wx.EVT_MENU, self.on_save_as, save_setting_as)
        
        save_data_as = filemenu.Append(wx.NewId(), "&Save data setup as", "Save currnet data setup as")
        self.Bind(wx.EVT_MENU, self.on_save_data_as, save_data_as)
        
        delete_data = filemenu.Append(wx.NewId(), "&Delete data setup", "Delete data setup")
        self.Bind(wx.EVT_MENU, self.on_delete_data_setup, delete_data)
        
        filemenu.AppendSeparator()
        exit = filemenu.Append(wx.ID_EXIT, "&Exit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.on_exit, exit)

        menuBar.Append(filemenu, "&File")
        
        set_menu = wx.Menu()
        set_data_dir = set_menu.Append(wx.NewId(), "Data folder", "Set data folder")
        self.Bind(wx.EVT_MENU, self.on_data_dir, set_data_dir)

        menuBar.Append(set_menu, "&Set")

        help_menu = wx.Menu()
        about = help_menu.Append(wx.ID_ABOUT, "About", "About")
        self. Bind(wx.EVT_MENU, self.on_about, about)

        menuBar.Append(help_menu, "Help")
        self.SetMenuBar(menuBar)
        
        self.Center()
        self.Show(True)
    
    def on_load(self, event):
        choice = self.saved_settings.keys()
        choice.remove('DIR')
        dlg = wx.SingleChoiceDialog(self, 'Choose setting to load:','Load setting', choice, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            setting_name = dlg.GetStringSelection()
            setting = self.saved_settings[setting_name]
            self.controlpanel.data_sets_list = [[[] for i in xrange(self.controlpanel.max_row_num)] for j in xrange(self.controlpanel.max_column_num)]
            for i in xrange(self.controlpanel.max_row_num):
                for j in xrange(self.controlpanel.max_column_num):
                    set_up_list = setting['subplot('+str(i+1)+','+str(j+1)+')']
                    for data_set_name in set_up_list:
                        if self.controlpanel.latest_data_sets.has_key(data_set_name):
                            new_data_setup = data_setup(data_set_name, self.controlpanel.latest_data_sets.get(data_set_name))
                            self.controlpanel.data_sets_list[i][j].append(new_data_setup)
            
            self.controlpanel.plot_row_num.SetSelection(int(setting['row_num']) - 1)
            self.controlpanel.evt_select_row_num(wx.EVT_CHOICE)
            self.controlpanel.plot_column_num.SetSelection(int(setting['column_num']) - 1)
            self.controlpanel.evt_select_column_num(wx.EVT_CHOICE)
        
        dlg.Destroy()


    def on_save(self, event):
        dlg = wx.TextEntryDialog(self, 'Enter a new name for current setting','Save current setting as new')
        if dlg.ShowModal() == wx.ID_OK:
            setting_name = dlg.GetValue()
            setting = self.get_setting(setting_name)
            self.saved_settings.update(setting)
            self.saved_settings.write()
        dlg.Destroy()

    def on_save_as(self, event):
        choice = self.saved_settings.keys()
        choice.remove('DIR')
        dlg = wx.SingleChoiceDialog(self, 'Choose to overide an old setting:','Save current setting to old', choice, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            setting_name = dlg.GetStringSelection()
            setting = self.get_setting(setting_name)
            self.saved_settings.update(setting)
            self.saved_settings.write()
        dlg.Destroy()

    def get_setting(self, setting_name):
        section_name = setting_name
        section = {}
        section.update({'row_num': self.controlpanel.row_num})
        section.update({'column_num': self.controlpanel.column_num})
        data_sets_list = self.controlpanel.data_sets_list
        
        for i,data_sets_i in enumerate(data_sets_list):
            for j,data_sets_j in enumerate(data_sets_i):
                data_sets_name_list = []
                if len(data_sets_j)>0:
                    for data_set in data_sets_j:
                        data_sets_name_list.append(data_set.name)
                section.update({'subplot('+str(i+1)+','+str(j+1)+')': data_sets_name_list})
        return {section_name:section}

    def on_save_data_as(self, event):
        if (self.controlpanel.current_subplot >= 0) & (self.controlpanel.current_data_set >= 0):
            dlg = wx.TextEntryDialog(self, 'Enter a new name for current data set','Save current data set as new')
            if dlg.ShowModal() == wx.ID_OK:
                self.controlpanel.data_sets_list[self.controlpanel.current_row][self.controlpanel.current_column][self.controlpanel.current_data_set].name = dlg.GetValue()
                self.controlpanel.evt_press_save_data_setup(wx.EVT_BUTTON)
                self.controlpanel.update_data_sets()
                self.controlpanel.latest_data_sets.reload()
            dlg.Destroy()

                
    def on_delete_data_setup(self, event):
        choice = self.controlpanel.latest_data_sets.keys()
        dlg = wx.SingleChoiceDialog(self, 'Choose data setup:','Delete data setup', choice, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            setup_name = dlg.GetStringSelection()
            del self.controlpanel.latest_data_sets[setup_name]
            self.controlpanel.latest_data_sets.write()
        dlg.Destroy()

    def on_exit(self, event):
        self.Destroy()

    def on_data_dir(self, event):
        dlg = wx.DirDialog(self, "Choose a directory for data:", style = wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            global data_dir
            data_dir = dlg.GetPath()
            self.saved_settings['DIR']['data_dir'] = data_dir
            self.saved_settings.write()
        dlg.Destroy()

    def on_about(self, event):
        dlg = wx.MessageDialog(self, 'View Data 2.0', style = wx.OK)
        dlg.ShowModal()
        dlg.Destroy()


    def evt_press_replot(self, event):
        row_num = self.controlpanel.row_num
        column_num = self.controlpanel.column_num
        data_sets_list = self.controlpanel.data_sets_list

#        self.plotpanel.add_subplot()
        k = 0
        self.plotpanel.axes = []
        self.plotpanel.fig.clf()
        for i in xrange(row_num):
            for j in xrange(column_num):
                if len(data_sets_list[i][j]) > 0:
                    axes = self.plotpanel.fig.add_subplot(row_num, column_num, k+1)
                    self.plotpanel.axes.append(axes)
                    legend_tuple = ()
                    for l, data_set in enumerate(data_sets_list[i][j]):
                        data_set.get_data()
                        if len(data_set.data) > 0:
                            color = data_set.setup_dict['color'] if data_set.setup_dict['color'] != '' else 'black'
                            ec = data_set.setup_dict['ec'] if (data_set.setup_dict['ec'] != '')&(data_set.setup_dict['matchB'] == 'False') else color
                            fmt = data_set.setup_dict['fmt'] if data_set.setup_dict['fmt'] != '' else 'o'
                            ms = float(data_set.setup_dict['ms']) if data_set.setup_dict['ms'] != '' else 6.0
                            mew = float(data_set.setup_dict['mew']) if data_set.setup_dict['mew'] != '' else 1.0
                            
                            Legend = data_set.setup_dict['Legend'] if data_set.setup_dict['Legend'] != '' else 'NoLegend'

                            stats = (data_set.setup_dict['statsB'] == 'True') if data_set.setup_dict.has_key('statsB') else False
                            
                            axes.plot(data_set.data[:,0], data_set.data[:,1], fmt, mec = ec, mfc = color, ms = ms, mew =mew )
                            
                            legend_tuple = legend_tuple + (Legend,)

                            if data_set.setup_dict['plotB'] == 'True':
                                if data_set.setup_dict['fitB'] == 'True':
                                    data_set.get_fit()
                                    
                                    axes.plot(data_set.fitX, data_set.fitY)
                                    self.controlpanel.fit.fit_result.ChangeValue(data_set.setup_dict['fit_result'])
                                    legend_tuple = legend_tuple + (Legend+'_fit',)

                            if l == 0:
                                Xl = data_set.setup_dict['Xl'] if data_set.setup_dict['Xl'] != '' else data_set.setup_dict['X']
                                Yl = data_set.setup_dict['Yl'] if data_set.setup_dict['Yl'] != '' else data_set.setup_dict['Y']
                                grid = (data_set.setup_dict['gridB'] == 'True') if data_set.setup_dict.has_key('gridB') else False
                                Xmin = float(data_set.setup_dict['Xmin']) if data_set.setup_dict['Xmin'] != '' else 'nan'
                                Ymin = float(data_set.setup_dict['Ymin']) if data_set.setup_dict['Ymin'] != '' else 'nan'
                                Xmax = float(data_set.setup_dict['Xmax']) if data_set.setup_dict['Xmax'] != '' else 'nan'
                                Ymax = float(data_set.setup_dict['Ymax']) if data_set.setup_dict['Ymax'] != '' else 'nan'
                                logx = (data_set.setup_dict['logxB'] == 'True') if data_set.setup_dict.has_key('logxB') else False
                                logy = (data_set.setup_dict['logyB'] == 'True') if data_set.setup_dict.has_key('logyB') else False
                                xticks = (data_set.setup_dict['xticksB'] == 'True') if data_set.setup_dict.has_key('xticksB') else True
                                yticks = (data_set.setup_dict['yticksB'] == 'True') if data_set.setup_dict.has_key('yticksB') else True

                                axes.set_xlabel(Xl)
                                axes.set_ylabel(Yl)
                                axes.grid(grid)
                                
                                if xticks == False:
                                    axes.set_xticks([])

                                if yticks == False:
                                    axes.set_yticks([])

                                if logx:
                                    axes.set_xscale('log')
                                
                                if logy:
                                    axes.set_yscale('log')
                                
                                if (Xmin != 'nan') & (Xmax != 'nan'):
                                    axes.set_xlim(Xmin, Xmax)

                                if (Ymin != 'nan') & (Ymax != 'nan'):
                                    axes.set_ylim(Ymin, Ymax)

                    if legend_tuple != ():
                        axes.legend(legend_tuple)
                k = k+1
        self.plotpanel.canvas.draw()

        self.controlpanel.update_raw_data()

class PlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.dpi = 100
        self.fig = Figure((1.0, 1.0), dpi = self.dpi)
        self.canvas = FigCanvas(self, -1, self.fig)
        toolbar = NavigationToolbar2Wx( self.canvas )

#        self.axes = self.fig.add_subplot(2,1,1)
#        self.axes = self.fig.add_subplot(2,1,2)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.EXPAND | wx.ALL) #wx.LEFT | wx.TOP | wx.BOTTOM | wx.GROW
        self.vbox.Add(toolbar, 0, wx.EXPAND)
        self.SetSizerAndFit(self.vbox)
#        self.hbox.Fit(self)
#        self.axes = self.fig.add_subplot(2,1,2)

    def add_subplot(self):
        self.axes = self.fig.add_subplot(2,1,2)
        self.canvas.draw()

class ControlPanel(wx.Panel):
    ''' class of ControlPanel, containing all the controls for the plot'''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size = (200,400))

        #save setting button
        self.save_data_setup = wx.Button(self, label = "save data setup")
        self.Bind(wx.EVT_BUTTON, self.evt_press_save_data_setup, self.save_data_setup)

        #number of rows/columns of subplots
        self.row_num = 1
        self.column_num = 1
        self.max_row_num = 4
        self.max_column_num = 4
        self.current_subplot = 0
        self.current_data_set = -1
        self.update_current_subplot_row_column()
        self.data_sets_list = [[[] for i in xrange(self.max_row_num)] for j in xrange(self.max_column_num)]
        self.latest_data_sets = ConfigObj(latest_data_sets_dir)
#        self.data_sets_names = self.latest_data_sets.keys()

        self.tex_row_num = wx.StaticText(self, label = "rows:")
        self.plot_row_num = wx.Choice(self, choices = [str(i+1) for i in xrange(self.max_row_num)])
        self.Bind(wx.EVT_CHOICE, self.evt_select_row_num, self.plot_row_num)
        self.tex_column_num = wx.StaticText(self, label = "cols:")
        self.plot_column_num = wx.Choice(self, choices = [str(j+1) for j in xrange(self.max_row_num)])
        self.Bind(wx.EVT_CHOICE, self.evt_select_column_num, self.plot_column_num)
        
        #current subplot
        self.subplot_list = self.get_subplot_list()
        self.plot_cur = wx.ListBox(self, size = (60,100), choices = self.subplot_list, style = wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX,self.evt_select_subplot, self.plot_cur)

        #add/duplicate/delete data to subplot
        self.add = wx.Button(self, label = 'Add')
        self.Bind(wx.EVT_BUTTON, self.evt_press_add, self.add)

#        self.duplicate = wx.Button(self, label = 'Duplicate')
#        self.Bind(wx.EVT_BUTTON, self.evt_press_duplicate, self.duplicate)

        self.delete = wx.Button(self, label = 'Del')
        self.Bind(wx.EVT_BUTTON, self.evt_press_delete, self.delete)
        
        
        #data sets of current subplot
        self.data_sets = wx.ListBox(self, size = (250,40), style = wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.evt_select_data_sets, self.data_sets)

        #setup of one data set
        self.nb = wx.Notebook(self, size = (450,300))
        self.data_setup = DataSetup(self.nb)
        self.fit = Fit(self.nb)
        self.raw_data = RawData(self.nb)
        self.nb.AddPage(self.data_setup,"Setup")
        self.nb.AddPage(self.fit,"Fit")
        self.nb.AddPage(self.raw_data, "Raw Data")

        self.Bind(wx.EVT_TEXT, self.evt_date_change, self.data_setup.date)
        self.Bind(wx.EVT_TEXT, self.evt_shots_change, self.data_setup.shots)
        self.Bind(wx.EVT_TEXT, self.evt_X_change, self.data_setup.X)
        self.Bind(wx.EVT_TEXT, self.evt_Y_change, self.data_setup.Y)
        
        self.Bind(wx.EVT_TEXT, self.evt_Xl_change, self.data_setup.Xl)
        self.Bind(wx.EVT_TEXT, self.evt_Xmin_change, self.data_setup.Xmin)
        self.Bind(wx.EVT_TEXT, self.evt_Xmax_change, self.data_setup.Xmax)
        self.Bind(wx.EVT_TEXT, self.evt_Yl_change, self.data_setup.Yl)
        self.Bind(wx.EVT_TEXT, self.evt_Ymin_change, self.data_setup.Ymin)
        self.Bind(wx.EVT_TEXT, self.evt_Ymax_change, self.data_setup.Ymax)
        self.Bind(wx.EVT_TEXT, self.evt_Legend_change, self.data_setup.Legend)
        self.Bind(wx.EVT_TEXT, self.evt_color_change, self.data_setup.color)
        self.Bind(wx.EVT_TEXT, self.evt_ec_change, self.data_setup.ec)
        self.Bind(wx.EVT_CHECKBOX, self.evt_matchB_change, self.data_setup.matchB)
        self.Bind(wx.EVT_TEXT, self.evt_fmt_change, self.data_setup.fmt)
        self.Bind(wx.EVT_TEXT, self.evt_ms_change, self.data_setup.ms)
        self.Bind(wx.EVT_TEXT, self.evt_mew_change, self.data_setup.mew)

#        self.Bind(wx.EVT_CHECKBOX, self.evt_x2B_change, self.data_setup.x2B)
#        self.Bind(wx.EVT_CHECKBOX, self.evt_y2B_change, self.data_setup.y2B)
        self.Bind(wx.EVT_CHECKBOX, self.evt_statsB_change, self.data_setup.statsB)
        self.Bind(wx.EVT_CHECKBOX, self.evt_gridB_change, self.data_setup.gridB)
        self.Bind(wx.EVT_CHECKBOX, self.evt_logxB_change, self.data_setup.logxB)
        self.Bind(wx.EVT_CHECKBOX, self.evt_logyB_change, self.data_setup.logyB)
        self.Bind(wx.EVT_CHECKBOX, self.evt_xticksB_change, self.data_setup.xticksB)
        self.Bind(wx.EVT_CHECKBOX, self.evt_yticksB_change, self.data_setup.yticksB)


        self.Bind(wx.EVT_CHECKBOX, self.evt_plotB_change, self.fit.plotB)
        self.Bind(wx.EVT_CHECKBOX, self.evt_fitB_change, self.fit.fitB)
        self.Bind(wx.EVT_CHOICE, self.evt_func_change, self.fit.func)
        self.Bind(wx.EVT_TEXT, self.evt_para_list_0_change, self.fit.para_list[0])
        self.Bind(wx.EVT_TEXT, self.evt_para_list_1_change, self.fit.para_list[1])
        self.Bind(wx.EVT_TEXT, self.evt_para_list_2_change, self.fit.para_list[2])
        self.Bind(wx.EVT_TEXT, self.evt_para_list_3_change, self.fit.para_list[3])
        self.Bind(wx.EVT_TEXT, self.evt_para_list_4_change, self.fit.para_list[4])
        
        #Layout of the control panel
        hSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer1.Add(self.tex_row_num, 0, wx.ALIGN_CENTER, 0)
        hSizer1.Add(self.plot_row_num, 0, wx.ALIGN_CENTER, 0)
        hSizer1.Add(self.tex_column_num, 0, wx.ALIGN_CENTER, 0)
        hSizer1.Add(self.plot_column_num, 0 , wx.ALIGN_CENTER, 0)
        hSizer1.AddSpacer(30)
        hSizer1.AddSpacer(30)
        hSizer1.AddSpacer(30)
        hSizer1.AddSpacer(30)
        hSizer1.AddSpacer(30)
        hSizer1.AddSpacer(30)
        hSizer1.Add(self.save_data_setup, 0, wx.ALL, 0)

        vSizer22 = wx.BoxSizer(wx.VERTICAL)
        vSizer22.Add(self.add, 1, wx.ALL, 5)
#        vSizer22.Add(self.duplicate, 1, wx.ALL, 5)
        vSizer22.Add(self.delete, 1, wx.ALL, 5)

        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer2.Add(self.plot_cur, 0, wx.ALL, 5)
        hSizer2.Add(vSizer22, 0, wx.ALL, 5)
        hSizer2.Add(self.data_sets, 1, wx.EXPAND|wx.ALL, 5)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(hSizer1, 0, wx.ALL, 5)
        mainSizer.Add(hSizer2, 0, wx.ALL, 5)
        mainSizer.Add(self.nb, 1, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)


#    def update_data_sets_list(self):
#        self.data_sets_list = [[] for i in xrange(self.row_num * self.column_num)]

    def evt_press_save_data_setup(self, event):
#        self.latest_data_sets.get(new_data_set_name)
        if (self.current_subplot >= 0) & (self.current_data_set >= 0):
            data_set = self.data_sets_list[self.current_row][self.current_column][self.current_data_set]
            current_data_set_name = data_set.name
            self.latest_data_sets[current_data_set_name] = data_set.setup_dict
#            print type(self.latest_data_sets)
            self.latest_data_sets.write()

    def evt_select_row_num(self, event):
        self.row_num = self.plot_row_num.GetCurrentSelection() + 1
        self.update_plot_cur()

    def evt_select_column_num(self, event):
        self.column_num = self.plot_column_num.GetCurrentSelection() + 1
        self.update_plot_cur()

    def update_plot_cur(self):
        choices = self.get_subplot_list()
        self.current_subplot = 0
        self.update_current_subplot_row_column()
        self.plot_cur.DeselectAll()
        self.plot_cur.Clear()
        self.plot_cur.AppendItems(choices)
        self.plot_cur.SetSelection(0)
        self.evt_select_subplot(wx.EVT_LISTBOX)

    def get_subplot_list(self):
        '''get subplot ids from the number of rows/columns'''
        choices = []
        for i in range(self.row_num):
            for j in range(self.column_num):
                choices = choices + ['(' + str(i+1) + ',' + str(j+1) + ')']

        return choices

    def evt_select_subplot(self, event):
        self.current_subplot = self.plot_cur.GetSelections()[0]
        self.update_current_subplot_row_column()
        self.flag_add_pressed = False
        self.update_data_sets()

    def update_current_subplot_row_column(self):
        if self.current_subplot >= 0:
            self.current_row = self.current_subplot/self.column_num
            self.current_column = self.current_subplot%self.column_num
        else:
            self.current_row = 0
            self.current_column = 0

    def evt_press_add(self, event):
        dlg = wx.SingleChoiceDialog(self, 'Add one data set:', 'Choose Data Set', self.latest_data_sets.keys(), wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            new_data_set_name = dlg.GetStringSelection()
            new_data_setup = data_setup(new_data_set_name, self.latest_data_sets.get(new_data_set_name))
            self.data_sets_list[self.current_row][self.current_column].append(new_data_setup)
            self.flag_add_pressed = True
            self.update_data_sets()
        dlg.Destroy()

    def update_data_sets(self):
        self.data_sets.DeselectAll()
        self.data_sets.Clear()
        self.current_data_set = -1
        if len(self.data_sets_list[self.current_row][self.current_column]) > 0:
            for i, data_setup_instant in enumerate(self.data_sets_list[self.current_row][self.current_column]):
                data_set_name = str(i+1) +'.' +data_setup_instant.name
                self.data_sets.Append(data_set_name)

            if self.flag_add_pressed:
                self.current_data_set = len(self.data_sets_list[self.current_row][self.current_column]) - 1
                self.data_sets.SetSelection(self.current_data_set)
            else:
                self.current_data_set = 0
                self.data_sets.SetSelection(0)
            self.evt_select_data_sets(wx.EVT_LISTBOX)
        else:
            self.update_setup()

    def evt_select_data_sets(self, event):
#        self.update_data_sets_list()
        self.current_data_set = self.data_sets.GetSelections()[0]
        self.update_setup()

#    def evt_press_duplicate(self, event):
#        print 'duplicating'

    def evt_press_delete(self, event):
        if self.current_data_set >= 0:
            self.data_sets_list[self.current_row][self.current_column].pop(self.current_data_set)
            self.current_data_set = -1
            self.update_data_sets()

    def update_raw_data(self):
        if self.data_sets_list[self.current_row][self.current_column] == []:
            raw_data = ''
        else:
            raw_data = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].raw_data
        self.raw_data.text.ChangeValue(raw_data)

    def update_setup(self):
        if self.data_sets_list[self.current_row][self.current_column] == []:
            setup_dict = {}
        else:
            setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        
        if setup_dict.has_key('date'):
            self.data_setup.date.ChangeValue(setup_dict['date'])
        else:
            self.data_setup.date.ChangeValue('')

        if setup_dict.has_key('shots'):
            shots = setup_dict['shots']
            if type(shots) == type([]):
                shots = ", ".join(shots)
            shots.replace(" ", "")
            self.data_setup.shots.ChangeValue(shots)
        else:
            self.data_setup.shots.ChangeValue('')

        if setup_dict.has_key('X'):
            self.data_setup.X.ChangeValue(setup_dict['X'])
        else:
            self.data_setup.X.ChangeValue('')

        if setup_dict.has_key('Y'):
            self.data_setup.Y.ChangeValue(setup_dict['Y'])
        else:
            self.data_setup.Y.ChangeValue('')

        if setup_dict.has_key('Xl'):
            self.data_setup.Xl.ChangeValue(setup_dict['Xl'])
        else:
            self.data_setup.Xl.ChangeValue('')

        if setup_dict.has_key('Xmin'):
            self.data_setup.Xmin.ChangeValue(setup_dict['Xmin'])
        else:
            self.data_setup.Xmin.ChangeValue('')

        if setup_dict.has_key('Xmax'):
            self.data_setup.Xmax.ChangeValue(setup_dict['Xmax'])
        else:
            self.data_setup.Xmax.ChangeValue('')

        if setup_dict.has_key('Yl'):
            self.data_setup.Yl.ChangeValue(setup_dict['Yl'])
        else:
            self.data_setup.Yl.ChangeValue('')

        if setup_dict.has_key('Ymin'):
            self.data_setup.Ymin.ChangeValue(setup_dict['Ymin'])
        else:
            self.data_setup.Ymin.ChangeValue('')

        if setup_dict.has_key('Ymax'):
            self.data_setup.Ymax.ChangeValue(setup_dict['Ymax'])
        else:
            self.data_setup.Ymax.ChangeValue('')

        if setup_dict.has_key('Legend'):
            self.data_setup.Legend.ChangeValue(setup_dict['Legend'])
        else:
            self.data_setup.Legend.ChangeValue('')

        if setup_dict.has_key('color'):
            self.data_setup.color.ChangeValue(setup_dict['color'])
        else:
            self.data_setup.color.ChangeValue('')

        if setup_dict.has_key('ec'):
            self.data_setup.ec.ChangeValue(setup_dict['ec'])
        else:
            self.data_setup.ec.ChangeValue('')

        if setup_dict.has_key('fmt'):
            self.data_setup.fmt.ChangeValue(setup_dict['fmt'])
        else:
            self.data_setup.fmt.ChangeValue('')

        if setup_dict.has_key('ms'):
            self.data_setup.ms.ChangeValue(setup_dict['ms'])
        else:
            self.data_setup.ms.ChangeValue('')

        if setup_dict.has_key('mew'):
            self.data_setup.mew.ChangeValue(setup_dict['mew'])
        else:
            self.data_setup.mew.ChangeValue('')

        if setup_dict.has_key('matchB'):
            self.data_setup.matchB.SetValue(setup_dict['matchB'] == 'True' )
        else:
            self.data_setup.matchB.SetValue(True)

#        if setup_dict.has_key('x2B'):
#            self.data_setup.x2B.SetValue(setup_dict['x2B'])
#        else:
#            self.data_setup.x2B.SetValue(False)
#
#        if setup_dict.has_key('y2B'):
#            self.data_setup.y2B.SetValue(setup_dict['y2B'])
#        else:
#            self.data_setup.y2B.SetValue(False)

        if setup_dict.has_key('statsB'):
            self.data_setup.statsB.SetValue(setup_dict['statsB'] == 'True')
        else:
            self.data_setup.statsB.SetValue(False)

        if setup_dict.has_key('gridB'):
            self.data_setup.gridB.SetValue(setup_dict['gridB'] == 'True')
        else:
            self.data_setup.gridB.SetValue(False)

        if setup_dict.has_key('logxB'):
            self.data_setup.logxB.SetValue(setup_dict['logxB'] == 'True')
        else:
            self.data_setup.logxB.SetValue(False)

        if setup_dict.has_key('logyB'):
            self.data_setup.logyB.SetValue(setup_dict['logyB'] == 'True')
        else:
            self.data_setup.logyB.SetValue(False)

        if setup_dict.has_key('xticksB'):
            self.data_setup.xticksB.SetValue(setup_dict['xticksB'] == 'True')
        else:
            self.data_setup.xticksB.SetValue(False)

        if setup_dict.has_key('yticksB'):
            self.data_setup.yticksB.SetValue(setup_dict['yticksB'] == 'True')
        else:
            self.data_setup.yticksB.SetValue(False)

        if setup_dict.has_key('plotB'):
            self.fit.plotB.SetValue(setup_dict['plotB'] == 'True')
        else:
            self.fit.plotB.SetValue(False)
        
        if setup_dict.has_key('fitB'):
            self.fit.fitB.SetValue(setup_dict['fitB'] == 'True')
        else:
            self.fit.fitB.SetValue(False)

        if setup_dict.has_key('func'):
            self.fit.func.SetStringSelection(setup_dict['func'])
            self.evt_func_change(wx.EVT_CHOICE)
        else:
            self.fit.func.SetSelection(0)

        if setup_dict.has_key('para_list'):
#            print setup_dict['para_list']
            self.fit.para_list[0].ChangeValue(setup_dict['para_list'][0])
            self.fit.para_list[1].ChangeValue(setup_dict['para_list'][1])
            self.fit.para_list[2].ChangeValue(setup_dict['para_list'][2])
            self.fit.para_list[3].ChangeValue(setup_dict['para_list'][3])
            self.fit.para_list[4].ChangeValue(setup_dict['para_list'][4])
        else:
            self.fit.para_list[0].ChangeValue('0')
            self.fit.para_list[1].ChangeValue('0')
            self.fit.para_list[2].ChangeValue('0')
            self.fit.para_list[3].ChangeValue('0')
            self.fit.para_list[4].ChangeValue('0')

        if setup_dict.has_key('fit_result'):
            self.fit.fit_result.ChangeValue(setup_dict['fit_result'])
        else:
            self.fit.fit_result.ChangeValue('')
        
        self.update_raw_data()
    
    
    def evt_date_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['date'] = self.data_setup.date.GetValue()

    def evt_shots_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['shots'] = self.data_setup.shots.GetValue().replace(" ", "")
    
    def evt_X_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['X'] = self.data_setup.X.GetValue()
    
    def evt_Y_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Y'] = self.data_setup.Y.GetValue()
    
    def evt_Xl_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Xl'] = self.data_setup.Xl.GetValue()
    
    def evt_Xmin_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Xmin'] = self.data_setup.Xmin.GetValue()
    
    def evt_Xmax_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Xmax'] = self.data_setup.Xmax.GetValue()
    
    def evt_Yl_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Yl'] = self.data_setup.Yl.GetValue()
    
    def evt_Ymin_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Ymin'] = self.data_setup.Ymin.GetValue()
    
    def evt_Ymax_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Ymax'] = self.data_setup.Ymax.GetValue()
    
    def evt_Legend_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['Legend'] = self.data_setup.Legend.GetValue()
    
    def evt_color_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['color'] = self.data_setup.color.GetValue()
    
    def evt_ec_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['ec'] = self.data_setup.ec.GetValue()
    
    def evt_fmt_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['fmt'] = self.data_setup.fmt.GetValue()
    
    def evt_ms_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['ms'] = self.data_setup.ms.GetValue()

    def evt_mew_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['mew'] = self.data_setup.mew.GetValue()

    def evt_matchB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['matchB'] = 'True' if self.data_setup.matchB.GetValue() else 'False'

#    def evt_x2B_change(self, event):
#        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
#        setup_dict['x2B'] = self.data_setup.x2B.GetValue()
#
#    def evt_y2B_change(self, event):
#        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
#        setup_dict['y2B'] = self.data_setup.y2B.GetValue()

    def evt_statsB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['statsB'] = 'True' if self.data_setup.statsB.GetValue() else 'False'

    def evt_gridB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['gridB'] = 'True' if self.data_setup.gridB.GetValue() else 'False'

    def evt_logxB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['logxB'] = 'True' if self.data_setup.logxB.GetValue() else 'False'

    def evt_logyB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['logyB'] = 'True' if self.data_setup.logyB.GetValue() else 'False'

    def evt_xticksB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['xticksB'] = 'True' if self.data_setup.xticksB.GetValue() else 'False'

    def evt_yticksB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['yticksB'] = 'True' if self.data_setup.yticksB.GetValue() else 'False'

    def evt_plotB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['plotB'] = 'True' if self.fit.plotB.GetValue() else 'False'

    def evt_fitB_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['fitB'] = 'True' if self.fit.fitB.GetValue() else 'False'

    def evt_func_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        setup_dict['func'] = self.fit.func.GetStringSelection()
        self.fit.function = fitdict[setup_dict['func']]
#        print setup_dict['func']
#        print fitdict[setup_dict['func']].fitexpr
        self.fit.tex_function.SetLabel('f(x) = ' + self.fit.function.fitexpr)

    def evt_para_list_0_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        if setup_dict.has_key('para_list') == False:
            setup_dict['para_list'] = [ 0 for i in xrange(5)]
        setup_dict['para_list'][0] = self.fit.para_list[0].GetValue()

    def evt_para_list_1_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        if setup_dict.has_key('para_list') == False:
            setup_dict['para_list'] = [ 0 for i in xrange(5)]
        setup_dict['para_list'][1] = self.fit.para_list[1].GetValue()

    def evt_para_list_2_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        if setup_dict.has_key('para_list') == False:
            setup_dict['para_list'] = [ 0 for i in xrange(5)]
        setup_dict['para_list'][2] = self.fit.para_list[2].GetValue()

    def evt_para_list_3_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        if setup_dict.has_key('para_list') == False:
            setup_dict['para_list'] = [ 0 for i in xrange(5)]
        setup_dict['para_list'][3] = self.fit.para_list[3].GetValue()

    def evt_para_list_4_change(self, event):
        setup_dict = self.data_sets_list[self.current_row][self.current_column][self.current_data_set].setup_dict
        if setup_dict.has_key('para_list') == False:
            setup_dict['para_list'] = [ 0 for i in xrange(5)]
        setup_dict['para_list'][4] = self.fit.para_list[4].GetValue()


class data_setup():
    def __init__(self, name, setup_dict):
        self.name = name
        self.setup_dict = copy.deepcopy(setup_dict)
        self.raw_data = ''

    def get_data(self):
        directory = self.get_dir()
        shots = self.setup_dict['shots']
        if type(shots) == type([]):
            shots = ",".join(shots)
        keys = " ".join([self.setup_dict['X'], self.setup_dict['Y']])
        self.data, self.errmsg, self.raw_data = qrange.qrange(directory, shots, keys)
    
    def get_dir(self):
        year, month, day = self.setup_dict['date'].split('/')
        year2 = year[2:4]
        return data_dir + '/' + year + '/' + year2+month + '/' + year2+month+day + '/' 

    def get_fit(self):
        func_name = self.setup_dict['func']
        function = fitdict[func_name].function
        p = [ float(f) for f in self.setup_dict['para_list']]
        data = numpy.array(self.data)
        self.para_list_fit, self.error_list_fit = fit_function(p, data, function)
        self.fitX, self.fitY = plot_function(self.para_list_fit, data[:,0], function)
        self.fit_result_string = 'para' + '\t\t\t' + 'error' + '\n'
        for i, para in enumerate(self.para_list_fit):
            self.fit_result_string = self.fit_result_string + "{0:.2e}".format(para) + '\t' + "{0:.2e}".format(self.error_list_fit[i]) + '\n'
        self.setup_dict['fit_result'] = self.fit_result_string


class DataSetup(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.tex_date = wx.StaticText(self, label = "Date:")
        self.date = wx.TextCtrl(self, size = (150,30))
#        self.Bind(wx.EVT_TEXT, ControlPanel.evt_date_change, self.date)

        self.tex_shots = wx.StaticText(self, label = "Shots:")
        self.shots = wx.TextCtrl(self, size = (370,30))
        
        self.tex_X = wx.StaticText(self, label = "X:")
        self.X = wx.TextCtrl(self, size = (370,30))

        self.tex_Y = wx.StaticText(self, label = "Y:")
        self.Y = wx.TextCtrl(self, size = (370,30))

#        self.tex_color = wx.StaticText(self, label = "color:")
#        self.color = wx.TextCtrl(self, size = (100,30))

        grid1 = wx.GridBagSizer(hgap = 5, vgap = 5)
        grid1.Add(self.tex_date, pos = (0,0))
        grid1.Add(self.date, pos = (0,1))
        grid1.Add(self.tex_shots, pos = (1,0))
        grid1.Add(self.shots, pos = (1,1))
        grid1.Add(self.tex_X, pos = (2,0))
        grid1.Add(self.X, pos = (2,1))
        grid1.Add(self.tex_Y, pos = (3,0))
        grid1.Add(self.Y, pos = (3,1))
#        grid1.Add(self.tex_color, pos = (4,0))
#        grid1.Add(self.color, pos = (4,1))
        
        
        #### PLOT SECTION
        grid0  = wx.FlexGridSizer(1, 6, 7, 15)
#        self.x2B     =  wx.CheckBox(self, label="X2?")
#        self.y2B     =  wx.CheckBox(self, label="Y2?")
        self.statsB  =  wx.CheckBox(self, label="stats")
        self.gridB   =  wx.CheckBox(self, label="grid")
        self.logxB   =  wx.CheckBox(self, label="logx")
        self.logyB   =  wx.CheckBox(self, label="logy")
        self.xticksB =  wx.CheckBox(self, label="xticks")
        self.yticksB =  wx.CheckBox(self, label="yticks")
#        grid0.AddMany([(self.x2B), (self.y2B), (self.statsB), (self.gridB), (self.logxB), (self.logyB), (self.xticksB), (self.yticksB) ])
        grid0.AddMany([(self.statsB), (self.gridB), (self.logxB), (self.logyB), (self.xticksB), (self.yticksB) ])
       
       
        grid2 = wx.FlexGridSizer(2, 6, 9, 15)
        self.optxlab = wx.StaticText(self, label="Xl")
        self.optxmin = wx.StaticText(self, label="Xmin")
        self.optxmax = wx.StaticText(self, label="Xmax")

        self.optylab = wx.StaticText(self, label="Yl")
        self.optymin = wx.StaticText(self, label="Ymin")
        self.optymax = wx.StaticText(self, label="Ymax")

        self.Xl = wx.TextCtrl(self)
        self.Xmin = wx.TextCtrl(self)
        self.Xmax = wx.TextCtrl(self)
        self.Yl = wx.TextCtrl(self)
        self.Ymin = wx.TextCtrl(self)
        self.Ymax = wx.TextCtrl(self)

        grid2.AddMany([
         (self.optxlab), (self.Xl, 2, wx.EXPAND), (self.optxmin), (self.Xmin), (self.optxmax), (self.Xmax),
         (self.optylab), (self.Yl, 2, wx.EXPAND), (self.optymin), (self.Ymin), (self.optymax), (self.Ymax)])
        grid2.AddGrowableCol(1, 1)

        grid3 = wx.FlexGridSizer(1, 2, 9, 15)
        self.optleg = wx.StaticText(self, label="Legend")
        self.Legend = wx.TextCtrl(self, size = (350,30))
        grid3.AddMany([(self.optleg), (self.Legend)])
        grid3.AddGrowableCol(1, 1)

        grid4 = wx.FlexGridSizer(2,6, 9, 15)
        self.optec  = wx.StaticText(self, label="fc")
        self.optfc  = wx.StaticText(self, label="ec")
        self.optfmt = wx.StaticText(self, label="fmt")
        self.optms  = wx.StaticText(self, label="ms")
        self.optmew = wx.StaticText(self, label="mew")
        self.dummy = wx.StaticText(self, label="")

        self.color = wx.TextCtrl(self)
        self.ec = wx.TextCtrl(self)
        self.fmt = wx.TextCtrl(self)
        self.ms = wx.TextCtrl(self)
        self.mew = wx.TextCtrl(self)
        self.matchB =  wx.CheckBox(self, label="match?")
        grid4.AddMany([(self.optec), (self.color, 1, wx.EXPAND),
                      (self.optfc), (self.ec, 1, wx.EXPAND),
                      (self.matchB), (self.dummy),
                      (self.optfmt), (self.fmt, 1, wx.EXPAND),
                      (self.optms), (self.ms, 1, wx.EXPAND),
                      (self.optmew), (self.mew, 1, wx.EXPAND),
                      ])
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(5)
        vbox.Add(grid0)
        vbox.AddSpacer(5)
        vbox.Add(grid1)
        vbox.AddSpacer(5)
#        vbox.Add(grid2, proportion=1, flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)
        vbox.Add(grid2)
        vbox.AddSpacer(5)
#        vbox.Add(grid3, proportion=0, flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)
        vbox.Add(grid3)
        vbox.AddSpacer(5)
        vbox.Add(grid4)

        self.SetSizerAndFit(vbox)


class Fit(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.plotB   =  wx.CheckBox(self, label="plot?")
        self.fitB   =  wx.CheckBox(self, label="fit?")

        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.AddSpacer(20)
        hbox0.Add(self.plotB)
        hbox0.AddSpacer(30)
        hbox0.Add(self.fitB)

        self.tex_func = wx.StaticText(self, label = "Func:")
        self.func = wx.Choice(self, choices = fitdict.keys())
        hbox0.AddSpacer(30)
        hbox0.Add(self.tex_func)
        hbox0.AddSpacer(10)
        hbox0.Add(self.func)

#        self.tex_x0 = wx.StaticText(self, label = "x0:")
#        self.x0 = wx.TextCtrl(self,size = (100,30))
#
#        self.tex_xf = wx.StaticText(self, label = "xf:")
#        self.xf = wx.TextCtrl(self, size = (100,30))
#
#        self.tex_y0 = wx.StaticText(self, label = "y0:")
#        self.y0 = wx.TextCtrl(self,size = (100,30))
#
#        self.tex_yf = wx.StaticText(self, label = "yf:")
#        self.yf = wx.TextCtrl(self, size = (100,30))
#
#        grid1 = wx.FlexGridSizer(2,4, 9, 15)
#        grid1.AddMany([(self.tex_x0), (self.x0, 1, wx.EXPAND),
#                      (self.tex_xf), (self.xf, 1, wx.EXPAND),
#                      (self.tex_y0), (self.y0, 1, wx.EXPAND),
#                      (self.tex_yf), (self.yf, 1, wx.EXPAND)])
        
        self.tex_function = wx.StaticText(self, label = "f(x) = ")
        
        vbox3 = wx.BoxSizer(wx.VERTICAL)
        self.para_list = []
        for i in xrange(5):
            text = wx.TextCtrl(self, size = (70, 30))
            self.para_list.append(text)
            vbox3.Add(text)
        
#        self.para_list[2].SetValue('abc')
        self.fit_result = wx.TextCtrl(self, size = (250, 150), style = wx.TE_READONLY | wx.TE_MULTILINE)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(vbox3)
        hbox4.AddSpacer(20)
        hbox4.Add(self.fit_result)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(hbox0)
#        vbox.Add(grid1)
        vbox.AddSpacer(10)
        vbox.Add(self.tex_function)
        vbox.AddSpacer(10)
        vbox.Add(hbox4)
#        grid.Add(self.date, pos = (0,1))
#        grid.Add(self.tex_fit2, pos = (1,0))
#        grid.Add(self.shots, pos = (1,1))
        self.SetSizerAndFit(vbox)

class RawData(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.text = wx.TextCtrl(self, style = wx.TE_MULTILINE)
        self.text.SetEditable(False)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(sizer)

if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(parent = None, title = "view data 2.0")
    app.MainLoop()
