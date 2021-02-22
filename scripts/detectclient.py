"""
detectclient.py

Author: noway421
Modified by: MuffinTastic
License: CC-BY-SA

"""

from pyspades.constants import *
from pyspades.loaders import Loader
from pyspades.bytes import ByteReader, ByteWriter
from commands import add, alias, get_player
from twisted.internet.reactor import callLater
from random import randint

CLIENT_NAMES = {
    ord('a') : "Ace of Spades",
    ord('o') : "OpenSpades",
    ord('B') : "BetterSpades",
}

KICK_OLD_VERSIONS = True
KICK_DELAY = 5
MINIMUM_VERSIONS = {
    ord('o') : (0, 1, 0) # as requested by yvt

    # add other minimum versions if necessary.
    # any clients omitted will be ignored
}

# for easy comparisons
MINIMUM_VERSIONS_I = dict((key, (MINIMUM_VERSIONS[key][0] << 16 | MINIMUM_VERSIONS[key][1] << 8 | MINIMUM_VERSIONS[key][2])) for key in MINIMUM_VERSIONS)

class HandShakeInit(Loader):
    id = 31

    answer = 0

    def read(self, reader):
        self.answer = reader.readInt(True)

    def write(self, writer):
        writer.writeByte(self.id, True)
        writer.writeInt(self.answer, True)


class HandShakeReturn(Loader):
    id = 32

    answer = 0

    def read(self, reader):
        self.answer = reader.readInt(True)

    def write(self, writer):
        writer.writeByte(self.id, True)
        writer.writeInt(self.answer, True)


class VersionGet(Loader):
    id = 33

    def read(self, reader):
        pass

    def write(self, writer):
        writer.writeByte(self.id, True)


class VersionSend(Loader):
    id = 34

    client = ord('-')
    version_major = -1
    version_minor = -1
    version_revision = -1
    version_info = 'None'

    def read(self, reader):
        self.client = reader.readByte(True)
        self.version_major = reader.readByte(True)
        self.version_minor = reader.readByte(True)
        self.version_revision = reader.readByte(True)
        self.version_info = reader.readString()

    def write(self, writer):
        writer.writeByte(self.id, True)
        writer.writeByte(self.client, True)
        writer.writeByte(self.version_major, True)
        writer.writeByte(self.version_minor, True)
        writer.writeByte(self.version_revision, True)
        writer.writeString(self.version_info)


handshake_init = HandShakeInit()
handshake_return = HandShakeReturn()
version_get = VersionGet()
version_send = VersionSend()


def formatted_client_info(self, whom):
    return "%s running %s v%d.%d.%d on %s" % (
        whom,
        (CLIENT_NAMES[self.client_info.client] if self.client_info.client in CLIENT_NAMES else "Unknown"),
        self.client_info.version_major,
        self.client_info.version_minor,
        self.client_info.version_revision,
        self.client_info.version_info)

def formatted_warning_message(self, time):
    WARNING_MESSAGE = "!!! %s v%d.%d.%d IS TOO OLD! Upgrade to at LEAST v%d.%d.%d. You'll be kicked in %ss. !!!"
    return WARNING_MESSAGE % (CLIENT_NAMES[self.client_info.client] if self.client_info.client in CLIENT_NAMES else "Unknown",
                                            self.client_info.version_major,
                                            self.client_info.version_minor,
                                            self.client_info.version_revision,
                                            MINIMUM_VERSIONS[self.client_info.client][0],
                                            MINIMUM_VERSIONS[self.client_info.client][1],
                                            MINIMUM_VERSIONS[self.client_info.client][2],
                                            time)


@alias('clin')
def client_info(self, value=None):
    if value is None:
        if self not in self.protocol.players:
            raise ValueError()
        return formatted_client_info(self, "You're")
    else:
        him = get_player(self.protocol, value)
        return formatted_client_info(him, him.name)
add(client_info)


class ClientInfo(object):
    def __init__(self):
        self.disconnected()

    def connected(self):
        self.reset()

    def disconnected(self):
        self.reset()
        self.version_info = 'Disconnected'

    def reset(self):
        self.client = ord('-')
        self.version_major = -1
        self.version_minor = -1
        self.version_revision = -1
        self.version_info = 'Pending'


def apply_script(protocol, connection, config):

    class DetectclientConnection(connection):

        client_info = None
        listen_for_response = False
        listening_timeout = None
        old_kick_timeout = None
        challenge_question = None

        showed_clin = False

        def __init__(self, *arg, **kw):
            self.client_info = ClientInfo()
            connection.__init__(self, *arg, **kw)

        def on_connect(self):
            self.client_info.connected()
            self.listen_for_response = False
            self.showed_clin = False

            return connection.on_connect(self)

        def on_disconnect(self):
            try:
                self.listening_timeout.cancel()
            except:
                pass

            try:
                self.old_kick_timeout.cancel()
            except:
                pass

            self.client_info.disconnected()
            self.listen_for_response = False
            self.showed_clin = False

            return connection.on_disconnect(self)

        def on_spawn(self, pos):
            if not self.showed_clin:
                if self.client_info.version_info != 'Pending':
                    self.showed_clin = True
                    self.protocol.irc_say('%s' % (formatted_client_info(self,self.name)))
                    print '%s' % (formatted_client_info(self,self.name))
            return connection.on_spawn(self, pos)

        def on_join(self):
            self.challenge_question = randint(0, 2**32 - 1)
            handshake_init.answer = self.challenge_question
            self.send_contained(handshake_init)

            self.listening_timeout = callLater(1.4, self.handshake_timeout)
            self.listen_for_response = True

            return connection.on_join(self)

        def loader_received(self, loader):
            if self.player_id is not None and self.listen_for_response:
                data = ByteReader(loader.data)
                packet_id = data.readByte(True)
                if packet_id == HandShakeReturn.id:
                    handshake_return.read(data)
                    if handshake_return.answer == self.challenge_question:
                        self.on_handshake_answer()
                    else:
                        try:
                            self.listening_timeout.cancel()
                        except:
                            pass
                        self.client_info.client = ord('U')
                        self.client_info.version_major = 0
                        self.client_info.version_minor = 0
                        self.client_info.version_revision = 0
                        self.client_info.version_info = 'Unknown'
                        self.listen_for_response = False
                        self.on_version_get()
                    return None
                elif packet_id == VersionSend.id:
                    version_send.read(data)
                    self.on_version_answer(version_send)
                    return None

            return connection.loader_received(self, loader)

        def handshake_timeout(self):
            if not client_info:
                self.stop_listhening()
                return
            # just assume it's vanilla
            self.client_info.client = ord('a')
            self.client_info.version_major = 0
            self.client_info.version_minor = 75
            self.client_info.version_revision = 0
            self.client_info.version_info = 'Windows'

            self.listening_timeout = callLater(5, self.stop_listhening)
            self.on_version_get()

        def stop_listhening(self):
            self.listen_for_response = False

        def on_handshake_answer(self):
            try:
                self.listening_timeout.cancel()
            except:
                pass

            self.listening_timeout = callLater(5, self.stop_listhening)
            self.send_contained(version_get)

        def on_version_answer(self, info):
            try:
                self.listening_timeout.cancel()
            except:
                pass

            self.client_info.client = info.client
            self.client_info.version_major = info.version_major
            self.client_info.version_minor = info.version_minor
            self.client_info.version_revision = info.version_revision
            self.client_info.version_info = info.version_info
            self.listen_for_response = False
            self.on_version_get()

        def on_outdated_version_get(self):
            outdated_client_string = "%s v%d.%d.%d" % (CLIENT_NAMES[self.client_info.client] if self.client_info.client in CLIENT_NAMES else "Unknown",
                                                       self.client_info.version_major,
                                                       self.client_info.version_minor,
                                                       self.client_info.version_revision)

            print "%s ID %s using outdated client %s" % (self.name, self.player_id, outdated_client_string)

            # these lines take two seconds
            self.send_chat(formatted_warning_message(self, KICK_DELAY + 2.0))
            callLater(0.5, self.send_chat, formatted_warning_message(self, KICK_DELAY + 1.5))
            callLater(1.0, self.send_chat, formatted_warning_message(self, KICK_DELAY + 1.0))
            callLater(1.5, self.send_chat, formatted_warning_message(self, KICK_DELAY + 0.5))
            callLater(2.0, self.send_chat, formatted_warning_message(self, KICK_DELAY))

            def kick_old_client(self, reason):
                self.kick(reason, self.team is None)

            callLater(KICK_DELAY + 2.0, kick_old_client, self, "Outdated client: %s" % outdated_client_string)

        def on_version_get(self):
            if self.team is not None and not self.showed_clin:  # spawned
                self.protocol.irc_say(formatted_client_info(self,self.name))
                print '%s ID %s %s' % (self.name, self.player_id,formatted_client_info(self,self.name))
                self.showed_clin = True

            version_i = self.client_info.version_major << 16 | self.client_info.version_minor << 8 | self.client_info.version_revision

            if self.client_info.client in MINIMUM_VERSIONS_I:
                if version_i < MINIMUM_VERSIONS_I[self.client_info.client]:
                    self.old_kick_timeout = callLater(5, self.on_outdated_version_get) # give them a little time to spawn

    class DetectclientProtocol(protocol):
        def __init__(self, *arg, **kw):
            return protocol.__init__(self, *arg, **kw)

    return DetectclientProtocol, DetectclientConnection
