#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright © 2014 Sébastien Gross <seb•ɑƬ•chezwam•ɖɵʈ•org>
# Created: 2015-01-15
# Last changed: 2015-05-04 10:13:42
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.
#
# This file is not part of Ansible


import os
import yaml


import ansible.constants as C


def _print_slots(obj):
    for slot in obj.__slots__:
        try:
            print '  %s => "%s"' % (slot, getattr(obj, slot))
        except AttributeError:
            print '  %s => NONE' % (slot)

def mergedicts(dict1, dict2):
    if isinstance(dict1,dict) and isinstance(dict2,dict):
        # make sure keys starting with + come last.
        for k,v in sorted(dict2.iteritems(), reverse=True):
            # if key starts with a + sign, merge both keys
            if k.startswith('+'):
                new_key = k.strip('+')
                if dict1.has_key(new_key):
                    ## List
                    if type(dict1[new_key]) == type([]):
                        # list of list
                        if type(dict1[new_key][0]) != type({}):
                            dict1_set = set(dict1[new_key])
                            dict1_set.update(v)
                            dict1[new_key] = list(dict1_set)
                        else:
                            # list of hash. do not add hash multiple times.
                            for _v in v:
                                if not _v in dict1[new_key]:
                                    dict1[new_key].append(_v)
                else:
                    dict1[new_key] = v
            else:
                dict1[k] = v
    elif isinstance(dict1,list) and isinstance(dict2,list):
        dict1 += dict2

    return dict1

class VarsModule(object):

    CUSTOM = 'custom'
    def __init__(self, inventory):
        self.inventory = inventory
        self.custom_root = inventory.basedir()
        self.custom_levels = C.get_config(C.p, self.CUSTOM, 'levels', None, '..')
        self.custom_dir =  C.get_config(C.p, self.CUSTOM, 'dir', None, 'secret')

        self.custom_path = self.custom_root + '/' + self.custom_levels + \
                           '/' + self.custom_dir + '/%s/%s' 
        
        self.group_cache = {}

                
    def run(self, host, vault_password=None):
        # print "Custom"
        _vars = self.inventory._hosts_cache[host.name].get_variables()
        
        if _vars.has_key('groups'):
            _groups = _vars['groups'].split(',')
            if type(_groups) == type(''):
                _groups = [ _groups ]
            for group in _groups:
                _vars['group_names'].append(group)

        var = self.inventory._hosts_cache[host.name]
        # print var.get_variables()

        if host.name.startswith('/'):
            host_name = '_chroot'
            #host_store = '_chroot'
        else:
            host_name = host.name
           # host_store = host.name
        
        host.vars['custom_store'] = self.custom_path % ('store', '')
        host.vars['custom_secret'] = self.custom_path % ('secret', host_name)
        host.vars['custom_vars'] = (self.custom_path + '.yml') % ('host_vars', host_name)
        host.vars['custom_path'] = self.custom_path

        files_to_read = []
        for group in [ 'all' ] + _vars['group_names']:
            # print "Group: %s" % group
            files_to_read.append((self.custom_path + '.yml') % ('group_vars', group))

        if host.name.startswith('/'):
            files_to_read.append((self.custom_path + '.yml') % ('group_vars', '_chroot'))
        else:
            files_to_read.append(host.vars['custom_vars'])
        
        for var_file in files_to_read:
            # print host_name, var_file
            if os.path.exists(var_file):
                for data in yaml.load_all(file(var_file).read()):
                    #print data
                    for k, v in data.iteritems():
                        new_key = k.strip('+')
                        if host.vars.has_key(new_key) and k.startswith('+'):
                            host.vars[new_key] = mergedicts(host.vars[new_key], v)
                        else:
                            host.vars[new_key] = v

        # print host.vars
        # for key in [ 'custom_store', 'custom_secret', 'custom_vars', 'custom_path' ]:
        #     print '%s\t%s' % (key, host.vars[key])
        # _print_slots(self.inventory)
