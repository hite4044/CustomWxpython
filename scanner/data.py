from base64 import b64decode
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import Iterable
from uuid import UUID

from PIL import Image

from scanner.motd import MOTD


class ErrorData:
    def __init__(self, msg: str):
        self.msg = msg


@dataclass
class Player:
    name: str
    uuid: UUID

    @classmethod
    def from_json(cls, json):
        return cls(json["name"], UUID(json["uuid"]))

    def __hash__(self):
        return hash(self.name.encode("utf-8") + self.uuid.bytes)


@dataclass
class PortScanInfo:
    host: str
    port: int
    protocol_version: int = -1


@dataclass
class ServerInfo:
    scan_info: PortScanInfo

    ping: float

    version_name: str
    version_protocol: int
    player_max: int
    player_online: int
    sample: list[Player] | None
    description: MOTD
    thumbnail: Image.Image | None

    @classmethod
    def load(cls, scan_info: PortScanInfo, ping: float, json: dict):
        def content(*paths, default=None):
            result: int | float | str | dict | list = json
            for path in paths:
                result = result.get(path)
                if result is None:
                    return default
            return result

        favicon = content("favicon")
        if favicon:
            if not favicon.startswith("data:image/png;base64,"):
                favicon = ErrorData('图标数据不以 [data:image/png;base64,] 起始')
            else:
                try:
                    favicon = Image.open(BytesIO(b64decode(favicon[22:])))
                except ValueError:
                    favicon = ErrorData("图标base64数据解码错误")
                except Image.UnidentifiedImageError:
                    favicon = ErrorData("图标文件数据错误")
        return cls(
            scan_info,
            ping,
            content("version", "name", default=ErrorData("未知")),
            content("version", "protocol", default=0),
            content("players", "max", default=-1),
            content("players", "online", default=-1),
            [Player.from_json(player) for player in content("players", "sample", default=[])],
            MOTD(content("description")),
            favicon)


@dataclass
class HostScanInfo:
    scan_thread_num: int

    host: str
    ports: Iterable[int]
    connect_timeout: float
    read_timeout: float

    proxy_cfg: dict | None = None

    def __iter__(self):
        for port in self.ports:
            yield PortScanInfo(self.host, port)


class ScanResultStat(Enum):
    CONNECTION_REFUSED = 0  # 拒绝连接 - ConnectionRefusedError
    CONNECT_TIMEOUT = 1  # 连接超时 - TimeoutError
    CONNECT_UNKNOWN_ERROR = 2  # 连接时的未知错误 - Exception

    READ_TIMEOUT = 3  # 读取超时 - TimeoutError
    SEND_TIMEOUT = 4  # 发送超时 - TimeoutError
    JSON_DECODE_ERROR = 5  # JSON解析错误 - JSONDecodeError
    COMMUNICATE_UNKNOWN_ERROR = 6  #

    UNKNOWN_ERROR = 7

    SUCCESS = 8


@dataclass
class ScanResult:
    stat: ScanResultStat
    scan_info: PortScanInfo

    info: ServerInfo | None = None
    error_exception: Exception | None = None



if __name__ == "__main__":
    import socket

    socket.create_connection(("ld.frp.one", 13559), 0.01)
