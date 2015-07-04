#!/usr/bin/python3

import imp
import os
import socket
import time
import sys
from collections import defaultdict

from conf import conf
import classes

class Irc():
    def __init__(self, proto):
        # Initialize some variables
        self.connected = False
        self.users = {}
        self.channels = defaultdict(classes.IrcChannel)
        self.name = conf['server']['netname']
        self.conf = conf
        self.servers = {}

        self.serverdata = conf['server']
        ip = self.serverdata["ip"]
        port = self.serverdata["port"]
        self.sid = self.serverdata["sid"]
        print("Connecting to network %r on %s:%s" % (self.name, ip, port))

        self.socket = socket.socket()
        self.socket.connect((ip, port))
        self.proto = proto
        proto.connect(self)
        self.loaded = []
        self.load_plugins()
        self.connected = True
        self.run()

    def run(self):
        buf = ""
        data = ""
        while self.connected:
            try:
                data = self.socket.recv(2048).decode("utf-8")
                buf += data
                if not data:
                    break
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    print("<- {}".format(line))
                    proto.handle_events(self, line)
            except socket.error as e:
                print('Received socket.error: %s, exiting.' % str(e))
                break
        sys.exit(1)

    def send(self, data):
        data = data.encode("utf-8") + b"\n"
        print("-> {}".format(data.decode("utf-8").strip("\n")))
        self.socket.send(data)

    def load_plugins(self):
        to_load = conf['plugins']
        plugins_folder = [os.path.join(os.getcwd(), 'plugins')]
        # Here, we override the module lookup and import the plugins
        # dynamically depending on which were configured.
        for plugin in to_load:
            try:
                moduleinfo = imp.find_module(plugin, plugins_folder)
                self.loaded.append(imp.load_source(plugin, moduleinfo[1]))
            except ImportError as e:
                if str(e).startswith('No module named'):
                    print('Failed to load plugin %r: the plugin could not be found.' % plugin)
                else:
                    print('Failed to load plugin %r: import error %s' % (plugin, str(e)))
        print("loaded plugins: %s" % self.loaded)

if __name__ == '__main__':
    print('PyLink starting...')
    if conf['login']['password'] == 'changeme':
        print("You have not set the login details correctly! Exiting...")
        sys.exit(2)

    protoname = conf['server']['protocol']
    protocols_folder = [os.path.join(os.getcwd(), 'protocols')]
    try:
        moduleinfo = imp.find_module(protoname, protocols_folder)
        proto = imp.load_source(protoname, moduleinfo[1])
    except ImportError as e:
        if str(e).startswith('No module named'):
            print('Failed to load protocol module %r: the file could not be found.' % protoname)
        else:
            print('Failed to load protocol module: import error %s' % (protoname, str(e)))
    else:
        irc_obj = Irc(proto)
