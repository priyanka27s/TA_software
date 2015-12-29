# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 18:23:12 2015

@author: thomasaref
"""

from taref.core.chief import Chief
from taref.core.save_file import Save_TXT
#from taref.core.log import log_info
from atom.api import Typed, Float, Enum, Callable, Dict
from enaml import imports
from collections import OrderedDict
from taref.ebl.jdf import JDF_Top, JDF_Pattern, JDF_Assign
from taref.ebl.polygon_backbone import sPoly,minx, maxx, miny, maxy

class Polygon_Chief(Chief):
    jdf=Typed(JDF_Top)
    
    def _default_jdf(self):
        jdf=JDF_Top()
        assign_list=[]
        for n, p in enumerate(self.agents):
            jdf.patterns.append(JDF_Pattern(num=n+1, name=p.name))
            assign_list.append("P({0})".format(n+1))
            #jdf.arrays[0].assigns.append(JDF_Assign(assign_type=["P({0})".format(n+1)], short_name=p.name))
        jdf.arrays[0].assigns.append(JDF_Assign(assign_type=assign_list))
        return jdf

    def plot_JDF(self):
        for p in self.jdf.patterns:
            a=self.agent_dict[p.name] #[agent for agent in self.agents if agent.name==p.name][0]
            verts=sPoly(a)
            self.plot.set_data(a.name, verts, a.color)
            xmin=minx(verts)
            xmax=maxx(verts)
            ymin=miny(verts)
            ymax=maxy(verts)
            
        #xmin=min(b.xmin for b in self.agents)
        #xmax=max(b.xmax for b in self.agents)
        #ymin=min(b.ymin for b in self.agents)
        #ymax=max(b.ymax for b in self.agents)
        self.plot.set_xlim(xmin, xmax)
        self.plot.set_ylim(ymin, ymax)
        self.plot.draw()
            
        
    angle_x=Float(0.3e-6).tag(desc="shift in x direction when doing angle evaporation", unit="um")
    angle_y=Float(0.0e-6).tag(desc="shift in y direction when doing angle evaporation", unit="um")
    view_type=Enum("pattern", "angle")
    add_type=Enum("overwrite", "add")

    save_factory=Callable(Save_TXT)

    pattern_dict=Dict() #for plotting
    patterns=Typed(OrderedDict, ()) #for generating jdf

    def do_plot(self):
        for p in self.agents:
            p.verts=[]
            p.make_polylist()
            if p.plot_sep:
                self.plot.set_data(p.name, p.verts, p.color)
            #self.pattern_dict[p.name]=dict(verts=p.verts[:], color=p.color, layer=p.layer, plot_sep=p.plot_sep)
            p.make_name_sug()
            p.save_file.main_file=p.name_sug+".dxf"

        #for key in self.pattern_dict:
        #    if self.pattern_dict[key]["plot_sep"]:
        #        self.plot.set_data(key, self.pattern_dict[key]["verts"], self.pattern_dict[key]["color"])

        xmin=min(b.xmin for b in self.agents)
        xmax=max(b.xmax for b in self.agents)
        ymin=min(b.ymin for b in self.agents)
        ymax=max(b.ymax for b in self.agents)
        self.plot.set_xlim(xmin, xmax)
        self.plot.set_ylim(ymin, ymax)
        self.plot.draw()

    def _default_show_all(self):
        return True

    @property
    def view_window(self):
        with imports():
            from taref.ebl.polygon_chief_e import EBLView
        return EBLView(chief=self)

polygon_chief=Polygon_Chief()

if __name__=="__main__":
    polygon_chief.show()