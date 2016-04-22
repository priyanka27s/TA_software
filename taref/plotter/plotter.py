# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 14:50:17 2016

@author: thomasaref
"""

from taref.plotter.fig_format import Fig
from taref.plotter.plotter_backbone import process_kwargs
from taref.core.atom_extension import private_property
from taref.plotter.plot_format import line_plot, vline_plot, hline_plot, scatter_plot, colormesh_plot, multiline_plot


class Plotter(Fig):
    def line(self, *args, **kwargs):
        kwargs=process_kwargs(self, kwargs)
        line_plot(self, *args, **kwargs)

    def vline(self, plot_name="", *args, **kwargs):
        kwargs=process_kwargs(self, kwargs)
        vline_plot(self, plot_name, *args, **kwargs)

    def hline(self, plot_name="", *args, **kwargs):
        kwargs=process_kwargs(self, kwargs)
        hline_plot(self, plot_name, *args, **kwargs)

    def scatter(self, plot_name="", *args, **kwargs):
        kwargs=process_kwargs(self, kwargs)
        scatter_plot(self, plot_name, *args, **kwargs)

    def colormesh(self, plot_name="", *args, **kwargs):
        kwargs=process_kwargs(self, kwargs)
        colormesh_plot(self, plot_name=plot_name, *args, **kwargs)

    def multiline(self, plot_name="", *args,**kwargs):
        kwargs=process_kwargs(self, kwargs)
        multiline_plot(self, plot_name=plot_name, *args,**kwargs)

    def savefig(self, dir_path="/Users/thomasaref/Documents/TA_software/", fig_name="test_colormap_plot.png"):
        """saves the figure. if a canvas does not exist, the window will be shown and hidden to create it.
        if a QtApplication is not active, a temporary one will be created but not run to host the plot"""
        print "saving figure"
        self.figure.savefig(dir_path+fig_name, dpi=self.dpi,
                            bbox_inches='tight',
                            transparent=self.transparent)#, format=self.save_type)

    @classmethod
    def plot_do(cls, plot_func, *args, **kwargs):
        """utility function that extracts plotter and plot_name from kwargs and then does plot specified by func_name"""
        plotter=kwargs.pop("plotter", None)
        #plot_name=kwargs.pop("plot_name", "")
        if plotter is None:
            plotter=Plotter()
        elif isinstance(plotter, basestring):
            if plotter in cls.agent_dict:
                plotter=cls.agent_dict[plotter]
            else:
                plotter=Plotter(name=plotter)
        getattr(plotter, plot_func)(*args, **kwargs)
        return plotter

    @private_property
    def cls_run_funcs(self):
        """class or static methods to include in run_func_dict on initialization. Can be overwritten in child classes"""
        return [self.savefig]
#
#def plots(func):
#    """decorator that assists with plotting function definition"""
#    def plotty_func(obj, *args, **kwargs):
#        plotter=kwargs.pop("pl", None)
#        plot_name=kwargs.pop("pn", "")
#        if plotter is None:
#            plotter=Plotter()
#        elif isinstance(plotter, basestring):
#            if plotter in obj.agent_dict:
#                plotter=obj.agent_dict[plotter]
#            else:
#                plotter=Plotter(name=plotter)
#        print args, kwargs
#        func(obj, plotter, plot_name, *args, **kwargs)
#        return plotter
#    return plotty_func



def line(*args, **kwargs):
    return Plotter.plot_do("line", *args, **kwargs)

def vline(*args, **kwargs):
    return Plotter.plot_do("vline", *args, **kwargs)

def hline(*args, **kwargs):
    return Plotter.plot_do("hline", *args, **kwargs)

def scatter(*args, **kwargs):
    return Plotter.plot_do("scatter", *args, **kwargs)

def colormesh(*args, **kwargs):
    return Plotter.plot_do("colormesh", *args, **kwargs)

def multiline(*args, **kwargs):
    return Plotter.plot_do("multiline", *args, **kwargs)

if __name__=="__main__":
    b=line([[4,5,6], [7,8,9]])
    #b=scatter([1,2,3])

    #b=vline(3, plotter=b)
    print Plotter.agent_dict

    b.show()
