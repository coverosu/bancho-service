from typing import Any, Callable, Optional, Sequence

import packets
from objects.channels import Channel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from objects.session import Session


class Channels(list[Channel]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_from_name(self, name: str) -> Optional[Channel]:
        for channel in self:
            if channel.name == name:
                return channel

    def add(self, channel: Channel) -> None:
        self.append(channel)

    @classmethod
    def from_channels(cls, channel_list: list[Channel]) -> "Channels":
        channels = cls()
        channels.extend(channel_list)
        return channels


class Sessions(list["Session"]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __len__(self) -> int:
        no_bot = [sess for sess in self if not sess.is_bot]
        return len(no_bot)

    def get_from_token(self, token: str) -> Optional["Session"]:
        session = [s for s in self if s.cho_token == token]

        if not session:
            return None
        else:
            return session[0]

    def get_from_user_id(self, user_id: int) -> Optional["Session"]:
        session = [s for s in self if s.account.user_id == user_id]

        if not session:
            return None
        else:
            return session[0]

    def get_from_user_name(self, user_name: str) -> Optional["Session"]:
        session = [s for s in self if s.account.user_name == user_name]

        if not session:
            return None
        else:
            return session[0]

    def get_from_user_ids(self, user_ids: list[int]) -> Optional[list["Session"]]:
        session = [s for s in self if s.account.user_id in user_ids]

        if not session:
            return None
        else:
            return session

    #def get_bot(self) -> "Bot":
    #    # TODO: fix this typing
    #    return [session for session in self if session.is_bot][0]  # type: ignore

    def send_to_all(self, data: bytes) -> None:
        for session in self:
            if session.is_bot:
                continue

            session.osu_client.packet_queue += data

    def send_to_all_but(
        self,
        excluded: list["Session"],
        data: bytes,
    ) -> None:
        for session in self:
            if session.is_bot:
                continue

            if session in excluded:
                continue

            session.osu_client.packet_queue += data

    def collect_all_sessions_for(self, session: "Session") -> bytes:
        data = bytearray()

        user_id = session.account.user_id

        for session in self:
            if session.account.user_id == user_id:
                continue

            data += packets.pack_osu_session(session)

        return bytes(data)

    # def send_to_all_if(
    #    self,
    #    condition: Callable[["Session"], bool],
    #    data: bytes,
    # ) -> None:
    #    ...

    # def collect_all_data(self) -> bytes:
    #    ...
