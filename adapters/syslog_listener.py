import argparse
import socketserver
from datetime import datetime, timezone
try:
    from common.logger import get_logger
except Exception:
    import os
    import sys
    sys.path.append(os.getcwd())
    from common.logger import get_logger  # type: ignore

logger = get_logger(__name__)


try:
    from adapters.writer import write_jsonl
except Exception:
    import os
    import sys as _sys
    _sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip(), errors="ignore")
        rec = {
            "source": "syslog",
            "client": f"{self.client_address[0]}:{self.client_address[1]}",
            "message": data,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        write_jsonl(self.server.output_path, [rec])


def main():
    logger.info('starting syslog_listener.py')
    ap = argparse.ArgumentParser(description="Syslog UDP server → JSONL")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5140)  # non-privileged
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    class _Server(socketserver.UDPServer):
        pass

    _Server.allow_reuse_address = True
    server = _Server((args.host, args.port), SyslogUDPHandler)
    server.output_path = args.output  # type: ignore

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()