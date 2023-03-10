import enum
import struct
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

import objects.matches
import utils
from enums.actions import ActionType
from enums.game_mode import GameMode
from enums.mods import Mods
from enums.multiplayer import SlotStatus
from enums.presence import PresenceFilter

if TYPE_CHECKING:
    import objects.matches
    from objects.session import Session


@enum.unique
class ClientPackets(enum.IntEnum):
    """These are all the packet ids sent from the osu! client to the server."""

    CHANGE_ACTION = 0
    SEND_PUBLIC_MESSAGE = 1
    LOGOUT = 2
    REQUEST_STATUS_UPDATE = 3
    PING = 4
    START_SPECTATING = 16
    STOP_SPECTATING = 17
    SPECTATE_FRAMES = 18
    ERROR_REPORT = 20
    CANT_SPECTATE = 21
    SEND_PRIVATE_MESSAGE = 25
    PART_LOBBY = 29
    JOIN_LOBBY = 30
    CREATE_MATCH = 31
    JOIN_MATCH = 32
    PART_MATCH = 33
    MATCH_CHANGE_SLOT = 38
    MATCH_READY = 39
    MATCH_LOCK = 40
    MATCH_CHANGE_SETTINGS = 41
    MATCH_START = 44
    MATCH_SCORE_UPDATE = 47
    MATCH_COMPLETE = 49
    MATCH_CHANGE_MODS = 51
    MATCH_LOAD_COMPLETE = 52
    MATCH_NO_BEATMAP = 54
    MATCH_NOT_READY = 55
    MATCH_FAILED = 56
    MATCH_HAS_BEATMAP = 59
    MATCH_SKIP_REQUEST = 60
    CHANNEL_JOIN = 63
    BEATMAP_INFO_REQUEST = 68
    MATCH_TRANSFER_HOST = 70
    FRIEND_ADD = 73
    FRIEND_REMOVE = 74
    MATCH_CHANGE_TEAM = 77
    CHANNEL_PART = 78
    RECEIVE_UPDATES = 79
    SET_AWAY_MESSAGE = 82
    IRC_ONLY = 84
    USER_STATS_REQUEST = 85
    MATCH_INVITE = 87
    MATCH_CHANGE_PASSWORD = 90
    TOURNAMENT_MATCH_INFO_REQUEST = 93
    USER_PRESENCE_REQUEST = 97
    USER_PRESENCE_REQUEST_ALL = 98
    TOGGLE_BLOCK_NON_FRIEND_DMS = 99
    TOURNAMENT_JOIN_MATCH_CHANNEL = 108
    TOURNAMENT_LEAVE_MATCH_CHANNEL = 109


@enum.unique
class ServerPackets(enum.IntEnum):
    """These are all the packet ids sent by the server to the osu! client"""

    USER_ID = 5
    SEND_MESSAGE = 7
    PONG = 8
    HANDLE_IRC_CHANGE_USERNAME = 9
    HANDLE_IRC_QUIT = 10
    USER_STATS = 11
    USER_LOGOUT = 12
    SPECTATOR_JOINED = 13
    SPECTATOR_LEFT = 14
    SPECTATE_FRAMES = 15
    VERSION_UPDATE = 19
    SPECTATOR_CANT_SPECTATE = 22
    GET_ATTENTION = 23
    NOTIFICATION = 24
    UPDATE_MATCH = 26
    NEW_MATCH = 27
    DISPOSE_MATCH = 28
    TOGGLE_BLOCK_NON_FRIEND_DMS = 34
    MATCH_JOIN_SUCCESS = 36
    MATCH_JOIN_FAIL = 37
    FELLOW_SPECTATOR_JOINED = 42
    FELLOW_SPECTATOR_LEFT = 43
    ALL_PLAYERS_LOADED = 45
    MATCH_START = 46
    MATCH_SCORE_UPDATE = 48
    MATCH_TRANSFER_HOST = 50
    MATCH_ALL_PLAYERS_LOADED = 53
    MATCH_PLAYER_FAILED = 57
    MATCH_COMPLETE = 58
    MATCH_SKIP = 61
    UNAUTHORIZED = 62  # unused
    CHANNEL_JOIN_SUCCESS = 64
    CHANNEL_INFO = 65
    CHANNEL_KICK = 66
    CHANNEL_AUTO_JOIN = 67
    BEATMAP_INFO_REPLY = 69
    PRIVILEGES = 71
    FRIENDS_LIST = 72
    PROTOCOL_VERSION = 75
    MAIN_MENU_ICON = 76
    MONITOR = 80  # unused
    MATCH_PLAYER_SKIPPED = 81
    USER_PRESENCE = 83
    RESTART = 86
    MATCH_INVITE = 88
    CHANNEL_INFO_END = 89
    MATCH_CHANGE_PASSWORD = 91
    SILENCE_END = 92
    USER_SILENCED = 94
    USER_PRESENCE_SINGLE = 95
    USER_PRESENCE_BUNDLE = 96
    USER_DM_BLOCKED = 100
    TARGET_IS_SILENCED = 101
    VERSION_UPDATE_FORCED = 102
    SWITCH_SERVER = 103
    ACCOUNT_RESTRICTED = 104
    RTX = 105  # unused
    MATCH_ABORT = 106
    SWITCH_TOURNAMENT_SERVER = 107


@dataclass
class Action:
    action_type: ActionType
    info_text: str
    map_md5: str
    mods: Mods
    mode: GameMode
    map_id: int


@dataclass
class Message:
    sender: str  # TODO: should it always be an empty string?
    text: str
    reciever: str
    sender_id: int  # TODO: should it always be 0?


@dataclass
class Match:
    id: int = 0
    in_progress: bool = False

    powerplay: int = 0  # TODO: what is this
    mods: int = 0
    name: str = ""
    pass_word: str = ""

    map_name: str = ""
    map_id: int = 0
    map_md5: str = ""

    slot_statuses: list[int] = field(default_factory=list)  # i8
    slot_teams: list[int] = field(default_factory=list)  # i8
    slot_ids: list[int] = field(default_factory=list)  # i8

    host_id: int = 0

    game_mode: int = 0
    win_condition: int = 0
    team_type: int = 0

    freemods: bool = False
    slot_mods: list[int] = field(default_factory=list)

    seed: int = 0  # TODO: what is this


NO_PACKET_DATA = [
    ClientPackets.REQUEST_STATUS_UPDATE,
    ClientPackets.PING,
    ClientPackets.PART_MATCH
]  # no packet data is provided when this packet is sent to the server
USER_IDS = list[int]
CHANNEL_NAME = str

VALID_PACKET_DATA = Union[
    USER_IDS,
    Action,
    None,
    int,
    Message,
    PresenceFilter,
    CHANNEL_NAME,
    Match,
]


class PacketReader:
    def __init__(self, raw_data: bytes) -> None:
        self.raw_data: bytes = raw_data
        self.offset: int = 0
        self.packet_id: ClientPackets = self.read_packet_id()
        self.length: int = self.read_packet_length()

    @property
    def buffer_data(self):
        return self.raw_data[self.offset :]

    def read_packet_length(self) -> int:
        length = self.read_unsigned_int()  # self.read_int()
        return length

    def read_packet_id(self) -> ClientPackets:
        packet_id = self.read_custom(
            fmt="Hx",
            buffer=self.buffer_data[:3],
            offset=3,
        )[0]

        return ClientPackets(packet_id)

    def packet_data(self) -> VALID_PACKET_DATA:
        if self.packet_id in NO_PACKET_DATA:
            return None

        parsing_functions = {
            ClientPackets.CHANGE_ACTION: self.read_action,
            ClientPackets.USER_STATS_REQUEST: self.read_user_stats_request,
            ClientPackets.SEND_PUBLIC_MESSAGE: self.read_message,
            ClientPackets.SEND_PRIVATE_MESSAGE: self.read_message,
            ClientPackets.RECEIVE_UPDATES: self.read_presence_filter,
            ClientPackets.LOGOUT: self.read_logout,
            ClientPackets.CHANNEL_PART: self.read_channel_name,
            ClientPackets.CHANNEL_JOIN: self.read_channel_name,
            ClientPackets.JOIN_LOBBY: self.read_join_lobby,
            ClientPackets.PART_LOBBY: self.read_part_lobby,
            ClientPackets.CREATE_MATCH: self.read_match,
            ClientPackets.START_SPECTATING: self.read_start_spectating,
            ClientPackets.MATCH_CHANGE_SETTINGS: self.read_match,
        }

        if self.packet_id not in parsing_functions:
            raise Exception(f"Need to read packet data from {self.packet_id.name}")

        return parsing_functions[self.packet_id]()

    def read_start_spectating(self) -> int:
        return self.read_int()

    def read_match(self) -> Match:
        match = Match(
            id=self.read_short(),
            in_progress=self.read_byte() == 1,
            powerplay=self.read_byte(),
            mods=self.read_int(),
            name=self.read_string(),
            pass_word=self.read_string(),
            map_name=self.read_string(),
            map_id=self.read_int(),
            map_md5=self.read_string(),
            slot_statuses=[self.read_byte() for _ in range(16)],
            slot_teams=[self.read_byte() for _ in range(16)],
        )

        for status in match.slot_statuses:
            if status & SlotStatus.HAS_PLAYER:
                match.slot_ids.append(self.read_int())

        match.host_id = self.read_int()
        match.game_mode = self.read_byte()
        match.win_condition = self.read_byte()
        match.team_type = self.read_byte()
        match.freemods = self.read_byte() == 1

        if match.freemods:
            match.slot_mods = [self.read_int() for _ in range(16)]

        match.seed = self.read_int()  # used for mania random mod

        return match

    def read_part_lobby(self) -> None:
        return None

    def read_join_lobby(self) -> None:
        return None

    def read_channel_name(self) -> CHANNEL_NAME:
        return self.read_string()

    def read_logout(self) -> None:
        self.read_int()
        return None

    def read_presence_filter(self) -> PresenceFilter:
        return PresenceFilter(self.read_int())  # TODO: read unsigned int?

    def read_message(self) -> Message:
        return Message(
            sender=self.read_string(),
            text=self.read_string(),
            reciever=self.read_string(),
            sender_id=self.read_int(),  # TODO: read unsigned int?
        )

    def read_user_stats_request(self) -> USER_IDS:
        return list(
            self.read_i32_list_i16l(),
        )

    def read_action(self) -> Action:
        action_type = ActionType(
            self.read_unsigned_byte(),
        )

        info_text = self.read_string()

        map_md5 = self.read_string()

        mods, game_mode = utils.ensure_mods_and_gamemode(
            mods=self.read_unsigned_int(),
            game_mode=self.read_unsigned_byte(),
        )

        map_id = self.read_int()

        return Action(
            action_type=action_type,
            info_text=info_text,
            map_md5=map_md5,
            mods=mods,
            mode=game_mode,
            map_id=map_id,
        )

    def read_unsigned_int(self) -> int:
        (val,) = struct.unpack("<I", self.buffer_data[:4])
        self.offset += 4
        return val

    def read_unsigned_byte(self) -> int:
        (val,) = struct.unpack("<B", self.buffer_data[:1])
        self.offset += 1
        return val

    def read_byte(self) -> int:
        (val,) = struct.unpack("<b", self.buffer_data[:1])
        self.offset += 1
        return val  # val - 256 if val > 127 else val

    def read_short(self) -> int:
        (val,) = struct.unpack("<h", self.buffer_data[:2])
        self.offset += 2
        return val

    def read_int(self) -> int:
        (val,) = struct.unpack("<i", self.buffer_data[:4])
        self.offset += 4
        return val

    def read_long_long(self) -> int:
        (val,) = struct.unpack("<q", self.buffer_data[:8])
        self.offset += 8
        return val

    def read_double(self) -> int:
        (val,) = struct.unpack("<d", self.buffer_data[:8])
        self.offset += 8
        return val

    def read_uleb128(self) -> int:
        val = shift = 0

        while True:
            b = self.buffer_data[0]
            self.offset += 1

            val |= (b & 0b01111111) << shift
            if (b & 0b10000000) == 0:
                break

            shift += 7

        return val

    def read_string(self) -> str:
        if self.read_byte() == 0x0B:
            return self.read_raw(self.read_uleb128()).decode()

        return ""

    def read_raw(self, length: int) -> bytes:
        val = self.buffer_data[:length]
        self.offset += length
        return val

    def read_custom(self, fmt: str, buffer: bytes, offset: int) -> tuple[Any]:
        val = struct.unpack(f"<{fmt}", buffer)
        self.offset += offset
        return val

    def read_i32_list_i16l(self) -> tuple[int]:
        length = self.read_short()

        offset = length * 4

        return self.read_custom(
            fmt="I" * length,
            buffer=self.buffer_data[:offset],
            offset=offset,
        )


@dataclass
class Packet:
    id: ClientPackets
    data: VALID_PACKET_DATA

    @property
    def name(self) -> str:
        return f"ClientPackets.{self.id.name}"


def read_packets(client_packets: bytes) -> list[Packet]:
    packets = []

    reader = PacketReader(client_packets)

    while reader.buffer_data:

        packets.append(
            Packet(
                id=reader.packet_id,
                data=reader.packet_data(),
            )
        )

        if not reader.buffer_data:
            break

        reader = PacketReader(reader.buffer_data)

    if not packets:
        packets.append(
            Packet(
                id=reader.packet_id,
                data=reader.packet_data(),
            )
        )

    return packets


def write_uleb128(num: int) -> bytes:
    if num == 0:
        return bytearray(b"\x00")

    ret = bytearray()
    length = 0

    while num > 0:
        ret.append(num & 0b01111111)
        num >>= 7
        if num != 0:
            ret[length] |= 0b10000000
        length += 1

    return bytes(ret)


def write_string(string: str) -> bytes:
    s = string.encode()
    return b"\x0b" + write_uleb128(len(s)) + s


def write_int(i: int) -> bytes:
    return struct.pack("<i", i)


def write_unsigned_int(i: int) -> bytes:
    return struct.pack("<I", i)


def write_float(f: float) -> bytes:
    return struct.pack("<f", f)


def write_byte(b: int) -> bytes:
    return struct.pack("<b", b)


def write_unsigned_byte(b: int) -> bytes:
    return struct.pack("<B", b)


def write_short(s: int) -> bytes:
    return struct.pack("<h", s)


def write_unsigned_short(s: int) -> bytes:
    return struct.pack("<H", s)


def write_long_long(l: int) -> bytes:
    return struct.pack("<q", l)


def write_list_32(l: Sequence[int]) -> bytes:
    ret = bytearray(write_short(len(l)))

    for item in l:
        ret += write_int(item)

    return bytes(ret)


def write_packet(packet_id: int, *packet_data: bytes) -> bytes:
    packet = bytearray(struct.pack("<Hx", packet_id))

    for data in packet_data:
        packet += data

    packet[3:3] = struct.pack("<I", len(packet) - 3)
    return bytes(packet)


def user_id(user_id: int) -> bytes:
    write = write_unsigned_int if user_id > 0 else write_int
    return write_packet(
        ServerPackets.USER_ID,
        write(user_id),
    )


def notification(message: str) -> bytes:
    return write_packet(
        ServerPackets.NOTIFICATION,
        write_string(message),
    )


def protocol_version(version: int = 19):
    return write_packet(
        ServerPackets.PROTOCOL_VERSION,
        write_int(version),
    )


def bancho_privileges(bancho_privleges: int) -> bytes:
    return write_packet(
        ServerPackets.PRIVILEGES,
        write_int(bancho_privleges),
    )


def user_presence(
    user_id: int,
    user_name: str,
    utc_offset: int,
    country: int,
    bancho_privleges: int,
    mode: int,
    location: tuple[float, float],
    rank: int,
) -> bytes:
    return write_packet(
        ServerPackets.USER_PRESENCE,
        write_int(user_id),
        write_string(user_name),
        write_unsigned_byte(utc_offset + 24),
        write_unsigned_byte(country),
        write_unsigned_byte(bancho_privleges | mode << 5),
        write_float(location[0]),
        write_float(location[1]),
        write_int(rank),
    )


def user_stats(
    user_id: int,
    action: int,
    info_text: str,
    map_md5: str,
    mods: int,
    mode: int,
    map_id: int,
    ranked_score: int,
    acc: float,
    playcount: int,
    total_score: int,
    rank: int,
    pp: int,
) -> bytes:
    return write_packet(
        ServerPackets.USER_STATS,
        write_int(user_id),
        write_byte(action),
        write_string(info_text),
        write_string(map_md5),
        write_int(mods),
        write_unsigned_byte(mode),
        write_int(map_id),
        write_long_long(ranked_score),
        write_float(acc / 100.0),
        write_int(playcount),
        write_long_long(total_score),
        write_int(rank),
        write_short(pp),
    )


def menu_icon(menu_image: str, redirect_url: str) -> bytes:
    return write_packet(
        ServerPackets.MAIN_MENU_ICON, write_string(f"{menu_image}|{redirect_url}")
    )


def channel_info_end() -> bytes:
    return write_packet(ServerPackets.CHANNEL_INFO_END)


def channel_join(channel_name: str) -> bytes:
    return write_packet(
        ServerPackets.CHANNEL_JOIN_SUCCESS,
        write_string(channel_name),
    )


def channel_info(
    channel_name: str,
    channel_description: str,
    channel_player_count: int,
) -> bytes:
    return write_packet(
        ServerPackets.CHANNEL_INFO,
        write_string(channel_name),
        write_string(channel_description),
        write_short(channel_player_count),
    )


def channel_kick(
    channel_name: str,
) -> bytes:
    return write_packet(
        ServerPackets.CHANNEL_KICK,
        write_string(channel_name),
    )


def friends_list(friends: Optional[Sequence[int]] = None) -> bytes:
    if friends is None:
        friends = []

    return write_packet(
        ServerPackets.FRIENDS_LIST,
        write_list_32(friends),
    )


def system_restart(miliseconds: int = 0) -> bytes:
    return write_packet(
        ServerPackets.RESTART,
        write_int(miliseconds),
    )


def logout(user_id: int) -> bytes:
    return write_packet(
        ServerPackets.USER_LOGOUT,
        write_int(user_id),
        write_unsigned_byte(0),
    )


def send_message(
    senders_name: str,
    message: str,
    target_channel_or_user: str,
    sender_user_id: int,
) -> bytes:
    return write_packet(
        ServerPackets.SEND_MESSAGE,
        write_string(senders_name),
        write_string(message),
        write_string(target_channel_or_user),
        write_int(sender_user_id),
    )


def user_silenced(userid: int) -> bytes:
    return write_packet(
        ServerPackets.USER_SILENCED,
        write_int(userid),
    )


def pack_osu_session_stats(session: "Session") -> bytes:
    return user_stats(
        user_id=session.account.user_id,
        action=session.osu_client.status.action,
        info_text=session.osu_client.status.info_text,  # TODO
        map_md5=session.osu_client.status.map_md5,
        mods=session.osu_client.status.mods,
        mode=session.osu_client.status.mode.as_osu_client,
        map_id=session.osu_client.status.map_id,
        ranked_score=0,  # TODO:
        acc=100.0,  # TODO
        playcount=0,  # TODO:
        total_score=0,  # TODO:
        rank=1,  # TODO:
        pp=2000,  # TODO:
    )


def pack_osu_session_presence(session: "Session") -> bytes:
    return user_presence(
        user_id=session.account.user_id,
        user_name=session.account.user_name,
        utc_offset=session.utc_offset,
        country=session.osu_client.country_code_to_client_code(
            session.account.country_code
        ),
        bancho_privleges=session.osu_client.server_to_client_privileges(
            session.privileges
        ),
        mode=session.osu_client.status.mode.as_osu_client,
        location=(0.0, 0.0),  # TODO: longitude, latitude
        rank=1,  # TODO
    )


def pack_osu_session(session: "Session") -> bytes:
    return pack_osu_session_presence(session) + pack_osu_session_stats(session)


def match_join_fail() -> bytes:
    return write_packet(ServerPackets.MATCH_JOIN_FAIL)


def match_join_sucess(
    match: "objects.matches.Match",
    send_pass_word: bool = True,
) -> bytes:
    pass_word = b""

    # what is this and what is going on
    if match.pass_word:
        if send_pass_word:
            pass_word = write_string(match.pass_word)
        else:
            pass_word = b"\x0b\x00"
    else:
        pass_word = b"\x00"

    free_mod = write_byte(match.free_mod)
    if match.free_mod:
        for slot in match.slots:
            free_mod += write_unsigned_int(slot.mods)

    return write_packet(
        ServerPackets.MATCH_JOIN_SUCCESS,
        write_unsigned_short(match.id),
        write_byte(match.in_progress),
        write_byte(0),
        write_unsigned_int(match.mods),
        write_string(match.name),
        pass_word,
        write_string(match.name),
        write_int(match.current_map.id),
        write_string(match.current_map.md5),
        *[write_byte(slot.status) for slot in match.slots],
        *[write_byte(slot.team) for slot in match.slots],
        *[
            write_unsigned_int(slot.user_id)
            for slot in match.slots
            if slot.status & SlotStatus.HAS_PLAYER and slot.user_id
        ],
        write_unsigned_int(match.host_id),
        write_byte(match.game_mode),
        write_byte(match.win_condition),
        write_byte(match.team_type),
        free_mod,
        write_byte(match.seed),
    )
