# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 12:38:54 2015

@author: thomasaref
"""
#from taref.core.log import f_top#, log_debug
from taref.core.shower_backbone import get_view_window
from taref.core.backbone import Backbone
from enaml import imports
from enaml.qt.qt_application import QtApplication

def shower(*agents, **kwargs):
    """A powerful showing function for any Atom object(s) specified in agents.
    Checks if an object has a view_window and otherwise uses a default window for the object.

    Checks kwargs for particular keywords:
        * ``start_it``: boolean representing whether to go through first time setup prior to starting app
        * ``app``: defaults to existing QtApplication instance and will default to a new instance if none exists
        chief_cls: if not included defaults to the first agent and defaults to Backbone if no agents are passed.
        show_log: shows the log_window of chief_cls if it has one, defaults to not showing
        show_ipy: shows the interactive_window of chief_cls if it has one, defaults to not showing
        show_code: shows the code_window of chief_cls if it has one, defaults to not showing

    shower also provides a chief_window (generally for controlling which agents are visible) which defaults to Backbone's chief_window
    if chief_cls does not have one. attributes of chief_window can be modified with the remaining kwargs"""

    start_it=kwargs.pop("start_it", False)
    app=QtApplication.instance()
    if app is None:
        app = QtApplication()
        start_it=True

    with imports():
        from taref.core.agent_e import AutoAgentView
    for n, agent in enumerate(agents):
        view=get_view_window(agent, AutoAgentView(agent=agent), "window_{0}".format(n))
        view.show()

    if start_it:
        chief_cls=kwargs.pop("chief_cls", agents[0] if agents!=() else Backbone)
        chief_view=getattr(chief_cls, "chief_window", Backbone.chief_window)
        chief_view.chief_cls=chief_cls
        for key in kwargs:
            setattr(chief_view, key, kwargs[key])
        chief_view.show()
        if hasattr(chief_cls, "interact"):
            chief_cls.interact.make_input_code()

        try:
            app.start()
        finally:
            if hasattr(chief_cls, "clean_up"):
                chief_cls.clean_up()


if __name__=="__main__":
    shower()