from kitt.interfaces import implements, IDroneDService
from twisted.application import internet
from twisted.application.service import Service
from twisted.protocols import ftp
from twisted.protocols.ftp import IFTPShell, FTPShell, FTPAnonymousShell
from twisted.cred import error, portal, checkers, credentials
from kitt.util import dictwrapper
from droned.logging import logWithContext
from twisted.python import filepath
import config

class Ftp(object):
    implements(IDroneDService) 
 
    parentService = None
    service = None 
    SERVICENAME = 'ftp' 
    SERVICECONFIG = dictwrapper()

    def install(self, _parentService):
        self.ftpserver = ftp.FTPFactory()
        self.parentService = _parentService
 
    def start(self):
        if self.running(): return

        realm = GenericFTPRealm(self.SERVICECONFIG.SITE_ROOT, self.SERVICECONFIG.SITE_ROOT)
        ftpportal = portal.Portal(realm)
        if self.SERVICECONFIG.ALLOW_ANONYMOUS: ftpportal.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)
        if self.SERVICECONFIG.PASSWORDFILE: ftpportal.registerChecker(checkers.FilePasswordDB(self.SERVICECONFIG.PASSWORDFILE, cache=True)) 
 
        self.ftpserver.userAnonymous = self.SERVICECONFIG.ANONYMOUS_USER or 'Anonymous'
        self.ftpserver.tld = self.SERVICECONFIG.SITE_ROOT
        self.ftpserver.portal = ftpportal
        self.ftpserver.protocol = ftp.FTP

        self.service = internet.TCPServer(int(self.SERVICECONFIG.PORT), self.ftpserver)
        self.service.setServiceParent(self.parentService)

    def stop(self):
        if self.service:
            self.service.disownServiceParent()
            self.service.stopService()
            self.service = None
 
    def running(self):
        return bool(self.service) and self.service.running

log = logWithContext(type=Ftp.SERVICENAME)

class GenericFTPRealm:
    implements(portal.IRealm)

    def __init__(self, anonymousRoot, site_root):
        self.anonymousRoot = filepath.FilePath(anonymousRoot)
        self.site_root = filepath.FilePath(site_root)

    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is IFTPShell:
                if avatarId is checkers.ANONYMOUS:
                    avatar = FTPAnonymousShell(self.anonymousRoot)
                else:
                    avatar = FTPShell(self.site_root)
                return IFTPShell, avatar, getattr(avatar, 'logout', lambda: None)
        raise NotImplementedError("Only IFTPShell interface is supported by this realm")

