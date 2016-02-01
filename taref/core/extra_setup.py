# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 22:29:11 2016

@author: thomasaref
"""
from atom.api import Property, Callable, Range, FloatRange#, Int, Float
from atom_extension import log_func, tag_Property, make_instancemethod, get_tag, set_tag, UNIT_DICT
from taref.core.log import log_debug

def property_func(func):
    name_list=func.func_name.split("_get_")
    if name_list[0]=="":
        name=name_list[1]
    else:
        name=name_list[0]
    new_func=log_func(func, name)
    new_func.fset_list=[]
    def setter(set_func):
        s_func=property_func(set_func)
        new_func.fset_list.append(s_func)
        return s_func
    new_func.setter=setter
    return new_func

class tagged_property(tag_Property):
    def __call__(self, func):
        return super(tagged_property, self).__call__(property_func(func))

def param_decider(obj, value, param, pname):
    log_debug(param, pname)
    if param==pname:
        return value
    return getattr(obj, param)

def fset_maker(obj, fget, name):
    def setit(obj, value):
        for fset in fget.fset_list:
            argvalues=[param_decider(obj, value, param, name) for param in fset.run_params]
            setattr(obj, fset.pname, fset(obj, *argvalues))
    return setit

def _setup_property_fs(self, param, typer):
    """sets up property_f's pointing obj at self and setter at functions decorated with param.fget.setter"""
    if typer==Property:
        fget =getattr(self.get_member(param), "fget")
        if getattr(fget, "fset_list", []) != []:
            self.get_member(param).setter(fset_maker(self, fget, param))

def _setup_callables(self, param, typer):
    if typer == Callable:
        func=getattr(self, param)
        if func is not None:
            #func.log_message=get_tag(self, param, "log_message", "RAN: {0} {1}")
            make_instancemethod(self, func)

def _setup_ranges(self, param, typer):
    """autosets low/high tags for Range and FloatRange"""
    if typer in [Range, FloatRange]:
        set_tag(self, param, low=self.get_member(param).validate_mode[1][0], high=self.get_member(param).validate_mode[1][1])

def _setup_units(self, param, typer):
        """autosets units using unit_dict"""
        #if typer in [Int, Float, Range, FloatRange, Property]:
        if not get_tag(self, param, "unit") is None and get_tag(self, param, "unit_factor") is None and get_tag(self, param, "unit_func") is None:
            unit=get_tag(self, param, "unit", "")#[0]
            if unit in self.unit_dict:
                unit_d=getattr(self, "unit_dict", UNIT_DICT)[unit]
                if isinstance(unit_d, int) or isinstance(unit_d, float):
                    set_tag(self, param, unit_factor=unit_d)
                else:
                    set_tag(self, param, unit_func=unit_d)
def extra_setup(self, param, typer):
    """sets up property_fs, ranges, and units"""
    _setup_callables(self, param, typer)
    _setup_property_fs(self, param, typer)
    _setup_ranges(self, param, typer)
    _setup_units(self, param, typer)