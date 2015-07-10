# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 21:52:51 2015

@author: thomasaref

A collection of for using my dynamic view with various objects. also defines common backbone
"""

from inspect import getmembers
from atom.api import Atom, Enum, Range, FloatRange, Int, Float, Callable, Unicode, Bool, List
from functools import wraps
from LOG_functions import log_info
from numpy import shape, ndarray
from enaml.application import deferred_call
from threading import Thread
from types import FunctionType


def get_member(obj, name):
    """returns a member if get_member exists and the attribute itself if it does not"""
    if hasattr(obj, "get_member"):
        return obj.get_member(str(name))
    return getattr(obj, str(name))

def members(obj):
    """returns members if defined, e.g. Atom class, or attributes whose names don't start with _"""
    if hasattr(obj, "members"):
        return obj.members()
    return dict([mem for mem in getmembers(obj) if mem[0][0]!="_"])
    
def get_metadata(obj, name):
    """returns the metadata of a member if it exists and generates an appropriately indexed empty dictionary if it does not"""
    if isinstance(obj, Atom):
        member=obj.get_member(name)
        if member.metadata is None:
            member.metadata={}
        return member.metadata
    if not hasattr(obj, "_metadata"):
        obj._metadata={name:{}}
    if obj._metadata.get(name, None) is None:
        obj._metadata[name]={}
    return obj._metadata[name]

def set_tag(obj, name, **kwargs):
    """sets the tag of a member using Atom's built in tag functionality or
    the object wide metadata dictionary for non-Atom objects"""
    if isinstance(obj, Atom):
        member=obj.get_member(name)
        member.tag(**kwargs)
    else:
        metadata=get_metadata(obj, name)
        metadata.update(**kwargs)

def set_all_tags(obj, **kwargs):
    """set all parameters tags using keyword arguments"""
    for param in get_all_params(obj):
        set_tag(obj, param, **kwargs)

def get_tag(obj, name, key, none_value=None):
    """returns the tag key of a member name an returns none_value if it does not exist"""
    metadata=get_metadata(obj, name)
    return metadata.get(key, none_value)

def get_all_tags(obj, key, key_value=None, none_value=None, search_list=None):
    """returns a list of names of parameters with a certain key_value"""
    if search_list is None:
        search_list=members(obj)
    if key_value==None:
        return [x for x in search_list if none_value!=get_tag(obj, x, key, none_value)]
    return [x for x in search_list if key_value==get_tag(obj, x, key, none_value)]

def get_map(obj, name, item=None, none_map={}):
    """gets the mapped value specified by dictionary mapping and uses none_map if it doesn't exist"""
    if item is None:
        item=getattr(obj, name)
    mapping=get_mapping(obj, name, none_map) #get_tag(obj, name, "mapping", none_map)
    if get_tag(obj, name, "map_type")=="attribute":
        item=getattr(obj, item)
    return mapping.get(item, item)


#def find_targets(dock_items, target_items=[]):
#    names=(o.name for o in dock_items)
#    targets=(o.name for o in target_items)
#    overlap=list(set(targets).intersection(names))
#    return overlap
    
def get_mapping(obj, name, none_map={}):
    mapping=get_tag(obj, name, 'mapping')
    if isinstance(mapping, dict): 
        #if mapping is already defined, just return it
        return mapping
    if isinstance(mapping, list):
        return {}
    if isinstance(mapping, basestring):
        #if mapping is defined as the name of a property, update to a dictionary and return it
        mapping=getattr(obj, mapping)
        set_tag(obj, name, mapping=mapping, map_type="property")
        return mapping
    items=obj.get_member(name).items
    if sorted(items)==sorted(set(items).intersection(members(obj))):
        #if every name in items maps to a member, update to a dictionary mapping to the members
        mapping=list(items) #dict(zip(items, [getattr(obj, item) for item in items]))
        set_tag(obj, name, mapping=mapping, map_type="attribute")
        return {}
    #if nothing else, set mapping to none_map and return
    set_tag(obj, name, mapping=none_map, map_type="none_map")
    return none_map

def get_map_type(obj, name):
    """makes sure to get mapping to update map_type before returning map_type"""
    get_mapping(obj, name)
    return get_tag(obj, name, "map_type")

def get_inv(obj, name, value):
    """returns the inverse mapped value (meant for an Enum)"""
    if get_tag(obj, name, 'inv_map') is None:
        mapping=get_mapping(obj, name) #self.get_tag(name, 'mapping', {getattr(self, name) : getattr(self, name)})
        set_tag(obj, name, inv_map={v:k for k, v in mapping.iteritems()})
    return get_tag(obj, name, 'inv_map').get(value, value)

def get_type(obj, name):
    """returns type of member with given name"""
    typer=type(get_member(obj, name))
    return get_tag(obj, name, "typer", typer)

def get_reserved_names(obj):
    """reserved names not to perform standard logging and display operations on,
           i.e. members that are tagged as private and will behave as usual Atom members"""
    return get_all_tags(obj, "private", True)    

def get_all_params(obj):
    """all members that are not tagged as private, i.e. not in reserved_names and will behave as agents"""
    return get_all_tags(obj, key="private", key_value=False, none_value=False)

def get_all_main_params(obj):
    """all members in all_params that are not tagged as sub.
     Convenience function for more easily custom defining main_params in child classes"""
    return get_all_tags(obj, 'sub', False, False, get_all_params(obj))

def get_main_params(obj):
    """returns main_params if it exists and all possible main params if it does not"""
    if hasattr(obj, "main_params"):
        return obj.main_params
    return get_all_main_params(obj)

def passf(*args, **kwargs):
    """do nothing function for when function does not exist"""
    pass

def get_attr(obj, name, none_value=None):
    """returns the attribute if the obj has it and the none_value if it does not"""
    if hasattr(obj, str(name)):
        return getattr(obj, name)
    return none_value
    
class fakeboss(object):
    abort=False
    busy=False
    progress=0

def get_boss(obj):
    """link to boss of object and uses base boss if none exists. boss is assumed to have abort and busy attributes"""
    return get_attr(obj, "boss", fakeboss())

def get_run_params(f, include_self=False):
    """returns names of parameters a function will call"""
    if hasattr(f, "run_params"):
        argnames=f.run_params
    else:
        argcount=f.func_code.co_argcount
        argnames=list(f.func_code.co_varnames[0:argcount])
    if not include_self and "self" in argnames:
        argnames.remove("self")
    return argnames
    
def code_caller(topdog, code, **kwargs):
    result=code(**kwargs)
    try:
        deferred_call(setattr, topdog, 'busy', False)
        deferred_call(setattr, topdog, 'progress', 0)
        deferred_call(setattr, topdog, 'abort', False)
    except RuntimeError:
        topdog.busy=False
        topdog.progress=0
        topdog.abort=False
    return result
 
def do_it_if_needed(topdog, code, **kwargs):
    if not topdog.busy:
        topdog.busy = True
        thread = Thread(target=code_caller, args=(topdog, code), kwargs=kwargs)
        thread.start()
            
def run_func(obj, name, **kwargs):
    """runs a function which is an attribute of an object. Auto-includes the obj itself depending on the types of function
    if kwargs are specified, it will set the attribtues of an object to those values (names need to match).
    if the object boss has the GUI threadsafe method do_it_if_needed, it will preferentially call that over the function itself"""
    f=getattr(obj, name)
    run_params=get_run_params(f)
    if get_type(obj, name) in (Callable, FunctionType):
        kwargs["self"]=obj
    for item in run_params:
        #if item=="self":
        
        #else:    
            if item in kwargs:
                setattr(obj, item, kwargs[item])
            else:
                value=getattr(obj, item)
                value=set_value_map(obj, item, value)
                kwargs[item]=value
    do_it_if_needed(get_boss(obj), f, **kwargs)                

def updater(fn):
    """a decorator to stop infinite recursion. also stores run_params as an attribute"""
    @wraps(fn)
    def updfunc(self, change):
        if not hasattr(updfunc, "callblock"):
            updfunc.callblock=""
        if change["name"]!=updfunc.callblock: # and change['type']!='create':
            updfunc.callblock=change["name"]
            fn(self, change)
            updfunc.callblock=""
    updfunc.run_params=get_run_params(fn)
    return updfunc
    
def log_func(fn):
    """a decorator that logs when a function is run. also stores run_params as an attribute"""
    @wraps(fn)
    def logf(*args, **kwargs):
        log_info("RAN: {name}".format(name=fn.func_name))
        fn(*args, **kwargs)
    logf.run_params=get_run_params(fn, True)
    return logf
   
#def get_args(obj, name):
#    f=getattr(obj, name)
#    run_params=get_run_params(f, True)
#    arglist=[]
#    if "self" in run_params:
#        if get_type(obj, name) in (Callable, FunctionType):
#            arglist.append(obj)
#        run_params.remove("self")
#    arglist.extend([getattr(obj, an) for an in run_params])
#    return arglist
    
def get_name(obj, default_name="NO NAME"):
    if hasattr(obj, "name"):
        return obj.name
    return default_name
 
def lowhigh_check(obj, name, value):
    """can specify low and high tags to keep float or int within a range."""
    if type(value) in (float, int):
        metadata=get_metadata(obj, name)
        if 'low' in metadata:
            if value<metadata['low']:
                return metadata['low']
        if 'high' in metadata:
            if value>metadata.get['high']:
                return metadata['high']
    return value

def set_value_map(obj, name, value):
    """checks floats and ints for low/high limits and automaps an Enum when setting. Not working for List?"""
    value=lowhigh_check(obj, name, value)
    if get_type(obj, name)==Enum:
        return get_map(obj, name, value) 
    return value

def data_save(obj, name, value):
    """data saving. does nothing if data_save is not defined"""
    get_attr(obj, "data_save", passf)(name, value)
    
def set_log(obj, name, value):
   """called when parameter of given name is set to value i.e. instr.parameter=value. Customized messages for different types. Also saves data"""
   if get_tag(obj, name, 'log', True):
       label=get_tag(obj, name, 'label', name)
       unit=get_tag(obj, name, 'unit', "")
       obj_name=get_name(obj)
       if get_type(obj, name)==Enum:
           log_info("Set {instr} {label} to {value} ({map_val})".format(
                 instr=obj_name, label=label, value=value,
                 map_val=get_map(obj, name, value)))
       #elif get_type(obj, name) in (Callable, type(dummyf)):
       #    log_info("Set {instr} {label} to {length} list".format(
       #        instr=obj_name, label=label, length=shape(getattr(obj, name))))
       elif type(value)==list:
           log_info("Set {instr} {label} to {length} list".format(
               instr=obj_name, label=label, length=shape(getattr(obj, name))))
       elif type(value)==ndarray:
           log_info("Set {instr} {label} to {length} array".format(
               instr=obj_name, label=label, length=shape(value)))
       elif type(value)==dict:
           log_info("Set {instr} {label}".format(instr=obj_name, label=label))
       elif type(value)==basestring:
           log_info("Set {instr} {label} to {length} string".format(instr=obj_name, label=label, length=len(value)))
       elif type(value)==float:
           unit_factor=get_tag(obj, name, 'unit_factor', 1.0)
           log_info("Set {instr} {label} to {value} {unit}".format(
                             instr=obj_name, label=label, value=value/unit_factor, unit=unit))
       elif type(value)==int:
           unit_factor=get_tag(obj, name, 'unit_factor', 1)
           log_info("Set {instr} {label} to {value} {unit}".format(
                             instr=obj_name, label=label, value=value/unit_factor, unit=unit))
       else:
           log_info("Set {instr} {label} to {value}".format(
                             instr=obj_name, label=label, value=value, unit=unit))
   data_save(obj, name, value)

#
#    def copy(self):
#        tempbase=type(self)()
#        for name in self.all_params:
#            setattr(tempbase, name, getattr(self, name))
#        for name in self.reserved_names:
#            setattr(tempbase, name, getattr(self, name))
#        return tempbase
#

unit_dict=dict(u=1.0e-6, m=1.0e-3, c=1.0e-2, 
              G=1.0e9, M=1.0e6, k=1.0e3)


           
class Backbone(Atom):
    """underlying backbone class that implements all universal aspects except those boss related"""
    name=Unicode().tag(private=True, desc="name of agent. A default will be provided if none is given")
    #title=Unicode().tag(private=True, desc="optional title/label")
    desc=Unicode().tag(private=True, desc="optional description of agent")
    full_interface=Bool(False).tag(private=True, desc="agent wide GUI control")
    plot_all=Bool(False).tag(private=True, desc="agent wide override for plotting")
    view=Enum("Auto").tag(private=True, desc="can be overwritten in children to allow custom views")
    main_params=List().tag(private=True, desc="main parameters: allows control over what is displayed and in what order")

    @property
    def base_name(self):
        """default base name of base if no name is given. can be overwritten in subclasses"""
        return "base"

    @property
    def reserved_names(self):
        """reserved names not to perform standard logging and display operations on,
           i.e. members that are tagged as private and will behave as usual Atom members"""
        return get_reserved_names(self) #get_all_tags("private", True)

    @property
    def all_params(self):
        """all params to perform logging and display operations on"""
        return get_all_params(self)

    @property
    def all_main_params(self):
        """all_params that are not tagged as sub"""
        return get_all_main_params(self)

    def _default_main_params(self):
        """defaults to all members in all_params that are not tagged as sub.
        Can be overwritten to allow some minimal custom layout control,
        e.g. order of presentation and which members are shown. Use self.all_main_params to get a list of
        all members that could be in main_params"""
        return self.all_main_params

    def get_map(self, name, item=None, none_map={}):
        return get_map(self, name=name, item=item, none_map=none_map)
        
    def run_func(self, name, **kwargs):
        return run_func(self, name, **kwargs)
#
#    def func2log(self, name, cmdstr):
#        """returns cmd associated with cmdstr in tag and converts it to a log if it isn't already.
#          returns None if cmdstr is not in metadata"""
#        cmd=self.get_tag(name, cmdstr)
#        if not isinstance(cmd, func_log) and cmd is not None:
#            cmd=func_log(cmd)
#            self.set_tag(name, **{cmdstr:cmd})
#        return cmd
#
#    def get_run_params(self, name, key, notself=False, none_value=[]):
#        """returns the run parameters of get_cmd and set_cmd. Used in GUI"""
#        cmd=self.func2log(name, key)
#        if cmd is None:
#            return none_value
#        else:
#            run_params=cmd.run_params[:]
#            if notself:
#                if name in run_params:
#                    run_params.remove(name)
#            return run_params
#
    def _observe_plot_all(self, change):
        """if instrument plot_all changes, change all plot tags of parameters"""
        if change['type']!='create':
            set_all_tags(self, plot=self.plot_all)

    def _observe_full_interface(self, change):
        """if instrument full_interface changes, change all full_interface tags of parameters"""
        if change['type']!='create':
            self.set_all_tags(full_interface=self.full_interface)
        
if __name__=="__main__":
    class to(object):
        a=5
        b=4.3
        c="hey"
        d=True

        @log_func    
        def ff(self, a=2):
            print self, a
            print "a f says hello"
        
        
    class tA(Atom):
        a=Int(5)
        b=Float(4.3)
        c=Unicode("hey")
        d=Bool(True)
        f=Enum(1,2,3)
        g=Enum("a", "b")
        
        @Callable
        @log_func    
        def ff(self, a=2):
            print self, a
            print "b f says hello"
        

    a=to()
    b=tA()
    print get_member(a, "a"), get_member(b, "a")
    print members(a), members(b)
    set_tag(a,"a", bill=5, private=True)
    set_tag(b,"a", bill="five", sub=True)
    set_all_tags(a, bob=7)
    set_all_tags(b, bob="seven")
    print get_metadata(a, "a"), get_metadata(b, "a")
    print get_tag(a, "a", "bill"), get_tag(b, "a", "bill")
    print get_all_tags(a, "bill"), get_all_tags(a, "bill", "five"),  get_all_tags(b, "bill", "five")    
    print b.f, get_map(b, "f"), get_mapping(b, "f"), get_inv(b, "f", 2)
    print b.g, get_map(b, "g"), get_mapping(b, "g"), get_inv(b, "f", 2)
    print get_type(a, "a"), get_type(b, "a")
    print get_reserved_names(a), get_reserved_names(b)
    print get_all_params(a), get_all_params(b)
    print get_all_main_params(a), get_main_params(b)
    print get_main_params(a), get_main_params(b)
    print get_attr(a, "a", "yes"), get_attr(b, "aa", "yes")
    
    @log_func    
    def ff(self, a=2):
        print self, a
        print "f says hello"
    a.gg=ff    
    a.ff(), b.ff(b), a.gg(a)
    print get_run_params(ff), get_run_params(a.ff), get_run_params(a.gg)
    print b.a, a.a
    run_func(b, "ff", a=1), run_func(a, "ff", a=1), run_func(a, "gg")
    print b.a, a.a
    
    c=Backbone()
    print c.view, c.main_params, c.base_name, c.all_params, c.all_main_params, c.reserved_names


    #print ff.func_code.co_argcount
    #print list(ff.func_code.co_varnames[0:ff.func_code.co_argcount])
    
#def get_args(obj, name):
#    f=getattr(obj, name)
#    run_params=get_run_params(f, True)
#    arglist=[]
#    if "self" in run_params:
#        arglist.append(obj)
#        run_params.remove("self")
#    arglist.extend([getattr(obj, an) for an in run_params])
#    return arglist    
    #   Enum, Range, FloatRange, Int, Float, Callable, Unicode, Bool, List 

#
#
#    def add_plot(self, name=''):
#        if name=="" or name in (p.name for p in self.boss.plots):
#            name="plot{}".format(len(self.boss.plots))
#            self.boss.plots.append(Plotter(name=name))
#
#    def add_line_plot(self, name):
#        xname=self.get_tag(name, 'xdata')
#        if xname==None:
#            xdata=None
#        else:
#            xdata=getattr(self, xname)
#        self.boss.plots[0].add_plot(name, yname=name, ydata=getattr(self, name), xname=xname, xdata=xdata)
#        self.boss.plots[0].title=self.name
#        if xname==None:
#            self.boss.plots[0].xlabel="# index"
#        else:
#            self.boss.plots[0].xlabel=self.get_tag(xname, "plot_label", xname)
#        self.boss.plots[0].ylabel=self.get_tag(name, "plot_label", name)
#
#    def add_img_plot(self, name):
#        xname=self.get_tag(name, 'xdata')
#        yname=self.get_tag(name, 'ydata')
#        if xname!=None and yname!=None:
#            xdata=getattr(self, xname)
#            ydata=getattr(self, yname)
#        else:
#            xdata=None
#            ydata=None
#        self.boss.plot_list[0].add_img_plot(name, zname=name, zdata=getattr(self, name), xname=xname, yname=yname, xdata=xdata, ydata=ydata)
#        self.boss.plot_list[0].title=self.name
#        if xname==None:
#            self.boss.plot_list[0].xlabel="# index"
#        else:
#            self.boss.plot_list[0].xlabel=self.get_tag(xname, "plot_label", xname)
#        if yname==None:
#            self.boss.plot_list[0].ylabel="# index"
#        else:
#            self.boss.plot_list[0].ylabel=self.get_tag(yname, "plot_label", yname)

#def set_attr(obj, name, value):
#    """a logging lowhigh checker for arbitrary classes. useful?"""
#    log_it=False
#    if name in get_all_params(obj) and isinstance(obj, (backbone, SubAgent)):
#        log_it=True
#        value=lowhigh_check(obj, name, value)            
#    setattr(obj, name, value)
#    if log_it:
#        set_log(obj, name, value)

class obackbone(object):
    """a non-atom convenience backbone class"""

    def __setattr__(self, name, value):
        log_it=False
        if name in get_all_params(self):
            log_it=True
            value=lowhigh_check(self, name, value)            
        super(obackbone, self).__setattr__(name, value)
        if log_it:
            set_log(self, name, value)

    name="" 
    title= ""
    desc= ""
    full_interface=False 
    plot_all=False 
    view="Auto" 

    @property
    def base_name(self):
        """default base name of base if no name is given. can be overwritten in subclasses"""
        return "base"

    @property
    def reserved_names(self):
        """reserved names not to perform standard logging and display operations on,
           i.e. members that are tagged as private and will behave as usual Atom members"""
        return get_reserved_names(self) #get_all_tags("private", True)

    @property
    def all_params(self):
        """all params to perform logging and display operations on"""
        return get_all_params(self)

    @property
    def all_main_params(self):
        """all_params that are not tagged as sub"""
        return get_all_main_params(self)
    @property
    def main_params(self):
        """defaults to all members in all_params that are not tagged as sub.
        Can be overwritten to allow some minimal custom layout control,
        e.g. order of presentation and which members are shown. Use self.all_main_params to get a list of
        all members that could be in main_params"""
        return self.all_main_params 