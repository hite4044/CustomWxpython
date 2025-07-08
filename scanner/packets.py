import struct
from dataclasses import dataclass
from io import BytesIO
from typing import cast as type_cast

import varint


class Packet:
    def __init__(self, packet_id: int | None = None, content: BytesIO | None = None):
        self.packet_id = packet_id
        self.content = content or BytesIO()

    @classmethod
    def load_packet(cls, stream):
        packet = cls(varint.decode_stream(stream), stream)
        return packet

    def write_varint(self, value: int):
        self.content.write(varint.encode(value))

    def read_varint(self) -> int:
        return varint.decode_stream(self.content)

    def write_string(self, value: str):
        data = value.encode("utf-8")
        self.content.write(varint.encode(len(data)) + data)

    def read_string(self) -> str:
        length = self.read_varint()
        return self.content.read(length).decode("utf-8")

    def write_unsigned_short(self, value: int):
        self.content.write(struct.pack(">H", value))

    def read_unsigned_short(self) -> int:
        return struct.unpack(">H", self.content.read(2))[0]

    def write_long(self, value: int):
        self.content.write(struct.pack(">Q", value))

    def read_long(self) -> int:
        return struct.unpack(">Q", self.content.read(8))[0]

    def export(self):
        if self.packet_id is None:
            raise ValueError("Packet ID is not set")
        return varint.encode(len(self.content.getbuffer())) + varint.encode(self.packet_id) + self.content


class CHandshakePacket(Packet):
    protocol_version: int
    server_address: str
    server_port: int
    next_state: int

    def __init__(self, protocol_version: int, server_address: str, server_port: int, next_state: int):
        super().__init__(0x00)
        self.protocol_version = protocol_version
        self.server_address = server_address
        self.server_port = server_port
        self.next_state = next_state

        self.write_varint(self.protocol_version)
        self.write_string(self.server_address)
        self.write_unsigned_short(self.server_port)
        self.write_varint(self.next_state)


class SHandshakePacket(Packet):
    json_response: str

    def __init__(self, packet_id: int, content: BytesIO):
        super().__init__(packet_id, content)
        self.json_response = self.read_string()

    @classmethod
    def load_packet(cls, stream) -> "SHandshakePacket":
        return type_cast(SHandshakePacket, Packet.load_packet(stream))


class CPingPacket(Packet):
    time: int

    def __init__(self, time: int):
        super().__init__(0x01)
        self.time = time
        self.write_long(self.time)

    @classmethod
    def load_packet(cls, stream) -> "CPingPacket":
        return type_cast(CPingPacket, Packet.load_packet(stream))


class SPongPacket(Packet):
    time: int

    def __init__(self, packet_id: int, content: BytesIO):
        super().__init__(packet_id, content)
        self.time = self.read_long()

    @classmethod
    def load_packet(cls, stream) -> "SPongPacket":
        return type_cast(SPongPacket, Packet.load_packet(stream))


