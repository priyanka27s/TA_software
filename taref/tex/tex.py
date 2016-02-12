# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 17:17:26 2015

@author: thomasaref
"""

from atom.api import Atom, Unicode, Typed, List, cached_property, Float
from taref.tex.tex_backbone import (texwrap, make_table, mult_fig_start, mult_fig_end, include_image, compile_tex)

from collections import OrderedDict

from taref.core.agent import Operative
from taref.core.universal import write_text
from taref.core.log import f_top, log_debug
from enaml.qt.qt_application import QtApplication
from taref.filer.filer import Folder
from taref.filer.read_file import Read_TXT
from taref.filer.save_file import Save_TXT
from subprocess import call

from enaml import imports
with imports():
    from tex_e import TEX_Window

class File_Parser(object):
    def __init__(self, starter, stopper, inblock=False):
        self.starter=starter
        self.stopper=stopper
        self.inblock=inblock

    def __call__(self, line):
        line=line.strip()
        if self.starter in line:
            self.inblock=True
            self.local_name=line.split(self.starter)[0]
        elif self.stopper in line:
            self.inblock=False
            return True
        return self.inblock

dir_path="/Users/thomasaref/Documents/TA_software/taref/tex/test_tex/"
file_name="texxy"
class TEX(Operative):
    folder=Folder(dir_path="/Users/thomasaref/Dropbox/Current stuff/test_data")
    source_folder=Folder(base_dir="/Users/thomasaref/Dropbox/Current stuff/test_data", main_dir="", quality="")
    read_file=Typed(Read_TXT)
    save_file=Typed(Save_TXT)

    def __init__(self, **kwargs):
        source_path=kwargs.pop("source_path", None)
        super(Operative, self).__init__(**kwargs)
        self.make_input_code()
        if source_path is not None:
            self.read_file.file_path=source_path
        if self.read_file.main_dir!="":
            self.read_source()

    def _default_read_file(self):
        return Read_TXT(folder=self.source_folder, file_suffix=".tex")

    def _default_save_file(self):
        return Save_TXT(folder=self.folder, file_name="report", file_suffix=".tex", fixed_mode=True)

    local_name=Unicode()
    source_dict=Typed(OrderedDict, ())
    tex_list=List()
    output_tex=Unicode()
    input_code=Unicode()

    user_name=Unicode("Thomas Aref")
    tex_title=Unicode("Sample TA210715A46 in Speedy 3-10-15 cooldown")
    department=Unicode(r"Department of Microtechnology and Nanoscience (MC2), Chalmers University of Technology, SE-412 96 G\"oteborg, Sweden")
    tex_start=List()
    tex_end=List()
    fig_width=Float(0.49)
    caption=Unicode()

    def _default_tex_start(self):
        return [r"\documentclass[12pt,a4paper]{article}",
                r"\usepackage[top=1 in,  bottom=1 in, left=1 in, right=1 in]{geometry}",
                r"\usepackage{amsfonts,amssymb,amsmath}",
                r"\usepackage{graphicx}",
                r"\usepackage{hyperref}",
                r"\usepackage{color}",
                r"%\usepackage{tikz}",
                r"%\usepackage[siunitx]{circuitikz}",
                r"%\usepackage{cite}",
                r"\usepackage{caption}",
                r"\usepackage{subcaption}",
                r"\usepackage{rotating}",
                r"\usepackage{paralist}",
                r"\usepackage{cprotect}",
                r"",
                r"\definecolor{red}{rgb}{1, 0, 0}   %used for making comments in red color text",
                r"\definecolor{green}{rgb}{0, 0.7, 0}",
                r"\definecolor{blue}{rgb}{0, 0, 1}",
                r"\newcommand{\mc}{\textcolor{red}}  %used for making comments in red color text remove before submit",
                r"\newcommand{\mg}{\textcolor{green}}  %used for making comments in red color text remove before submit",
                r"\newcommand{\mb}{\textcolor{blue}}  %used for making comments in red color text remove before submit",
                r"\newcommand{\comment}[1]{}  %used for commenting out blocks of text remove before submit",
                r"\newcommand{\pyb}[1]{} % do nothing command for marking for python extraction",
                r"\newcommand{\pye}{} % do nothing command for python extraction end",
                r"",
                r"",
                r"\begin{document}",
                r"\author{{{0}}}".format(self.user_name),
                r"%\inst{{3}} {{{0}}}".format(self.department),
                r"\title{{{0}}}".format(self.tex_title),
                r"\maketitle",
                r"\noindent"]

    def _default_tex_end(self):
        return [r"\end{document}"]

    def _observe_output_tex(self, change):
        self.tex_list=self.output_tex.split("\n")

    def make_input_code(self):
        fb=f_top()
        with open(fb.f_code.co_filename, "r") as f:
            file_text=f.read()
        file_reader=File_Parser(".TEX_start", ".TEX_end")
        self.input_code="\n".join([line for line in file_text.split("\n") if file_reader(line)])
        self.local_name=file_reader.local_name

    def simulate_tex(self):
        locals()[self.local_name]=self
        self.tex_list=[]
        exec(self.input_code)
        self.output_tex="\n".join(self.tex_list)

    def restore_source(self):
        self.tex_list=[]
        for key in self.source_dict:
            self.tex_list.extend(self.source_dict[key])
        self.output_tex="\n".join(self.tex_list)

    def process_source(self):
        self.source_dict=OrderedDict()
        for n, line in enumerate(self.tex_list):
            line=line.strip()
            if line.startswith("\pyb"):
                index=n
                key=line.split("\pyb")[1].split("{")[1].split("}")[0].strip()
            elif line.startswith("\pye"):
                self.source_dict[key]=[item for item in self.tex_list[index:n+1]]
                self.source_dict[key].append("")
        self.restore_source()

    def read_source(self, file_path=None):
        if file_path is not None:
            self.read_file.file_path=file_path
        self.tex_list=self.read_file.read()
        self.process_source()

    def compile_tex(self):
        compile_tex(self.save_file.dir_path, self.save_file.file_name)

    def open_pdf(self):
        call(["open", self.save_file.dir_path+self.save_file.divider+self.save_file.file_name+".pdf"])

    def make_tex_file(self):
        if QtApplication.instance() is not None:
            self.process_source()
            self.simulate_tex()
        self.save_file.save(self.tex_list, write_mode="w", flush_buffer=True)
        #write_text(dir_path+file_name+".tex", self.tex_list)

    def make_and_show(self):
        self.make_tex_file()
        self.compile_tex()

    def TEX_start(self, clear=True):
        if clear:
            self.tex_list=[]
        self.extend(self.tex_start)

    def TEX_end(self):
        self.extend(self.tex_end)

    def ext(self, block_name):
        self.extend(self.source_dict[block_name])

    def add(self, inline):
        self.tex_list.append(inline)

    def extend(self, inlist):
        self.tex_list.extend(inlist)

    def make_table(self, table_values, table_format=None):
        make_table(self.tex_list, table_values, table_format)

    def include_figure(graph_gen, tex, fig_name, caption="", label="", **kwargs):
        """uses the passed function graph_gen and kwargs to generate a figure and save it to the given file path"""
        #graph_gen(**kwargs)
        file_name=graph_gen.func_code.co_filename.split("Documents")[1]
        caption="{0}  Analysis: \\verb;{1};".format(caption, file_name)
        tex.append(r"\begin{figure}[ht!]")
        tex.append(r"\centering")
        tex.append("\\includegraphics[width=\\textwidth]{{{}}}".format(fig_name))
        tex.append("\\cprotect\\caption{{{}}}".format(caption))
        tex.append("\\label{{{}}}".format(label))
        tex.append(r"\end{figure}")
        #savefig(dir_path+fig_name, bbox_inches='tight')
        #close()

    def add_mult_fig(self, graph_gen, fig_name, **kwargs):
        """adds a graph to a multi figure using the function graph_gen and given kwargs"""
        #graph_gen(**kwargs)
        file_name=graph_gen.func_code.co_filename.split("Documents")[1]
        #savefig(dir_path+fig_name, bbox_inches='tight')
        #close()

        self.tex_list.extend(["\\begin{{subfigure}}[b]{{{}\\textwidth}}".format(self.fig_width),
                   "\\includegraphics[width=\\textwidth]{{{}}}".format(fig_name),
                   #"\\cprotect\\caption{{{}}}".format(caption),
                   r"\end{subfigure}"])
        self.caption="Analysis: \\verb;{0};".format(file_name)

    def mult_fig_start(self):
        mult_fig_start(self.tex_list)

    def mult_fig_end(self, caption=None):
        if caption is not None:
            self.caption=caption
        mult_fig_end(self.tex_list, self.caption)
        self.caption=""

    def include_image(self, fig_name, caption="", label=""):
        include_image(self.tex_list, self.dir_path, fig_name, caption, label)

    @cached_property
    def view_window(self):
        return TEX_Window(agent=self)

if __name__=="__main__":
    from taref.core.shower import shower
    tx=TEX()
    #tex_source="/Users/thomasaref/Dropbox/Current stuff/Logbook/TA210715A45_cooldown1/tikztry.tex"
    #print extract_block("sam", str_list)

    #print extract_block("bob", str_list)

    tx.output_tex="""\pyb {summary}
    \section{Summary}
    This is an attempt at reducing the coupling by changing the spacing of the fingers pairs on the qubit IDT, pushing them to a higher frequency.
    The coupling appears reduced by an order of magnitude and the qubit seems to be operating as a qubit.
    Unfortunately, the qubit frequency is below the IDT listening/talking frequency so it is never directly on resonance (this could be easily fixed by having less resistive junctions). Speedy was also experiencing quite a bit of trouble with blockages so the temperature was often in the 50-80 mK range.

\pye

\pyb {second entry}
this is the second entry
\pye"""#.split("\n")

    tx.input_code="""tx.start()
tx.ext("summary")
tx.ext("second entry")

qubit_values=[[r"Qubit"                                  ,  r"{}"                             ],
                      [r"Finger type"                            ,  r"double finger"                  ],
                      [r"Number of finger pairs, $N_{pq}$"      ,  r"9"                              ],
                      [r"Overlap length, $W$"                   ,  r"25 $\mu$m"                      ],
                      [r"finger width, $a_q$"                   ,  r"80 nm"                           ],
                      [r"DC Junction Resistances"               ,  r"8.93 k$\Omega$, 9.35k$\Omega$"  ],
                      [r"Metallization ratio"                   ,  r"50\%"                           ]]


tx.add(r"\subsection{Qubit values}")
tx.make_table(qubit_values, r"|p{5 cm}|p{3 cm}|")

tx.mult_fig_start()
tx.add_mult_fig(tx.add_mult_fig, "test_colormap_plot.png")
tx.mult_fig_end()
tx.end()"""
    tx.process_source()
    #tx.make_input_tex()
    print tx.source_dict
    if 0:
        qubit_values=[[r"Qubit"                                  ,  r"{}"                             ],
                      [r"Finger type"                            ,  r"double finger"                  ],
                      [r"Number of finger pairs, $N_{pq}$"      ,  r"9"                              ],
                      [r"Overlap length, $W$"                   ,  r"25 $\mu$m"                      ],
                      [r"finger width, $a_q$"                   ,  r"80 nm"                           ],
                      [r"DC Junction Resistances"               ,  r"8.93 k$\Omega$, 9.35k$\Omega$"  ],
                      [r"Metallization ratio"                   ,  r"50\%"                           ]]


        tx.add(r"\subsection{Qubit values}")
        tx.make_table(qubit_values, r"|p{5 cm}|p{3 cm}|")

    shower(tx)