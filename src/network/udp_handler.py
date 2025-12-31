import socket
import struct
import cv2
import numpy as np
from typing import Generator, Dict

# =========================
# UDP Frame Protocol
# =========================
# [frame_id(2)][chunk_id(2)][total_chunks(2)][payload]
HEADER_FORMAT = "!HHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

MAX_UDP_PACKET_SIZE = 65507
MAX_PAYLOAD_SIZE = MAX_UDP_PACKET_SIZE - HEADER_SIZE


# =========================
# Sender (PC3)
# =========================
class UDPFrameSender:
    """
    UDP frame sender.
    - Compresses frame (JPEG)
    - Splits into chunks
    - Sends over UDP
    """

    def __init__(self, host: str, port: int, jpeg_quality: int = 80):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.jpeg_quality = jpeg_quality
        self._frame_id = 0

    def send_frame(self, frame) -> None:
        encoded = self._encode_frame(frame)
        self._send_encoded(encoded)

    def send_frame_raw(self, jpeg_bytes: bytes) -> None:
        """Send already-encoded JPEG bytes directly"""
        self._send_encoded(jpeg_bytes)

    def _send_encoded(self, encoded: bytes) -> None:
        """Internal method to send encoded bytes"""
        chunks = self._split_chunks(encoded)

        total_chunks = len(chunks)
        frame_id = self._next_frame_id()

        for chunk_id, payload in enumerate(chunks):
            header = struct.pack(
                HEADER_FORMAT,
                frame_id,
                chunk_id,
                total_chunks,
            )
            self.sock.sendto(header + payload, self.addr)

    def _encode_frame(self, frame) -> bytes:
        ok, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality],
        )
        if not ok:
            raise RuntimeError("Frame JPEG encoding failed")
        return buffer.tobytes()

    def _split_chunks(self, data: bytes):
        return [
            data[i : i + MAX_PAYLOAD_SIZE]
            for i in range(0, len(data), MAX_PAYLOAD_SIZE)
        ]

    def _next_frame_id(self) -> int:
        fid = self._frame_id
        self._frame_id = (self._frame_id + 1) % 65536
        return fid


# =========================
# Receiver (PC2)
# =========================
class UDPFrameReceiver:
    """
    UDP frame receiver.
    - Receives chunked packets
    - Reassembles frames
    - Yields decoded frames
    """

    def __init__(self, bind_ip: str, bind_port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((bind_ip, bind_port))

        self._frames: Dict[int, Dict] = {}

    def receive_packets(self) -> Generator[bytes, None, None]:
        """
        Yield reassembled JPEG bytes (NOT decoded frame)
        """
        while True:
            packet, _ = self.sock.recvfrom(MAX_UDP_PACKET_SIZE)
            data = self._handle_packet(packet)
            if data is not None:
                yield data

    def _handle_packet(self, packet: bytes):
        if len(packet) < HEADER_SIZE:
            return None

        header = packet[:HEADER_SIZE]
        payload = packet[HEADER_SIZE:]

        frame_id, chunk_id, total_chunks = struct.unpack(HEADER_FORMAT, header)

        frame_entry = self._frames.setdefault(
            frame_id,
            {"total": total_chunks, "chunks": {}},
        )

        frame_entry["chunks"][chunk_id] = payload

        if len(frame_entry["chunks"]) == frame_entry["total"]:
            data = b"".join(
                frame_entry["chunks"][i] for i in range(frame_entry["total"])
            )
            del self._frames[frame_id]
            return data

        return None

    def _decode_frame(self, data: bytes):
        nparr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
