"""
Standalone parser test — no Ollama needed.
Tests the byte-position parser with demo data.
"""

import json
from parser.icedis_parser import parse_icedis_file


def pad(s, length):
    return str(s).ljust(length)


def padn(n, length):
    return str(n).zfill(length)


def build_demo_file():
    """Build a valid demo ICEDIS file in memory."""

    # File Header (type 0)
    header = (
        '0' +
        pad('SwetsLisse001', 20) +
        pad('Swets & Zeitlinger BV', 30) +
        '060321' +
        'ORDERS' +
        '0930' +
        pad('', 593)
    )

    # Order record (type 1) — Title A
    order1 = (
        '1' +
        pad('13601385', 8) +
        pad('7014385', 20) +
        pad('Nature Biotechnology', 90) +
        pad('PUB-SUB-001', 20) +
        pad('AGT-23792305', 20) +
        pad('Brian Green', 45) +
        pad('BIC/EDItEUR', 45) +
        pad('39-41 North Road', 45) +
        pad('London N7 9DP', 45) +
        pad('UK', 45) +
        pad('', 45) +
        pad('', 45) +
        'R' +           # Renewal
        'N' +           # Address unchanged
        '031006' +      # Start date
        '041005' +      # End date
        padn(147, 5) +  # Start volume
        padn(158, 5) +  # End volume
        padn(1, 5) +    # Start issue
        padn(4, 5) +    # End issue
        '1' +           # Airmail
        pad('CHQ-001', 10) +
        'USD' +
        padn(3625000, 10) +   # 36250.00
        padn(10, 4) +
        pad('', 20) +
        pad('Renewal confirmed', 72) +
        padn(362500, 10) +    # postal 3625.00
        padn(725000, 10) +    # tax 7250.00
        padn(45000, 10) +     # tax on postal 450.00
        pad('', 2)
    )

    # Title Subtotal (type 7) — closes Title A
    subtotal1 = (
        '7' +
        pad('13601385', 8) +
        pad('7014385', 20) +
        pad('Nature Biotechnology', 90) +
        padn(1, 8) +
        padn(10, 8) +
        pad('', 8) +
        'USD' + padn(3625000, 12) +
        pad('', 367)
    )

    # Order record (type 1) — Title B
    order2 = (
        '1' +
        pad('00278122', 8) +
        pad('8823991', 20) +
        pad('Journal of Biological Chemistry', 90) +
        pad('PUB-SUB-002', 20) +
        pad('AGT-44512001', 20) +
        pad('John Smith', 45) +
        pad('Rockefeller University', 45) +
        pad('1114 First Avenue', 45) +
        pad('New York NY 10021', 45) +
        pad('USA', 45) +
        pad('', 45) +
        pad('', 45) +
        'N' +           # New order
        'U' +           # Address unknown
        '060101' +
        '061231' +
        padn(0, 5) +
        padn(0, 5) +
        padn(0, 5) +
        padn(0, 5) +
        '0' +           # Standard delivery
        pad('', 10) +
        'EUR' +
        padn(15000000, 10) +  # 150000.00
        padn(5, 4) +
        pad('', 20) +
        pad('', 72) +
        padn(0, 10) +
        padn(0, 10) +
        padn(0, 10) +
        pad('', 2)
    )

    # Title Subtotal (type 7) — closes Title B
    subtotal2 = (
        '7' +
        pad('00278122', 8) +
        pad('8823991', 20) +
        pad('Journal of Biological Chemistry', 90) +
        padn(1, 8) +
        padn(5, 8) +
        pad('', 8) +
        'EUR' + padn(15000000, 12) +
        pad('', 367)
    )

    # Control Total (type 9)
    control = (
        '9' +
        pad('', 118) +
        padn(2, 8) +     # 2 orders
        padn(15, 8) +    # 15 copies
        padn(8, 8) +     # 8 records
        'USD' + padn(3625000, 12) +
        'EUR' + padn(15000000, 12) +
        pad('', 337)
    )

    return '\n'.join([
        header,
        order1,
        subtotal1,
        order2,
        subtotal2,
        control,
    ])


def run_tests():
    print("Running ICEDIS parser tests...\n")

    demo = build_demo_file()
    result = parse_icedis_file(demo)

    tests = [
        ("File header exists",
            result['file_header'] is not None),

        ("Sender name correct",
            result['file_header']['sender_name'] == 'Swets & Zeitlinger BV'),

        ("File identifier correct",
            result['file_header']['file_identifier'] == 'ORDERS'),

        ("Two title groups found",
            len(result['title_groups']) == 2),

        ("Two orders found",
            len(result['orders']) == 2),

        ("Title A journal name correct",
            result['title_groups'][0]['journal_title'] == 'Nature Biotechnology'),

        ("Title A ISSN correct",
            result['title_groups'][0]['issn'] == '13601385'),

        ("Order 1 type decoded correctly",
            result['orders'][0]['order_type'] == 'R – Renewal'),

        ("Order 1 remittance correct",
            result['orders'][0]['agent_remittance'] == '36250.00'),

        ("Order 1 start date correct",
            result['orders'][0]['renewal_period_start_date'] == '06/10/03'),

        ("Order 1 delivery decoded correctly",
            result['orders'][0]['delivery_method_indicator'] == '1 – Airmail'),

        ("Order 1 customer address correct",
            'Brian Green' in result['orders'][0]['customer_name_and_address']),

        ("Order 2 type decoded correctly",
            result['orders'][1]['order_type'] == 'N – New order'),

        ("Order 2 currency correct",
            result['orders'][1]['currency_code'] == 'EUR'),

        ("Control total exists",
            result['control_total'] is not None),

        ("Control total order count correct",
            result['control_total']['number_of_orders'] == '00000002'),

        ("Control total has USD currency",
            any(c['code'] == 'USD' for c in result['control_total']['currencies'])),

        ("Validation passes",
            result['validation']['is_valid'] == True),

        ("No parse errors",
            len(result['parse_errors']) == 0),
    ]

    passed = 0
    failed = 0

    for name, condition in tests:
        if condition:
            print(f"  ✓  {name}")
            passed += 1
        else:
            print(f"  ✗  {name}")
            failed += 1

    print(f"\n{passed}/{len(tests)} tests passed")

    if failed > 0:
        print("\nFull result for debugging:")
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run_tests()