from kitt.interfaces import implements, IDroneDService
from twisted.application import internet
from twisted.conch.manhole import Manhole
from twisted.conch.manhole_ssh import TerminalRealm, ConchFactory
from twisted.cred import error, portal, checkers, credentials
from kitt.util import dictwrapper
from droned.logging import logWithContext
import config
import copyright

class ManholeService(object):
    implements(IDroneDService)

    parentService = None
    service = None
    SERVICENAME = 'manhole'
    SERVICECONFIG = dictwrapper()

    def install(self, _parentService):
        self.parentService = _parentService
        realm = TerminalRealm()
        realm.chainedProtocolFactory.protocolFactory = lambda _: Manhole(globals())
        login = {self.SERVICECONFIG.USERNAME: self.SERVICECONFIG.PASSWORD}
        credChecker = checkers.InMemoryUsernamePasswordDatabaseDontUse(**login)
        sshportal = portal.Portal(realm)
        sshportal.registerChecker(credChecker)
        self.sessionFactory = ConchFactory(sshportal)

    def start(self):
        if self.running(): return
        self.service = internet.TCPServer(self.SERVICECONFIG.PORT, self.sessionFactory)
        self.service.setServiceParent(self.parentService)

    def stop(self):
        if self.service:
            self.service.disownServiceParent()
            self.service.stopService()
            self.service = None

    def running(self):
        return bool(self.service) and self.service.running

log = logWithContext(type=ManholeService.SERVICENAME)
