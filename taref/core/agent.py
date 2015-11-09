# -*- coding: utf-8 -*-
"""
Created on Sat Jul  4 13:03:26 2015

@author: thomasaref
"""
from atom.api import Unicode, Enum, Float, Int, ContainerList, Callable
from taref.core.chief import chief
from taref.core.backbone import Backbone, log_func

class SubAgent(Backbone):
    """Adds chief functionality to Backbone"""
    name=Unicode().tag(private=True, desc="name of agent. A default will be provided if none is given")
    desc=Unicode().tag(private=True, desc="optional description of agent")

    def show(self):
        self.chief.show()

    def extra_setup(self, param, typer):
        """Can be overwritten to allow custom setup extension in subclasses"""
        self.es_log_callables(param, typer)

    def es_log_callables(self, param, typer):
        """extra setup function that autosets Callables to be logged"""
        if typer==Callable:
            func=getattr(self, param)
            setattr(self, param, log_func(func))

    @property
    def base_name(self):
        return "subagent"

    @property
    def chief(self):
        """gets chief of agent. can be overwritten in children classes"""
        return chief

    @property
    def abort(self):
        """shortcut to chief's abort control"""
        return self.chief.abort
        
    def __init__(self, **kwargs):
        """extends __init__ to set boss, add agent to boss's agent list and give unique default name.
        does some extra setup for particular types"""
        #self.boss.make_boss()
        super(SubAgent, self).__init__(**kwargs)
        if "name" not in kwargs:
            self.name="{basename}__{basenum}".format(basename=self.base_name, basenum=len(self.chief.agents))
        self.chief.agents.append(self)

class Spy(SubAgent):
    """Spy uses observers to log all changes"""
    def __setattr__(self, name, value):
        """setattr performs low/high check"""
        if name in self.all_params:
            value=self.lowhigh_check(name, value)
        super(Spy, self).__setattr__(name, value)

    def log_changes(self, change):
        """a simple logger for all changes"""
        self.set_log(change["name"], change["value"])

    def extra_setup(self, param, typer):
        """adds log_changes observer to all params"""
        self.observe(param, self.log_changes)

    @property
    def base_name(self):
        return "spy"


class Agent(Spy):
    """Agents use setattr rather than observers to log all changes"""
    def __setattr__(self, name, value):
        """uses __setattr__ to log changes except for ContainerList"""
        log_it=False
        if name in self.all_params:
            log_it=True
            value=self.lowhigh_check(name, value)
        super(Agent, self).__setattr__(name, value)
        if log_it:
            self.set_log(name, value)

    def extra_setup(self, param, typer):
        """adds observer for ContainerLists to catch changes not covered by setattr"""
        if typer==ContainerList:
            self.observe(param, self.log_changes)


    @property
    def base_name(self):
        return "agent"


if __name__=="__main__":
    from a_Backbone import run_func, log_func
    c=SubAgent()
    print c.view, c.main_params, c.base_name, c.all_params, c.all_main_params, c.reserved_names

    class tSpy(Spy):
        a=Float().tag(unit="A", unit_factor=10.0, label="Current", no_spacer=True, show_value=True)
        b=Unicode()
        c=Unicode().tag( no_spacer=True, spec="multiline")
        d=Int().tag(unit="A", unit_factor=10, label="Current",show_value=True)
        e=Enum("arg")

        @Callable
        def g(self):
            print self
            print "ran g"

    d=tSpy()
    d.a=4.3
    d.a=3.2
    #d.g(d)

    #run_func(d, "g")
    d.show()#show(d)
#    class test(object):
#        b=4
#        c=2
#
#        #@property
#        def f(self):
#            return 7
#        f.metadata=dict(mapping={7:1})
#
#
#    a=test()
#    print members(a)
#    print get_member(a, "c")
#    print get_metadata(a, "c")
#    metadata=get_metadata(a, "c")
#    metadata.update(money="power", foo="bar")
#    print get_metadata(a, "c")
#    print get_tag(a, "c", "h", True)
#    print get_map(a, "c", {2:3})
#    print get_map(a, "f")
#
#    print list_recursion([[["a", "d"],[ 1,2]], "b", "c"])
#
#    from atom.api import Int, observe, Coerced, Typed, Instance
#
#    class test(Atom):
#        a=Int().tag(money="time")
#        b=Int()
#        #c=Coerced(float, coercer=int)
#        c=Instance(float, ())
##        Instance
#
#        def _observe_a(self, change):
#            print change
#
#        def _observe_b(self, change):
#            print change
#
#        @observe('a')
#        @updater
#        def update_b(self, change):
#            self.b=self.a+1
#
#        @observe('b')
#        @updater
#        def update_a(self, change):
#            self.a=self.b+1

    #a=test()
    #print get_metadata(a, "a")
    #Coerced type get_member.validate_mode[1][1]
    #print get_member(a, "c").validate_mode
    #print
    #a.a=4
    #a.a=9
    #a.b=3

