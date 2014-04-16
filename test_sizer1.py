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
from scipy import stats
import copy

import qrange

from fitlibrary import *
import statdat



data_dir = '/home/xinxing/Programs/data'

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
#        wx.Frame.__init__(self, parent, title=title, size = (1300, 600))
        wx.Frame.__init__(self, parent, title=title, size = (1000,400))
        
#        self.scroll = wx.ScrolledWindow(self, -1)
#        self.scroll.SetScrollbars(1,1,1300,1000)

        self.mainpanel = wx.ScrolledWindow(self,-1)
#        self.mainpanel.SetScrollbars(1,1,1600,1200)
        
        self.plotpanel = PlotPanel(self.mainpanel)
        self.plotpanel.SetBackgroundColour('blue')
        self.controlpanel = ControlPanel(self.mainpanel)
        self.controlpanel.SetBackgroundColour('red')
#       
        self.replot = wx.Button(self.mainpanel, label = 'replot')
#        self.Bind(wx.EVT_BUTTON, self.evt_press_replot, self.replot)
#        
        self.vSizer = wx.BoxSizer(wx.VERTICAL)
        self.vSizer.Add(self.replot, 0, wx.EXPAND | wx.ALL, 5)
        self.vSizer.Add(self.controlpanel, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.plotpanel, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(self.vSizer, 0,  wx.EXPAND | wx.ALL, 5)
        self.mainpanel.SetSizer(mainSizer)

        self.mainpanel.SetScrollbars(1,1,1600,12000)
#        self.vSizer = wx.BoxSizer(wx.VERTICAL)
#        self.vSizer.Add(self.replot, 0, wx.EXPAND | wx.ALL, 5)
#        self.vSizer.Add(self.controlpanel, 1, wx.EXPAND | wx.ALL, 5)
#        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
#        mainSizer.Add(self.plotpanel, 1, wx.EXPAND | wx.ALL, 5)
#        mainSizer.Add(self.vSizer, 0,  wx.EXPAND | wx.ALL, 5)
#        self.mainpanel.SetSizerAndFit(mainSizer)

        self.Center()
        self.Show(True)

class PlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        

class ControlPanel(wx.Panel):
    ''' class of ControlPanel, containing all the controls for the plot'''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size = (400,1000))

if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(parent = None, title = "view data 2.1")
    app.MainLoop()

#    curve1 = Curve_Setup_Dict()
#    curve1.set_value('location', '1,8')
#    curve1.set_value('name', 'my new')
#
##    for elem in curve1.dic:
##        print '%s is: ' %elem, curve1.get_str(elem)
#
##    print curve1.get_str_dic()
##    for i in xrange(2):
##        print 'para_list[%d]: ' %i, curve1.get('location', i)
#    subplot1 = Subplot_Setup_Dict()
#    subplot1.add_curve()
#    subplot1.add_curve()
#    subplot1.add_curve(curve1)
#
#    config = ConfigObj()
#    config.filename = 'new_setting.INI'
#    config['1st section'] = subplot1.get_str_dic()
#    config.write()
#
#    config = ConfigObj('./new_setting.INI')
##    print config['1st section']['curve 1']['name']
#    subplot1.set_str_dic(config['1st section'])
#    print subplot1.dic['curvelist'][0].dic
#    print subplot1.dic['curvelist'][1].dic
#    print subplot1.dic['curvelist'][2].dic
