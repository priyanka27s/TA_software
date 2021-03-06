# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 10:46:56 2015

@author: thomasaref
"""

#from a_Base import Base, NoShowBase
from Plotter import Plotter
from Atom_Text_Editor import Text_Editor
from EBL_quarter_coords import distribute_coords, get_GLM, get_Array
from atom.api import Typed, Dict, Unicode, ContainerList, Int, Float, Atom, List, Coerced, Enum
#from LOG_functions import log_info, log_debug, make_log_file, log_warning
from a_Show import show
from enaml import imports

def xy_string_split(tempstr):
    return tempstr.split("(")[1].split(")")[0].split(",")+tempstr.split("(")[2].split(")")[0].split(",")

def tuple_split(tempstr):
    return tempstr.split("(")[1].split(")")[0].split(",")

class JDF_Assign(Atom):
    assign_type=List(default=['P(1)']) #list of assigns #.tag(inside_type=unicode)
    pos_assign=List(default=[(1,1)])# list of tuples of position.tag(inside_type=jdf_pos)#inside_labels=["x", "y"])
    shot_assign=Unicode() # shot mod table name ContainerList(default=[0])
    assign_comment=Unicode()  #comment to assign

class JDF_Array(Atom):
    """describes a jdf array. defaults to an array centered at 0,0 with one item.
    array_num=0 corresponds to the main array"""
    array_num=Coerced(int) #Int()
    x_start=Coerced(int) #Int()
    x_num=Coerced(int, (1,)) #Int(1)
    x_step=Coerced(int) #Int()
    y_start=Coerced(int) #Int()
    y_num=Coerced(int, (1,)) #Int(1)
    y_step=Coerced(int) #Int()
    assigns=ContainerList().tag(no_spacer=True)# inside_type=jdf_assign)

    def add_assign(self, tempstr, comment):
        assign_type=tempstr.split("ASSIGN")[1].split("->")[0].strip().split("+")
        assign_type=[unicode(at) for at in assign_type]
        pos_assign=[]
        shot_assign=""
        for item in tempstr.split("->")[1].partition("(")[2].rpartition(")")[0].split(")"):
            if "(" in item:
                xcor, ycor=item.split("(")[1].split(",")
                pos_assign.append((xcor,ycor))
            elif "," in item:
                shot_assign=unicode(item.split(",")[1].strip())
        self.assigns.append(JDF_Assign(assign_type=assign_type, pos_assign=pos_assign,
                        shot_assign=shot_assign, assign_comment=comment))

class JDF_Main_Array(JDF_Array):
    M1x=Coerced(int, (1500,))
    M1y=Coerced(int, (1500,))

class JDF_Pattern(Atom):
    num=Coerced(int) #Int(1)
    x=Coerced(int) #Int()
    y=Coerced(int) #Int()
    name=Unicode()

def parse_comment(line):
    comment=""
    templist=line.split(";")
    tempstr=templist[0].strip() #remove comments
    if ';' in line:
        comment=templist[1].strip()
    if line.startswith(";"):
        tempstr=""
    return tempstr, comment

class JDF_Top(Atom):
    plot=Typed(Plotter, ())
    agents=List()
    pattern_dict=Dict()
    quarter_wafer=Enum("A", "B", "C", "D")

    def distribute_coords(self, num=None):
        self.comments=["distributed main array for quarter wafer {}".format(self.quarter_wafer)]
        self.Px, self.Py, self.Qx, self.Qy=get_GLM(self.quarter_wafer)
        
        if num is None:
            num=len(self.patterns)
        coords=distribute_coords(num, self.quarter_wafer)
        for n, c in enumerate(coords):
            self.arrays[0].assigns[n].pos_assign=c
        (self.arrays[0].x_start, self.arrays[0].x_num, self.arrays[0].x_step, 
                self.arrays[0].y_start, self.arrays[0].y_num, self.arrays[0].y_step)=get_Array(self.quarter_wafer)        
        
    def show(self):
        show(*self.agents)

    def pre_plot(self):
        for p in self.agents:
            p.verts=[]
            p.make_polylist()
            self.pattern_dict[p.name]=dict(verts=p.verts[:], color=p.color, layer=p.layer, plot_sep=p.plot_sep)

        for key in self.pattern_dict:
            if self.pattern_dict[key]["plot_sep"]:
                self.plot.set_data(key, self.pattern_dict[key]["verts"], self.pattern_dict[key]["color"])

        xmin=min(b.xmin for b in self.agents)
        xmax=max(b.xmax for b in self.agents)
        ymin=min(b.ymin for b in self.agents)
        ymax=max(b.ymax for b in self.agents)
        self.plot.set_xlim(xmin, xmax)
        self.plot.set_ylim(ymin, ymax)
        self.plot.draw()

    @property
    def show_all(self):
        return True

    text=Unicode()
    output_jdf=Unicode()
    comments=List() #Unicode()
    Px=Coerced(int, (-40000,))
    Py=Coerced(int, (4000,))
    Qx=Coerced(int, (-4000,))
    Qy=Coerced(int, (40000,))

    mgn_name=Unicode("IDT")
    wafer_diameter=Coerced(int, (4,))
    write_diameter=Coerced(float, (-4.2,))

    stdcur=Coerced(int, (2,))
    shot=Coerced(int, (8,))
    resist=Coerced(int, (165,))
    arrays=ContainerList()#.tag(width='max', inside_type=jdf_array)
    patterns=ContainerList()#.tag(width='max', inside_type=jdf_pattern)
    jdis=ContainerList()

    def do_plot(self, a=None):
        if a==None:
            a=self.arrays[0]
        for s in a.assigns:
            for p in s.assign_type:
                #generate verts
                if p[0]=="P":
                    verts=[t.name for t in self.patterns if t.num==int(p[2])][0]
                elif p[0]=="A":
                    pass #do_plot array given by num
            for o in s.pos_assign:
                x_ref=a.x_start+(int(o[0])-1)*a.x_step
                y_ref=a.y_start+(int(o[1])-1)*a.x_step
                print x_ref, y_ref #offset vertices by x_ref, y_ref

    def _observe_text(self, change):
        self.jdf_parse(self.text)
        self.output_jdf=self.jdf_produce()

    @property
    def view_window(self):
        with imports():
            from e_Show import JDFView
        return JDFView(jdf=self)

    def clear_JDF(self):
        self.comments=[]
        self.arrays=[]
        self.patterns=[]
        self.jdis=[]

    def jdf_parse(self, jdf_data):
        jdf_list=jdf_data.split("\n")
        inside_path=False
        inside_layer=False
        self.clear_JDF()
        array_num=0
        for n, line in enumerate(jdf_list):
            tempstr, comment=parse_comment(line)
            if tempstr=="" and comment!="":
                self.comments.append(comment)
            if tempstr.startswith('GLMPOS'):
                self.Px, self.Py, self.Qx, self.Qy=xy_string_split(tempstr) #get P and Q mark positions
            elif tempstr.startswith('JOB'):
                mgn_name, self.wafer_diameter, self.write_diameter=tempstr.split(",") #magazine name and wafer size
                self.mgn_name=mgn_name.split("'")[1].strip()
            elif tempstr.startswith("PATH"):
                inside_path=True
            elif "LAYER" in tempstr:
                inside_layer=True
            if inside_path:
                if 'ARRAY' in tempstr:
                    if ":" in tempstr:
                        array_num=tempstr.split(":")[0] #for subarrays
                        x_start, x_num, x_step, y_start, y_num, y_step=xy_string_split(tempstr)
                        self.arrays.append(JDF_Array(array_num=array_num, x_start=x_start, x_num=x_num, x_step=x_step,
                                         y_start=y_start, y_num=y_num, y_step=y_step))
                    else:
                        x_start, x_num, x_step, y_start, y_num, y_step=xy_string_split(tempstr)
                        self.arrays.append(JDF_Main_Array(x_start=x_start, x_num=x_num, x_step=x_step,
                                                         y_start=y_start, y_num=y_num, y_step=y_step))
                elif 'ASSIGN' in tempstr:
                    self.arrays[-1].add_assign(tempstr, comment)
                elif 'CHMPOS' in tempstr:
                    M1x, M1y=tuple_split(tempstr)
                    self.arrays[-1].M1x=M1x
                    self.arrays[-1].M1y=M1y
                elif "PEND" in tempstr:
                    inside_path=False
            elif inside_layer:
                if 'END' in tempstr:
                    inside_layer=False
                elif 'STDCUR' in tempstr:
                    stdcur=tempstr.split("STDCUR")[1]
                    self.stdcur=stdcur
                elif 'SHOT' in tempstr:
                    shot=tempstr.split(',')[1]
                    self.shot=shot
                elif 'RESIST' in tempstr:
                    resist=tempstr.split('RESIST')[1]
                    self.resist=resist
                elif 'P(' in tempstr:
                    pattern_name=tempstr.split("'")[1].split(".")[0]
                    pattern_num=tempstr.split("(")[1].split(")")[0]
                    pattern_x=tempstr.split("(")[2].split(")")[0].split(",")[0]
                    pattern_y=tempstr.split("(")[2].split(")")[0].split(",")[0]
                    self.patterns.append(JDF_Pattern(num=pattern_num, x=pattern_x, y=pattern_y, name=pattern_name))
                elif tempstr.startswith('@'):
                    jdi_str=tempstr.split("'")[1].split(".jdi")[0]
                    self.jdis.append(jdi_str)

    def jdf_produce(self):
        jl=[] #jdf_data.split("\n")
        jl.append("JOB/W '{name}', {waf_diam}, {write_diam}\n".format(name=self.mgn_name,
                  waf_diam=self.wafer_diameter, write_diam=self.write_diameter))
        jl.append(";{comment}\n".format(comment=self.comments[0]))
        jl.append("GLMPOS P=({Px}, {Py}), Q=({Qx},{Qy})".format(Px=self.Px, Py=self.Py, Qx=self.Qx, Qy=self.Qy))
        jl.append("PATH")

        for n, item in enumerate(self.arrays):
            if item.array_num==0:
                jl.append("ARRAY ({x_start}, {x_num}, {x_step})/({y_start}, {y_num}, {y_step})".format(
                       x_start=self.arrays[0].x_start, x_num=self.arrays[0].x_num, x_step=self.arrays[0].x_step,
                       y_start=self.arrays[0].y_start, y_num=self.arrays[0].y_num, y_step=self.arrays[0].y_step))
                jl.append("\tCHMPOS M1=({M1x}, {M1y})".format(M1x=self.arrays[0].M1x, M1y=self.arrays[0].M1y))
            else:
                jl.append("{arr_num}: ARRAY ({x_start}, {x_num}, {x_step})/({y_start}, {y_num}, {y_step})".format(
                       arr_num=item.array_num, x_start=item.x_start, x_num=item.x_num, x_step=item.x_step,
                       y_start=item.y_start, y_num=item.y_num, y_step=item.y_step))
            for item in item.assigns:
                asgn_type="+".join(item.assign_type)
                pos_asgn=""
                for pos in item.pos_assign:
                    pos_asgn+="({x},{y}),".format(x=pos[0], y=pos[1])
                pos_asgn=pos_asgn[:-1]
                if item.shot_assign=="":
                    shot_asgn=""
                else:
                    shot_asgn=", {sa}".format(sa=item.shot_assign)
                if item.assign_comment=="":
                    asgn_comment=""
                else:
                    asgn_comment=";{ac}".format(ac=item.assign_comment)
                jl.append("\tASSIGN {asgn_type} -> ({pos_asgn}{shot_asgn}) {asgn_comment}".format(
                          asgn_type=asgn_type, pos_asgn=pos_asgn, shot_asgn=shot_asgn, asgn_comment=asgn_comment))
            jl.append("AEND\n")

        jl.append("PEND\n\nLAYER 1")

        for n, item in enumerate(self.patterns):
            jl.append("P({pnum}) '{pname}.v30' ({px},{py})".format(
                      pnum=item.num, pname=item.name, px=item.x, py=item.y))
        jl.append("\nSTDCUR {0}".format(self.stdcur))
        jl.append("SHOT A,{0}".format(self.shot))
        jl.append("RESIST {}\n".format(self.resist))

        for item in self.jdis:
            jl.append("@ '{jdi_name}.jdi'".format(jdi_name=item))
        jl.append("\nEND 1")

        return "\n".join(jl)

def jdf_parse(jdf_data):
    jdf=JDF_Top()
    jdf.jdf_parse(jdf_data)
    return jdf
    
def jdf_qw_swap(jdf_data, qw="A", num=None):
    jdf=jdf_parse(jdf_data)
    jdf.quarter_wafer=qw
    jdf.distribute_coords(num=num)
    return jdf.jdf_produce()
    
def gen_jdf_quarter_wafer(patterns, qw="A"):
    """guesses at jdf from list of patterns. patterns is a dictionary with an optional shot_mod and an optional position list?"""
    jdf=JDF_Top(quarter_wafer=qw)
    jdf.arrays.append(JDF_Main_Array())                                                        
    for n,p in enumerate(patterns):
        jdf.patterns.append(JDF_Pattern(num=n+1, name=p))
        jdf.jdis.append(p)
        jdf.arrays.append(JDF_Array(array_num=n+1,
                                    assigns=[JDF_Assign(assign_type=['P({0})'.format(n+1)],
                                                        shot_assign=patterns[p].get("shot_mod", ""),
                                                        #pos_assign=patterns[p].get("pos", [(1,1)])
                                                        assign_comment=p)]))
        jdf.arrays[0].assigns.append(JDF_Assign(assign_type=['A({0})'.format(n+1)],
                                             assign_comment=p))
    jdf.distribute_coords()
    return jdf
    



if __name__=="__main__":
    jdf_data="""JOB/W 'IDT',4,-4.2

; For exposure on YZ-cut LiNbO3, Cop+ZEP., q-wafer D
GLMPOS P=(4000,-40000),Q=(40000,-4000)   ;D wafer
PATH
ARRAY (7500,8,5000)/(-7500,8,5000)  ; D wafer
        CHMPOS M1=(1500, 1500)

	ASSIGN A(1)+A(2)+A(15)  ->  ((1,1), (7,2), (6,4)) ;D32080 with two IDTs and Squid connect
	ASSIGN A(1)+A(3)+A(15)  ->  ((2,1), (8,2), (7,4)) ;S32080 with two IDTs and Squid connect
	ASSIGN A(1)+A(4)+A(15)  ->  ((3,1), (1,3), (1,5), (2,7)) ;S32050 with two IDTs and Squid connect
	ASSIGN A(1)+A(5)+A(15)  ->  ((4,1), (2,3), (2,5), (3,7))  ;D32050 with two IDTs and Squid connect
	ASSIGN A(1)+A(6)+A(15)  ->  ((5,1), (3,3), (3,5), (4,7)) ;D9050 with two IDTs and Squid connect
	ASSIGN A(1)+A(7)+A(15)  ->  ((6,1), (4,3), (4,5), (1,8))  ;S9050 with two IDTs and Squid connect
	ASSIGN A(1)+A(8)+A(15)  ->  ((7,1), (5,3), (5,5))  ;S9080 with two IDTs and Squid connect
	ASSIGN A(1)+A(9)+A(15)  ->  ((8,1), (6,3), (6,5), (2,8))  ;D9080 with two IDTs and Squid connect
	ASSIGN A(12)+A(10)+A(15) -> ((1,2),  (7,3), (1,6)) ;D5080 with two FDTs and Squid connect
        ASSIGN A(12)+A(11)+A(15) ->  ((2,2), (1,4), (2,6))   ;D5096 with two FDTs and Squid connect
        ASSIGN A(13)+A(15)       ->  ((3,2), (2,4), (3,6))   ;IDT by itself
        ASSIGN A(14)+A(15)       ->  ((4,2), (3,4), (4,6))         ;FDT by itself
	ASSIGN A(1)+A(15)        -> ((5,2), (4,4), (5,6))     ;Two IDTs alone with squid connect
	ASSIGN A(12)+A(15)       -> ((6,2), (5,4), (1,7))          ;two FDTs alone with squid connect


AEND

1: ARRAY (-200, 2, 500)/(0, 1, 0)
	ASSIGN P(1) -> ((1,1), IDT2)
	ASSIGN P(1) -> ((2,1), IDT2)
AEND

2: ARRAY (0,1,0)/(0,1,0)
	ASSIGN P(2) -> ((1,1), D32080)
AEND

3: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(3) -> ((1,1), S32080)
AEND

4: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(4) -> ((1,1), S32050)
AEND

5: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(5) -> ((1,1), D32050)
AEND

6: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(6) -> ((1,1), D9050)
AEND

7: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(7) -> ((1,1), S9050)
AEND

8: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(8) -> ((1,1), S9080)
AEND

9: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(9) -> ((1,1), D9080)
AEND

10: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(10) -> ((1,1), D5080)
AEND

11: ARRAY (0, 1, 0)/(0, 1, 0)
	ASSIGN P(11) -> ((1,1), SCB2)
AEND

12: ARRAY (-200, 2, 500)/(0, 1, 0)
	ASSIGN P(12) -> ((1,1), FDT2)
	ASSIGN P(12) -> ((2,1), FDT2)
AEND

13: ARRAY (-200, 2, 500)/(0, 1, 0)
	ASSIGN P(1) -> ((1,1), IDT2)
AEND

14: ARRAY (-200, 2, 500)/(0, 1, 0)
	ASSIGN P(12) -> ((1,1), FDT2)
AEND

15: ARRAY (-500, 2, 1000)/(-1500, 1, 0)
	ASSIGN P(13) -> ((1,1), QBRI)
	ASSIGN P(14) -> ((2,1), QBR3)
AEND
PEND

LAYER 1
   P(1) 'cIDT9bd36ef0w96wb0.v30' (0,0)
   P(2) 'cQDT9bd3ef20w80wb0.v30' (0,0)
   P(3) 'cQDT9bs3ef20w80wb0.v30' (0,0)
   P(4) 'cQDT9bs3ef20w50wb0.v30' (0,0)
   P(5) 'cQDT9bd3ef20w50wb0.v30' (0,0)
   P(6) 'cQDT9bd9ef0w50wb0.v30' (0,0)
   P(7) 'cQDT9bs9ef0w50wb0.v30' (0,0)
   P(8) 'cQDT9bs9ef0w80wb0.v30' (0,0)
   P(9) 'cQDT9bd9ef0w80wb0.v30' (0,0)
   P(10) 'cQDT9bd5ef0w80wb0.v30' (0,0)
   P(11) 'cQDT9bd5ef0w96wb0.v30' (0,0)
   P(12) 'cIDT9bd55ef0w96wb0.v30' (0,0)

   P(13) 'cQbri.v30' (0,0)
   P(14) 'cQbr3.v30' (0,0)
   ;SPPRM 3.996,,,1,1 ;use if SHOT is 6 nm (doesn't divide 4 um which is default)
   STDCUR 2
   SHOT A,8
   RESIST 165 ; new dose from dose test TA020315A_dt with modified bias from TA060315B

@ 'idt_s.jdi'
@ 'cQDT9bd3ef20w80wb0.jdi'
@ 'cQDT9bs3ef20w80wb0.jdi'
@ 'cQDT9bs3ef20w50wb0.jdi'
@ 'cQDT9bd3ef20w50wb0.jdi'
@ 'cQDT9bd9ef0w50wb0.jdi'
@ 'cQDT9bs9ef0w50wb0.jdi'
@ 'cQDT9bs9ef0w80wb0.jdi'
@ 'cQDT9bd9ef0w80wb0.jdi'
@ 'cQDT9bd5ef0w80wb0.jdi'
@ 'scb_s.jdi'
@ 'fdt_s.jdi'
@ 'cQbri.jdi'
@ 'cQbr3.jdi'

END 1"""
    #a=Text_Editor(name="Text_Editor", dir_path="/Volumes/aref/jbx9300/job/TA150515B/IDTs", main_file="idt.jdf")
    
    class Pattern(Atom):
        name=Unicode()
        shot_mod=Unicode()
        
    b=gen_jdf_quarter_wafer(dict(IDT={"shot_mod":"IDT1"}, QDT={}), "B")    
    print b.jdf_produce()
    #b=JDF_Top(text=jdf_data)#_base()
    #b.do_plot()
    #b.jdf_parse(jdf_data)
    #print b.Px, b.Py, b.Qx, b.Qy
    #print b.arrays[0].assigns
    #print b.patterns[0].name

    #b.arrays.extend((jdf_array(), jdf_array(x_start=5), jdf_array(x_start=5), jdf_array(x_start=5)))
    #a.read_file.read()
    #print a.data
    #b.jdf_parse(a.data)
    #c=Base()
    #a.jdf.arrays.append(4.5)
    #a.jdf.arrays.append(4)

    #print a.Px
    #print [a.get_tag(aa, 'label', aa) for aa in a.all_params]
    #print a.jdf_list
    #print b.get_member('arrays').item.validate_mode[1]
    #show(b)
#    b.show()
    #print a.data
    #print b.jdf_produce()
    #print a.jdf_save_file.file_path
#/Volumes/aref/jbx9300/job/TA150515B/IDTs