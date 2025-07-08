import json
import random
from collections import namedtuple
from enum import Enum
from queue import Queue, Empty
from threading import Event, Thread
from time import perf_counter

import socks

from scanner.data import PortScanInfo, HostScanInfo, ScanResult, ScanResultStat, ServerInfo
from scanner.packets import CHandshakePacket, SHandshakePacket, CPingPacket, SPongPacket


def clear_queue(queue: Queue):
    while not queue.empty():
        queue.get()


class ThreadStat(Enum):
    WORKING = 0
    PAUSED = 1
    STOPPED = 2


ExceptionGroup = namedtuple("ExceptionGroup", ["timeout", "error_exception"])

CONNECT_GROUP = ExceptionGroup(ScanResultStat.CONNECT_TIMEOUT, ScanResultStat.COMMUNICATE_UNKNOWN_ERROR)
SEND_GROUP = ExceptionGroup(ScanResultStat.SEND_TIMEOUT, ScanResultStat.COMMUNICATE_UNKNOWN_ERROR)
READ_GROUP = ExceptionGroup(ScanResultStat.READ_TIMEOUT, ScanResultStat.COMMUNICATE_UNKNOWN_ERROR)


class Scanner:
    def __init__(self):
        self.in_scanning = False
        self.info: HostScanInfo | None = None

        self.pause_event = Event()
        self.resume_event = Event()
        self.stop_event = Event()

        self.action_response_stack: Queue[ThreadStat] = Queue()
        self.task_stack: Queue[PortScanInfo] = Queue()
        self.result_stack: Queue[ScanResult] = Queue()

        self.threads: dict[int, Thread] = {}
        self.thread_stats: dict[int, ThreadStat] = {}
        self.alive_threads: int = 0

    def config(self, scan_info: HostScanInfo):
        self.info = scan_info

    def start(self):
        clear_queue(self.task_stack)
        clear_queue(self.result_stack)
        for port_info in self.info:
            self.task_stack.put(port_info)
        for i in range(self.info.scan_thread_num):
            thread_id = int.from_bytes(random.randbytes(2), "big")
            thread = Thread(target=self.scan_thread, args=(thread_id,), name=f"ScanWorker-{i}", daemon=True)
            thread.start()
            self.threads[thread_id] = thread
            self.thread_stats[thread_id] = ThreadStat.WORKING

    def pause(self):
        self.pause_event.set()
        counter = 0
        while counter >= self.alive_threads:
            self.action_response_stack.get()
            counter += 1

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()
        for thread in self.threads.values():
            thread.join()
        clear_queue(self.action_response_stack)

    def scan_thread(self, thread_id: int):
        while self.stop_event.is_set():
            try:
                scan_info = self.task_stack.get(block=False)
            except Empty:
                break
            result = self.scan_func(scan_info)
            self.result_stack.put(result)
            self.task_stack.task_done()

            if self.pause_event.is_set():
                self.action_response_stack.put(ThreadStat.PAUSED)
                self.thread_stats[thread_id] = ThreadStat.PAUSED
                self.pause_event.wait()
                self.thread_stats[thread_id] = ThreadStat.WORKING

        self.thread_stats[thread_id] = ThreadStat.STOPPED
        self.alive_threads -= 1

    def scan_func(self, scan_info: PortScanInfo):
        sock = socks.socksocket()
        sock.set_proxy(**self.info.proxy_cfg)
        group = CONNECT_GROUP

        try:
            # 连接
            sock.settimeout(self.info.connect_timeout)
            sock.connect((scan_info.host, scan_info.port))

            # 握手包发送
            group = SEND_GROUP
            client_handshake = CHandshakePacket(
                scan_info.protocol_version,
                scan_info.host,
                scan_info.port,
                1,
            ).export()
            sock.settimeout(self.info.read_timeout)
            sock.send(client_handshake)

            # 读取握手包
            group = READ_GROUP
            packet = SHandshakePacket.load_packet(sock)
            server_info = ServerInfo.load(scan_info, -1, json.loads(packet.json_response))

            # 发送ping包
            group = SEND_GROUP
            sock.send(CPingPacket(0).export())
            timer = perf_counter()

            # 接收ping包
            try:
                group = READ_GROUP
                SPongPacket.load_packet(sock)
                ping = perf_counter() - timer
                server_info.ping = ping
            except TimeoutError:
                pass

            # 收尾
            sock.close()
            return ScanResult(ScanResultStat.SUCCESS, scan_info, server_info)
        except ConnectionRefusedError:
            stat = ScanResultStat.CONNECTION_REFUSED
            return ScanResult(stat, scan_info)
        except TimeoutError:
            stat = group.timeout
            return ScanResult(stat, scan_info)
        except Exception as e:
            stat = group.error_exception
            return ScanResult(stat, scan_info, error_exception=e)
