#! /usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
##                                                                           ##
##  Copyright 2010-2012, Neil Wallace <neil@openmolar.com>                   ##
##                                                                           ##
##  This program is free software: you can redistribute it and/or modify     ##
##  it under the terms of the GNU General Public License as published by     ##
##  the Free Software Foundation, either version 3 of the License, or        ##
##  (at your option) any later version.                                      ##
##                                                                           ##
##  This program is distributed in the hope that it will be useful,          ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of           ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            ##
##  GNU General Public License for more details.                             ##
##                                                                           ##
##  You should have received a copy of the GNU General Public License        ##
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.    ##
##                                                                           ##
###############################################################################

import re
import sys

from lib_openmolar.common.connect import ProxyClient

from lib_openmolar.admin.connect import AdminConnection

def user_perms(func):
    def userf(*args, **kwargs):
        LOGGER.debug("server function called %s"% func.__name__)
        try:
            return func(*args, **kwargs)
        except ProxyClient.PermissionError:
            LOGGER.warning("permission error for function %s"% func.__name__)
            LOGGER.info(
                "\t offering user chance to elevate his/her permissions")
            proxy_manager_instance = args[0]
            if proxy_manager_instance.switch_server_user():
                return func(*args, **kwargs)

    return userf

class ProxyManager(object):
    '''
    A ProxyManager manages the openmolar-servers running and provides an
    interface for them to manage postgres.
    '''

    _proxy_clients = []
    selected_index = 0

    #:
    PermissionError = ProxyClient.PermissionError

    def __init__(self):
        # not called when this class is subclassed by AdminMainWindow
        self._init_proxies()

    @property
    def proxy_clients(self):
        '''
        A list of :doc:`ProxyClient`
        '''
        return self._proxy_clients

    def wait(self, *args):
        '''
        dummy function can overwritten
        '''
        pass

    def advise(self, message, importance=None):
        '''
        advise function. normally overwritten
        '''
        if importance is None:
            LOGGER.debug(message)
        elif importance == 1:
            LOGGER.info(message)
        else:
            LOGGER.warning(message)

    def log(self, message):
        '''
        dummy function often overwritten
        '''
        self.advise(message, 1)

    def display_proxy_message(self):
        '''
        display the proxy message.
        this function should be overwritten by subclasses of ProxyManager.
        it is called whenever the client message should be refreshed.
        '''
        LOGGER.warning("display_proxy_message should be overwritten")
        pass

    def _init_proxies(self):
        '''
        load the proxies.
        '''
        self.forget_proxies()
        n_clients, n_active = 0,0
        for connection230_data in SETTINGS.om_connections:
            LOGGER.debug("found connection data %s"% connection230_data)
            client = ProxyClient(connection230_data)
            LOGGER.debug("loading proxy_client %s"% client)
            try:
                client.connect()
            except client.ConnectionError:
                LOGGER.error("%s was unable to connect"% client)
            self._proxy_clients.append(client)
            n_clients += 1
            if client.is_connected:
                n_active += 1

        LOGGER.info("ProxyManager has %d clients (%d are connected)"% (
            n_clients, n_active))

    def forget_proxies(self):
        self._proxy_clients = []

    def om_connect(self):
        '''
        connect to a 230 server
        '''
        LOGGER.info("connecting to any configured openmolar_servers....")
        self._init_proxies()

    def om_disconnect(self):
        '''
        disconnect from the 230 server
        '''
        LOGGER.info("disconnecting from all openmolar_servers....")
        self.forget_proxies()

    @property
    def selected_client(self):
        '''
        return the currently selected :doc:ProxyClient
        (by default this is item 0 of _proxy_clients)
        '''
        try:
            return self._proxy_clients[self.selected_index]
        except IndexError:
            return None

    @property
    def selected_server(self):
        '''
        return the currently selected proxy server
        '''
        if self.selected_client.server is None:
            raise ProxyClient.ConnectionError
        return self.selected_client.server

    def set_proxy_index(self, index):
        '''
        :param:index(int)
        choose which server to use
        '''
        LOGGER.debug("setting proxy index to %s"% index)
        self.selected_index = index
        self.display_proxy_message()

    def switch_server_user(self):
        '''
        this needs to be a function to change the user of the proxy
        should be overwritten by subclasses
        '''
        LOGGER.warning("ProxyManager.switch_server_user should be overwritten")
        return False

    def create_demo_database(self):
        '''
        initiates the demo database
        '''
        continue_ = self.create_database("openmolar_demo")
        if not continue_:
            self.advise(_("failed"))
            return

    def create_demo_user(self):
        '''
        create and grant privileges to om_demo
        '''
        LOGGER.info("creating demo user")
        try:
            self.wait()
            self.advise("creating demo user")
            payload = self.selected_client.call("create_demo_user")
            self.wait(False)
            if payload.payload:
                self.advise(_("successfully created demo user"))
                LOGGER.info("successfully created demo user")
            else:
                self.advise(_("unable to create demo user"))
                LOGGER.error("unable to create demo user")
        except:
            message = "error creating demo_user"
            LOGGER.exception(message)
            self.advise(message, 2)
            continue_= False
        finally:
            self.wait(False)

        return payload.payload

    @user_perms
    def create_database(self, dbname):
        '''
        creates a new db
        '''
        success = False

        LOGGER.info("creating database %s"% dbname)
        self.advise("%s '%s' <br />%s"%(
            _("Creating a new database"), dbname,
            _("This may take some time")))
        self.wait()

        payload = self.selected_client.call("create_db",dbname)
        if payload.payload:
            if dbname == "openmolar_demo":
                self.advise("creating demo user and granting permissions")
                self.create_demo_user()
            else:
                self.advise(u"%s '%s'<br />%s"%(
                _("Successfully created database!"), dbname,
                _("This database has no users yet")), 1)

            LOGGER.info("database %s created"% dbname)

        self.wait(False)
        self.display_proxy_message()
        return payload.payload

    @user_perms
    def drop_db(self, dbname):
        '''
        send a message to the openmolar server to drop this database
        '''
        if dbname == "openmolar_demo":
            payload = self.selected_client.call("drop_demodb")
        else:
            payload = self.selected_client.call("drop_db", str(dbname))

        if payload.payload:
            self.advise(u"%s %s"%(
                _("Sucessfully dropped database"), dbname), 1)
        else:
            self.advise(u"%s<hr />%s"%(
                _("unable to drop database"), payload.error_message), 2)

        self.display_proxy_message()

    @user_perms
    def truncate_db(self, dbname):
        '''
        send a message to the openmolar server to delete all data this database
        this is for test purposes eg. demo database or import only
        '''
        if dbname == "openmolar_demo":
            payload = self.selected_client.call("truncate_demo")
        else:
            payload = self.selected_client.call("truncate_all_tables",
                str(dbname))

        if payload.payload:
            self.advise(u"%s %s"%(
                _("Sucessfully removed all data from"), dbname), 1)
        else:
            self.advise(u"%s<hr />%s"%(
                _("Operation failed"), payload.error_message), 2)

        self.display_proxy_message()

    @user_perms
    def add_postgres_user(self, username, password):
        '''
        send a message to the openmolar server to delete all data this database
        this is for test purposes eg. demo database or import only
        '''
        payload = self.selected_client.call("create_user", username, password)

        if payload.payload:
            self.advise(u"%s %s"% (
                _("Sucessfully added postgres user"), username), 1)
        else:
            self.advise(u"%s<hr />%s"%(
                _("Operation failed"), payload.error_message), 2)

        self.display_proxy_message()


def _test():
    import lib_openmolar.admin
    import gettext
    import logging
    from lib_openmolar.common.connect import ProxyUser

    #LOGGER is in the namespace due to lib_openmolar.admin import

    LOGGER.setLevel(logging.DEBUG)
    gettext.install("openmolar")
    pm = ProxyManager()

    LOGGER.debug("using %s"% pm.selected_server)
    LOGGER.debug(pm.drop_db("openmolar_demo"))
    LOGGER.debug(pm.create_demo_database())

if __name__ == "__main__":
    _test()
