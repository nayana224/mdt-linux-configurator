from __future__ import annotations

import argparse

from mdt_configurator.protocol.definitions import get_pid
from mdt_configurator.protocol.packet import MID_BLDC, MID_MMI, Packet
from mdt_configurator.services.session import Session
from mdt_configurator.transport.serial_transport import list_serial_ports


def _hex_bytes(text: str) -> bytes:
    cleaned = text.replace(" ", "").replace(":", "")
    if len(cleaned) % 2:
        raise argparse.ArgumentTypeError("hex data must contain complete bytes")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mdt-configurator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ports", help="list serial ports")

    read = sub.add_parser("read", help="request one PID")
    read.add_argument("--port", required=True)
    read.add_argument("--baud", type=int, default=19200)
    read.add_argument("--id", type=int, default=1)
    read.add_argument("--pid", type=int, required=True)

    pkt = sub.add_parser("packet", help="build and preview a write/command packet")
    pkt.add_argument("--id", type=int, default=1)
    pkt.add_argument("--pid", type=int, required=True)
    pkt.add_argument("--data", type=_hex_bytes, default=b"")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "ports":
        for port in list_serial_ports():
            print(port)
        return

    if args.command == "packet":
        packet = Packet(MID_BLDC, MID_MMI, args.id, args.pid, args.data)
        info = get_pid(args.pid)
        if info:
            print(f"{info.name} [{info.access}] - {info.description}")
        print(packet.hex())
        return

    if args.command == "read":
        session = Session()
        try:
            session.connect(args.port, args.baud, args.id)
            packet = session.request_pid(args.pid)
            info = get_pid(args.pid)
            if info:
                print(f"{info.name}: {info.description}")
            print(f"RX PID={packet.pid} DATA={packet.data.hex(' ')}")
        finally:
            session.disconnect()


if __name__ == "__main__":
    main()
