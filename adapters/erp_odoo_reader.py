import argparse
import sys
import json
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
    import xmlrpc.client as xmlrpclib
    HAS_XMLRPC = True
except Exception:
    HAS_XMLRPC = False

try:
    from adapters.writer import write_jsonl
except Exception:
    import os
    sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore

def main():
    logger.info('starting erp_odoo_reader.py')
    ap = argparse.ArgumentParser(description="ERP (Odoo) reader → JSONL via XML-RPC")
    ap.add_argument("--url", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--model", default="res.partner")
    ap.add_argument("--domain", default="[]")
    ap.add_argument("--fields", default='["name","create_date"]')
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if not HAS_XMLRPC:
        print("xmlrpc not available", file=sys.stderr)
        sys.exit(2)

    common = xmlrpclib.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        print("Authentication failed", file=sys.stderr)
        sys.exit(3)

    models = xmlrpclib.ServerProxy(f"{args.url}/xmlrpc/2/object")
    domain = json.loads(args.domain)
    fields = json.loads(args.fields)

    recs = models.execute_kw(args.db, uid, args.password, args.model, "search_read",
                             [domain], {"fields": fields, "limit": args.limit})

    out = []
    for r in recs:
        out.append({"source":"ERP_Odoo","model":args.model,"record":r,"ts":datetime.now(timezone.utc).isoformat()})
    write_jsonl(args.output, out)

if __name__ == "__main__":
    main()