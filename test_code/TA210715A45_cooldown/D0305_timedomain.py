# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 10:46:49 2016

@author: thomasaref
"""

from TA45_fundamental import TA45_Read, TA45_Fund, qdt
from atom.api import Typed, Unicode, Float, observe, FloatRange
from h5py import File
from taref.core.universal import Array
from numpy import float64, linspace, shape, reshape, squeeze, mean, angle, absolute, array
from taref.core.atom_extension import tag_Property, set_tag, private_property
from taref.physics.units import dB
from taref.plotter.fig_format import Plotter
from taref.core.shower import shower
from taref.core.agent import Operative
from scipy.optimize import leastsq # Levenberg-Marquadt Algorithm #


set_tag(qdt, "flux_factor", log=False)

class Fitter(Operative):
    base_name="fitter"

class Fitter1(Fitter):
     offset=FloatRange(-1.0, 1.0, -0.036).tag(tracking=True)
     flux_factor=FloatRange(0.01, 1.0, qdt.flux_factor).tag(tracking=True)

     @tag_Property(plot=True, private=True)
     def flux_parabola(self):
        return qdt.call_func("flux_parabola", voltage=a.yoko, offset=self.offset, flux_factor=self.flux_factor, Ec=qdt.Ec)

     @observe("offset", "flux_factor")
     def update_plot(self, change):
         if change["type"]=="update":
             self.get_member("flux_parabola").reset(self)
             b.plot_dict["magabs_flux"].clt.set_xdata(self.flux_parabola*1e-9)
             b.draw()

class Lyzer(TA45_Fund):
    base_name="lyzer"

    @private_property
    def main_params(self):
        return ["comment", "rt_atten", "rt_gain", "probe_frq", "probe_pwr", "actual_pwr"]

    rd_hdf=Typed(TA45_Read)

    comment=Unicode().tag(read_only=True, spec="multiline")

    rt_atten=Float(40)

    rt_gain=Float(23*2)

    time=Array().tag( plot=True, label="Time")
    yoko=Array().tag(unit="V", plot=True, label="Yoko")
    Magcom=Array().tag(private=True)

    probe_frq=Float().tag(unit="GHz", label="Probe frequency", read_only=True)
    probe_pwr=Float().tag(label="Probe power", read_only=True, display_unit="dBm/mW")

    @tag_Property(display_unit="dBm/mW", label="Power to sample")
    def actual_pwr(self):
        return self.probe_pwr-self.fridge_atten-self.rt_atten

    @tag_Property(display_unit="dB", plot=True)
    def MagdB(self):
        return self.Magcom[:, :]/dB

    @tag_Property(plot=True)
    def Phase(self):
        return angle(self.Magcom[:, :])#-mean(self.Magcom[:, 297:303], axis=1, keepdims=True))

    @tag_Property( plot=True)
    def MagAbs(self):
        #return absolute(self.Magcom[:, :])
        return absolute(self.Magcom[:, :])#-mean(self.Magcom[:, 2500:2501], axis=1, keepdims=True))


    def _default_rd_hdf(self):
        return TA45_Read(main_file="Data_0305/S1A1_TA45_time_flux_sweep_long.hdf5")

    def read_data(self):
        with File(self.rd_hdf.file_path, 'r') as f:
            #print f["Traces"].keys()
            self.comment=f.attrs["comment"]
            #print f["Instrument config"]["Anritsu 68377C Signal generator - GPIB: 8, Pump3 at localhost"].attrs.keys()
            self.probe_frq=f["Instrument config"]["Anritsu 68377C Signal generator - GPIB: 8, Pump3 at localhost"].attrs["Frequency"]
            self.probe_pwr=f["Instrument config"]["Anritsu 68377C Signal generator - GPIB: 8, Pump3 at localhost"].attrs["Power"]

            #print f["Data"]["Channel names"][:]
            Magvec=f["Traces"]["Digitizer 1 - Trace"]#[:]
            data=f["Data"]["Data"]
            print shape(data)
#
            self.yoko=data[:,0,0].astype(float64)
            tstart=f["Traces"]['Digitizer 1 - Trace_t0dt'][0][0]
            tstep=f["Traces"]['Digitizer 1 - Trace_t0dt'][0][1]
            #print shape(Magvec)
            sm=shape(Magvec)[0]
            sy=shape(data)
            s=(sm, sy[0], sy[2])
            print s
            Magcom=Magvec[:,0,:]+1j*Magvec[:,1,:]
            Magcom=reshape(Magcom, s, order="F")
            self.time=linspace(tstart, tstart+tstep*(sm-1), sm)
            #print shape(Magcom)
            Magcom=squeeze(Magcom)
            self.Magcom=Magcom.transpose()
            #Magabs=Magcom[:, :, :]-mean(Magcom[:, 197:200, :], axis=1, keepdims=True)


a=Lyzer(name="D0223_timedomain")
a.read_data()
c=Fitter1()
b=Plotter()
def magdB_colormesh():
    b.colormesh("magdB", a.time*1e6, a.yoko,  a.MagdB)
    #b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
    #b.set_ylim(4.4e9, 4.5e9)
    b.xlabel="Yoko (V)"
    b.ylabel="Frequency (Hz)"
    b.title="Reflection fluxmap"

def magabs_colormesh():
    flux_over_flux0=qdt.call_func("flux_over_flux0", voltage=a.yoko, offset=c.offset, flux_factor=c.flux_factor)

    b.colormesh("magabs",  a.time*1e6, flux_over_flux0[:-3], a.MagAbs[:-3])
    #b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
    #b.set_ylim(4.4e9, 4.5e9)
    b.xlabel="Time (us)"
    b.ylabel="Magnitude (abs)"
    b.title="Reflection vs time"

def phase_colormesh():
    b.colormesh("phase", a.yoko, a.frequency, a.Phase)
    b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
    b.set_ylim(4e9, 5e9)
    b.xlabel="Yoko (V)"
    b.ylabel="Frequency (Hz)"
    b.title="Reflection fluxmap"

def magabs_cs():
    b.line_plot("magabs_cs", c.flux_parabola, mean(a.MagAbs[58:59, :], axis=0))
    #b.line_plot("flux_parabola", c.yoko, c.flux_parabola, color="orange", alpha=0.4)
    #b.set_xlim(0, 7e9)
    #b.set_ylim(0, 0.02)

def magabs_cs2():
    b.line_plot("magabs_cs", a.time*1e6, a.MagAbs[ 0, :], label="Off resonance")
    b.line_plot("magabs_cs2", a.time*1e6, a.MagAbs[181, :], label="On resonance")
    b.xlabel="Time (us)"
    b.ylabel="Magnitude (abs)"
    b.title="Reflection time cross section"

def time_speed():
    print qdt.vf
    t=array([8.7e-8, 2.64e-7, 3.79e-7, 4.35e-7, 6.6e-7])-8.7e-8
    b.scatter_plot("spd", t*1e6, [0.0, 600.0, 1000.0, 1200.0, 2000.0], label="Reflections")
    b.line_plot("spd_fit", t*1e6,  (t*qdt.vf)*1e6, label="(3488 m/s)t")

def magabs_cs_fit():
    b.line_plot("magabs_flux", c.flux_parabola[:-3]*1e-9, mean(a.MagAbs[:-3, 76:90], axis=1), label="first reflection")
    #b.vline_plot('freq', 4.4622)
    b.line_plot("magabs_flux", c.flux_parabola[:-3]*1e-9, mean(a.MagAbs[:-3, 109:230], axis=1), label="first transmission")

    def lorentzian(x,p):
        return p[2]*(1.0-1.0/(1.0+((x-p[1])/p[0])**2))+p[3]

    def residuals(p,y,x):
        err = y - lorentzian(x,p)
        return err

    p = [20e6,4.5e9, -0.002, 0.002]

    pbest = leastsq(residuals,p,args=(mean(a.MagAbs[108:231, 76:90], axis=1), c.flux_parabola[108:231]), full_output=1)
    best_parameters = pbest[0]
    print best_parameters
    b.line_plot("lorentzian", c.flux_parabola[108:231]*1e-9, lorentzian(c.flux_parabola[108:231],best_parameters), label="fit 1st R")

    #def lorentzian_sq(x,p):
    #    return p[2]*(1.0-1.0/(1.0+((x-p[1])/p[0])**2))+p[3]

    #def residuals_sq(p,y,x):
    #    err = y - lorentzian_sq(x,p)
    #    return err

    p = [20e6,4.5e9, -0.002, 0.0022]

    pbest = leastsq(residuals, p, args=(mean(a.MagAbs[108:231, 109:230], axis=1), c.flux_parabola[108:231]), full_output=1)
    best_parameters = pbest[0]
    print pbest[0]
    b.line_plot("lorentzian", c.flux_parabola[108:231]*1e-9,  lorentzian(c.flux_parabola[108:231],best_parameters), label="fit 1st T")

    b.xlabel=" Qubit Frequency (GHz)"
    b.ylabel="Magnitude (abs)"
    b.title="Reflection vs qubit frequency cross sections"

    class Fitter2(Fitter):
      frequency=FloatRange(4.4, 4.5, 4.4622).tag(tracking=True)
      offset=FloatRange(0.00, 1.0e-2, 0.0).tag(tracking=True)
      height=FloatRange(0.00, 1.0e-2, 0.0).tag(tracking=True)
      width=FloatRange(10.0, 500.0, 50.0).tag(tracking=True)

      @tag_Property(plot=True, private=True)
      def lorenz(self):
         return lorentzian(c.flux_parabola, [self.width*1e6, self.frequency*1e9, self.height, self.offset])

      @observe("frequency", "offset", "width", "height")
      def update_plot(self, change):
         if change["type"]=="update":
             self.get_member("lorenz").reset(self)
             b.plot_dict["lorenz"].clt.set_ydata(self.lorenz)
             b.draw()
    #d=Fitter2()
    #bp=[  7.11932128e+07,   4.44542932e+09,   1.62596541e-04,  2.26753425e-05]
    #fit2 = lorentzian(c.flux_parabola, bp)
    #b.line_plot("lorenz", c.flux_parabola*1e-9, fit2)

if __name__=="__main__":
    #magdB_colormesh()
    #magabs_cs()
    #magabs_colormesh()
    magabs_cs_fit()
    #b.line_plot("magabs_flux", c.flux_parabola, mean(a.MagAbs[:, 30:40], axis=1))


    #magabs_cs2()
    #time_speed()
    #b.savefig(dir_path="/Users/thomasaref/Dropbox/Current stuff/test_data/")
    shower(b)


