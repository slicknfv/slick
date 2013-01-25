# This file should be used to comm. with the controller.
import os
import time
from threading import Thread

import rpyc
#import constants


class MBControllerService(rpyc.Service):
    class exposed_MBController(object):   # exposing names is not limited to methods :)
        def __init__(self, filename, remote_callback, interval = 1):
            self.filename = filename
            self.interval = interval
            self.last_stat = None
            self.callback = rpyc.async(remote_callback)   # create an async callback
            self.active = True
            self.thread = Thread(target = self.work)
            self.thread.start()

        def exposed_stop(self):   # this method has to be exposed too
            self.active = False
            self.thread.join()

        # Used by client to send the event.
        # These are in JSON format.
        def exposed_trigger(self,trigger):
            pass

        def work(self):
            while self.active:
                stat = os.stat(self.filename)
                if self.last_stat is not None and self.last_stat != stat:
                    self.callback(self.last_stat, stat)   # notify the client of the change
                self.last_stat = stat
                #time.sleep(self.interval)

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    ThreadedServer(MBControllerService, port = 18871).start()
