# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 10:46:49 2016

@author: thomasaref
"""

from TA88_fundamental import TA88_Read, TA88_Fund, qdt
from atom.api import Typed, Unicode, Float, observe, FloatRange, Int
from h5py import File
from taref.core.universal import Array
from numpy import float64, linspace, shape, reshape, squeeze, mean, angle, absolute
from taref.core.atom_extension import tag_Property
from taref.physics.units import dB
from taref.plotter.fig_format import Plotter
from taref.core.shower import shower
from taref.core.agent import Operative

class Fitter(Operative):
     offset=FloatRange(-1.0, 1.0, -0.03).tag(tracking=True)
     flux_factor=FloatRange(0.01, 1.0, 0.2945).tag(tracking=True)

     @tag_Property(plot=True, private=True)
     def flux_parabola(self):
        flux_over_flux0=qdt.call_func("flux_over_flux0", voltage=self.yoko, offset=self.offset, flux_factor=self.flux_factor)
        Ej=qdt.call_func("Ej", flux_over_flux0=flux_over_flux0)
        return qdt._get_fq(Ej, qdt.Ec)
         #return qdt.flux_parabola(voltage=self.yoko, offset=self.offset, flux_factor=self.flux_factor)

     yoko=Array().tag(unit="V", plot=True, label="Yoko", private=True)

     plotter=Typed(Plotter).tag(private=True)

     @observe("offset", "flux_factor")
     def update_plot(self, change):
         if change["type"]=="update":
             self.get_member("flux_parabola").reset(self)
             self.plotter.plot_dict["flux_parabola"].clt.set_ydata(self.flux_parabola)
             self.plotter.draw()

     #powind=Int(1)

     #def _observe_powind(self, change):
     #   if change["type"]=="update":
     #       a.powind=self.powind
     #       a.get_member("MagAbs").reset(a)
     #       if "magabs" in b.plot_dict:
     #           b.plot_dict["magabs"].clt.set_array(a.MagAbs)

class Lyzer(TA88_Fund):
    rd_hdf=Typed(TA88_Read)

    comment=Unicode().tag(read_only=True, spec="multiline")

    rt_atten=Float(40)

    rt_gain=Float(23*2)

    frequency=Array().tag(unit="GHz", plot=True, label="Frequency")
    yoko=Array().tag(unit="V", plot=True, label="Yoko")
    Magcom=Array().tag(private=True)
    pwr=Array()

    probe_frq=Float().tag(unit="GHz", label="Probe frequency", read_only=True)
    probe_pwr=Float().tag(label="Probe power", read_only=True, display_unit="dBm/mW")

    powind=Int(1)


    @tag_Property(display_unit="dB", plot=True)
    def MagdB(self):
        return self.Magcom[:, self.powind, :]/dB

    @tag_Property(plot=True)
    def Phase(self):
        return angle(self.Magcom[:, self.powind, :]-mean(self.Magcom[:, self.powind, 297:303], axis=1, keepdims=True))

    @tag_Property( plot=True)
    def MagAbs(self):
        #return absolute(self.Magcom[:, :])
        return absolute(self.Magcom[:, self.powind, :]-mean(self.Magcom[:, self.powind, 0:1], axis=1, keepdims=True))



    def _default_rd_hdf(self):
        return TA88_Read(main_file="Data_0221/S4A4_TA88_pwrswp.hdf5")

    def read_data(self):
        with File(self.rd_hdf.file_path, 'r') as f:
            print f["Traces"].keys()
            self.comment=f.attrs["comment"]
            print f["Instrument config"].keys()
            self.probe_frq=f["Instrument config"]['Rohde&Schwarz Network Analyzer - IP: 169.254.107.192, RS VNA at localhost'].attrs["Start frequency"]
            self.probe_pwr=f["Instrument config"]['Rohde&Schwarz Network Analyzer - IP: 169.254.107.192, RS VNA at localhost'].attrs["Output power"]
            print f["Instrument config"]['Rohde&Schwarz Network Analyzer - IP: 169.254.107.192, RS VNA at localhost'].attrs
#
            print f["Data"]["Channel names"][:]
            Magvec=f["Traces"]["RS VNA - S21"]#[:]
            data=f["Data"]["Data"]
            print shape(data)
#
            self.yoko=data[0,1,:].astype(float64)
            self.pwr=data[:,0,0].astype(float64)

            print self.yoko
            fstart=f["Traces"]['RS VNA - S21_t0dt'][0][0]
            fstep=f["Traces"]['RS VNA - S21_t0dt'][0][1]
            print shape(Magvec)
            sm=shape(Magvec)[0]
            sy=shape(data)
            s=(sm, sy[0], sy[2])
            print s
            Magcom=Magvec[:,0,:]+1j*Magvec[:,1,:]
            Magcom=reshape(Magcom, s, order="F")
            self.frequency=linspace(fstart, fstart+fstep*(sm-1), sm)
            print shape(Magcom)
            self.Magcom=squeeze(Magcom)
            #Magabs=Magcom[:, :, :]-mean(Magcom[:, 197:200, :], axis=1, keepdims=True)

if __name__=="__main__":
    a=Lyzer()
    a.read_data()
    c=Fitter()
    c.yoko=a.yoko[:]
    b=Plotter()
    def magdB_colormesh():
        b.colormesh("magdB", a.yoko, a.frequency, a.MagdB)
        b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
        b.set_ylim(4.4e9, 4.55e9)
        b.xlabel="Yoko (V)"
        b.ylabel="Frequency (Hz)"
        b.title="Reflection fluxmap"

    def magabs_colormesh():
        b.colormesh("magabs", a.yoko, a.frequency, a.MagAbs)
        b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
        b.set_ylim(4.4e9, 4.55e9)
        b.xlabel="Yoko (V)"
        b.ylabel="Frequency (Hz)"
        b.title="Reflection fluxmap"

    def magabs_allcolormesh():
        for pwi in range(11):
            a.powind=pwi
            a.get_member("MagAbs").reset(a)
            b.colormesh("magabs {}".format(a.pwr[a.powind]-a.rt_atten-a.fridge_atten), a.yoko, a.frequency, a.MagAbs)
        b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
        b.set_ylim(4.4e9, 4.55e9)
        b.xlabel="Yoko (V)"
        b.ylabel="Frequency (Hz)"
        b.title="Reflection fluxmap"

    c.plotter=b

    def phase_colormesh():
        b.colormesh("phase", a.yoko, a.frequency, a.Phase)
        b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
        b.set_ylim(4e9, 5e9)
        b.xlabel="Yoko (V)"
        b.ylabel="Frequency (Hz)"
        b.title="Reflection fluxmap"

    def magabs_cs():
        for pwi in range(11):
            a.powind=pwi
            a.get_member("MagAbs").reset(a)
            b.line_plot("magabs_cs", c.flux_parabola, a.MagAbs[280, :], label="{}".format(a.pwr[a.powind]-a.rt_atten-a.fridge_atten))

    def satatt():
        powsat=[]
        for pwi in range(11):
            a.powind=pwi
            a.get_member("MagAbs").reset(a)
            data=a.MagAbs[280, :]
            powsat.append(max(data)-min(data))
        b.line_plot("powsat", a.pwr, powsat) #a.MagAbs[280, :], label=str(a.pwr[a.powind]))

        #b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
        #b.set_xlim(0, 7e9)
        #b.set_ylim(0, 0.02)

    #magdB_colormesh()
    magabs_cs()
    #magabs_colormesh()
    #magabs_allcolormesh()
    #satatt()
    shower(b)


