def test_imports_smoke():
    try:
        import adapters.can_reader
        import adapters.modbus_reader
        import adapters.pcap_reader
        import adapters.syslog_listener
        import adapters.opcua_reader
        import adapters.erp_odoo_reader
    except Exception as e:
        assert False, f"Import error: {e}"
