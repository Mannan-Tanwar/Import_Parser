# ─────────────────────────────────────────────
# ICEDIS Fixed-Width Parser
# Agent → Publisher messages only
# Based on ICEDIS Messages & Implementation Guidelines v4
# ─────────────────────────────────────────────


# ── Helpers ──────────────────────────────────

def trim(s):
    """Remove leading/trailing whitespace from a string."""
    if not s:
        return ''
    return s.strip()


def date6(s):
    """
    Convert YYMMDD → DD/MM/YY
    Used in Order records (Table 6)
    """
    v = trim(s)
    if not v or v == '000000':
        return ''
    return f"{v[4:6]}/{v[2:4]}/{v[0:2]}"


def date8(s):
    """
    Convert CCYYMMDD → DD/MM/YYYY
    Used in E-Journal records (Table 6b)
    """
    v = trim(s)
    if not v or v == '00000000':
        return ''
    return f"{v[6:8]}/{v[4:6]}/{v[0:4]}"


def parse_value(s):
    """
    Convert ICEDIS value field to decimal string.
    10-digit numeric with 2 implied decimal places.
    e.g. 0000036250 → 362.50
    """
    v = trim(s)
    if not v:
        return ''
    try:
        n = int(v)
        return f"{n / 100:.2f}"
    except ValueError:
        return v


def decode(code, code_map):
    """
    Decode a single-character code using a lookup map.
    Returns 'CODE – Meaning' or just the raw code if not found.
    """
    if not code:
        return ''
    code = code.strip()
    if code in code_map:
        return f"{code} – {code_map[code]}"
    return code


# ── Code Maps ────────────────────────────────

CODE_MAPS = {
    'order_type': {
        'R': 'Renewal',
        'N': 'New order',
        'T': 'Transfer to this agent',
        'E': 'Electronic upgrade',
    },
    'delivery_method': {
        '0': 'Standard',
        '1': 'Airmail',
        '2': 'Registered',
        '3': 'Air freight',
        '4': 'First class mail',
        '5': 'Other',
        '6': 'Deeply discounted rate',
    },
    'change_of_address': {
        'Y': 'Yes – changed',
        'N': 'No – unchanged',
        'U': 'Unknown',
    },
    'method_of_access': {
        '0': 'Agent system',
        '1': 'Independent system',
        '2': 'Both agent & independent',
        '3': 'Publisher system',
        '4': 'Both agent & publisher',
        'U': 'Unknown',
    },
    'rate_indicator': {
        '0': 'Normal',
        '1': 'Deeply discounted',
        '2': 'Consortium',
        '3': 'Tier one',
        '4': 'Tier two',
        '5': 'Tier three',
        '6': 'Tier four',
        '7': 'Tier five',
        '8': 'Tier six',
    },
    'yes_no': {
        'Y': 'Yes',
        'N': 'No',
    },
}


# ── Address Decoder ───────────────────────────

def decode_address(raw):
    """
    Decode a 315-char address block into a readable string.
    Structure: 7 lines × 45 characters each.
    Empty lines are dropped.
    """
    lines = []
    for i in range(7):
        line = trim(raw[i * 45:(i + 1) * 45])
        if line:
            lines.append(line)
    return ', '.join(lines)


# ── Currency Block Decoder ────────────────────

def decode_currencies(line, start_pos):
    """
    Extract up to 10 currency/value pairs from a repeating block.
    Each pair = 3 chars (currency code) + 12 chars (value).
    Total per slot = 15 chars.
    """
    results = []
    for i in range(10):
        base = start_pos + (i * 15)
        code = trim(line[base:base + 3])
        value = parse_value(line[base + 3:base + 15])
        if code:
            results.append({'code': code, 'value': value})
    return results


# ── Safe Char Access ──────────────────────────

def char_at(line, pos):
    """
    Safely get a single character at a position.
    Returns empty string if line is too short.
    """
    if pos < len(line):
        return line[pos]
    return ''


# ── Record Parsers ────────────────────────────

def parse_file_header(line):
    """
    Table 1 — File Header (Record type 0)
    Total length: 660 chars
    """
    return {
        'record_type': '0',
        'label': 'File Header',
        'sender_reference': trim(line[1:21]),      # pos 2–21,  length 20
        'sender_name':      trim(line[21:51]),     # pos 22–51, length 30
        'creation_date':    date6(line[51:57]),    # pos 52–57, YYMMDD
        'file_identifier':  trim(line[57:63]),     # pos 58–63, length 6
        'creation_time':    trim(line[63:67]),     # pos 64–67, HHMM
    }


def parse_order_record(line):
    """
    Table 6 — Subscription Order / Renewal / Transfer (Record type 1)
    Total length: 660 chars
    """
    return {
        'record_type': '1',
        'label': 'Subscription Order / Renewal / Transfer',

        # ── Journal identification ──────────────
        'issn':                       trim(line[1:9]),      # pos 2–9
        'publisher_title_reference':  trim(line[9:29]),     # pos 10–29
        'journal_title':              trim(line[29:119]),   # pos 30–119

        # ── Subscription references ─────────────
        'publisher_subscription_ref': trim(line[119:139]),  # pos 120–139
        'agent_subscription_ref':     trim(line[139:159]),  # pos 140–159

        # ── Customer address ────────────────────
        # 315 chars = 7 lines × 45 chars, pos 160–474
        'customer_name_and_address':  decode_address(line[159:474]),

        # ── Order instruction ───────────────────
        'order_type':                 decode(char_at(line, 474), CODE_MAPS['order_type']),
        'change_of_address_indicator':decode(char_at(line, 475), CODE_MAPS['change_of_address']),

        # ── Subscription period ─────────────────
        'renewal_period_start_date':  date6(line[476:482]),  # pos 477–482
        'renewal_period_end_date':    date6(line[482:488]),  # pos 483–488
        'renewal_period_start_volume':trim(line[488:493]),   # pos 489–493
        'renewal_period_end_volume':  trim(line[493:498]),   # pos 494–498
        'renewal_period_start_issue': trim(line[498:503]),   # pos 499–503
        'renewal_period_end_issue':   trim(line[503:508]),   # pos 504–508

        # ── Delivery & payment ──────────────────
        'delivery_method_indicator':  decode(char_at(line, 508), CODE_MAPS['delivery_method']),
        'agent_payment_reference':    trim(line[509:519]),   # pos 510–519
        'currency_code':              trim(line[519:522]),   # pos 520–522
        'agent_remittance':           parse_value(line[522:532]),  # pos 523–532

        # ── Quantity & references ───────────────
        'subscription_quantity':          trim(line[532:536]),      # pos 533–536
        'agent_subscription_ref_prev_year':trim(line[536:556]),     # pos 537–556
        'publisher_notes':                trim(line[556:628]),      # pos 557–628

        # ── Tax & fees breakdown ────────────────
        'agent_remittance_postal_fees':   parse_value(line[628:638]),  # pos 629–638
        'agent_remittance_sales_tax':     parse_value(line[638:648]),  # pos 639–648
        'agent_remittance_tax_on_postal': parse_value(line[648:658]),  # pos 649–658
    }


def parse_end_user_address(line):
    """
    Table 6a — End User Address (Record type 2)
    Total length: 660 chars
    """
    return {
        'record_type': '2',
        'label': 'End User Address',
        'issn':                      trim(line[1:9]),
        'publisher_title_reference': trim(line[9:29]),
        'journal_title':             trim(line[29:119]),
        'publisher_subscription_ref':trim(line[119:139]),
        'agent_subscription_ref':    trim(line[139:159]),
        'end_user_name_and_address': decode_address(line[159:474]),  # pos 160–474
        'change_of_address_indicator':decode(char_at(line, 474), CODE_MAPS['change_of_address']),
    }


def parse_ejournal_info(line):
    """
    Table 6b — E-Journal Information (Record type 3)
    Total length: 660 chars
    """
    return {
        'record_type': '3',
        'label': 'E-Journal Information',

        # ── Identification ──────────────────────
        'issn':                      trim(line[1:9]),
        'publisher_title_reference': trim(line[9:29]),
        'journal_title':             trim(line[29:119]),
        'publisher_subscription_ref':trim(line[119:139]),
        'agent_subscription_ref':    trim(line[139:159]),

        # ── Access method & order type ──────────
        'method_of_access': decode(char_at(line, 159), CODE_MAPS['method_of_access']),
        'order_type':       decode(char_at(line, 160), CODE_MAPS['order_type']),

        # ── Access dates ────────────────────────
        'access_period_start_date': date8(line[161:169]),  # pos 162–169
        'access_period_end_date':   date8(line[169:177]),  # pos 170–177
        'backfile_start_date':      date8(line[177:185]),  # pos 178–185
        'backfile_end_date':        date8(line[185:193]),  # pos 186–193

        # ── Customer admin contacts ─────────────
        'agent_customer_id_code': trim(line[193:213]),  # pos 194–213
        'account_name':           trim(line[213:258]),  # pos 214–258
        'admin_contact_name':     trim(line[258:303]),  # pos 259–303
        'admin_email_address':    trim(line[303:343]),  # pos 304–343
        'admin_phone_number':     trim(line[343:373]),  # pos 344–373
        'admin_fax_number':       trim(line[373:403]),  # pos 374–403

        # ── Publisher e-access details ──────────
        'publisher_elec_sub_ref':    trim(line[403:423]),  # pos 404–423
        'online_service_provider':   trim(line[423:468]),  # pos 424–468

        # ── Credentials ─────────────────────────
        'user_id_password_flag':           decode(char_at(line, 468), CODE_MAPS['yes_no']),
        'user_id_requested_by_customer':   trim(line[469:494]),  # pos 470–494
        'password_requested_by_customer':  trim(line[494:519]),  # pos 495–519
        'provider_access_number':          trim(line[519:559]),  # pos 520–559

        # ── Licence metrics ──────────────────────
        'number_of_ftes':         trim(line[559:567]),  # pos 560–567
        'number_of_workstations': trim(line[567:575]),  # pos 568–575
        'number_of_users':        trim(line[575:583]),  # pos 576–583
        'number_of_sites':        trim(line[583:591]),  # pos 584–591

        # ── Consortium details ───────────────────
        'consortium_customer_flag': decode(char_at(line, 591), CODE_MAPS['yes_no']),
        'consortium_name':          trim(line[592:642]),  # pos 593–642
        'number_of_ip_ranges':      trim(line[642:647]),  # pos 643–647
        'rate_indicator':           decode(char_at(line, 647), CODE_MAPS['rate_indicator']),
    }


def parse_ip_addresses(line):
    """
    Table 6c — IP Addresses (Record type 4)
    Total length: 660 chars
    """
    raw_ips = trim(line[159:660])
    ip_ranges = [trim(ip) for ip in raw_ips.split(';') if trim(ip)]

    return {
        'record_type': '4',
        'label': 'IP Addresses',
        'issn':                      trim(line[1:9]),
        'publisher_title_reference': trim(line[9:29]),
        'journal_title':             trim(line[29:119]),
        'publisher_subscription_ref':trim(line[119:139]),
        'agent_subscription_ref':    trim(line[139:159]),
        'ip_address_ranges':         ip_ranges,  # list of IPs/ranges
    }


def parse_title_subtotal(line):
    """
    Table 2b — Title Subtotal (Record type 7)
    Total length: 660 chars
    """
    return {
        'record_type': '7',
        'label': 'Title Subtotal',
        'issn':                    trim(line[1:9]),    # pos 2–9
        'publisher_title_reference':trim(line[9:29]),  # pos 10–29
        'journal_title':           trim(line[29:119]), # pos 30–119
        'number_of_orders':        trim(line[119:127]),# pos 120–127
        'number_of_copies':        trim(line[127:135]),# pos 128–135
        'currencies':              decode_currencies(line, 143),
    }


def parse_control_total(line):
    """
    Table 3b — Control Total (Record type 9)
    Total length: 660 chars
    pos 2–119 are unused spaces in Agent→Publisher messages
    """
    return {
        'record_type': '9',
        'label': 'Control Total',
        'number_of_orders':  trim(line[119:127]),  # pos 120–127
        'number_of_copies':  trim(line[127:135]),  # pos 128–135
        'number_of_records': trim(line[135:143]),  # pos 136–143
        'currencies':        decode_currencies(line, 143),
    }


# ── Validation ────────────────────────────────

def validate_parsed_file(result):
    """
    Run validation checks on the parsed result.
    Returns dict with isValid flag and list of issues.
    """
    issues = []

    # Check 1 — file header present
    if not result['file_header']:
        issues.append({
            'severity': 'warning',
            'message': 'Missing File Header (type 0)'
        })

    # Check 2 — control total present
    if not result['control_total']:
        issues.append({
            'severity': 'error',
            'message': 'Missing Control Total (type 9)'
        })
    else:
        # Check 3 — order count matches
        try:
            declared = int(result['control_total']['number_of_orders'])
            actual   = len(result['orders'])
            if declared != actual:
                issues.append({
                    'severity': 'error',
                    'message': (
                        f"Order count mismatch: "
                        f"Control Total declares {declared}, "
                        f"found {actual} order records"
                    )
                })
        except (ValueError, TypeError):
            pass

    # Check 4 — file identifier
    if result['file_header']:
        fid = result['file_header'].get('file_identifier', '')
        if fid != 'ORDERS':
            issues.append({
                'severity': 'warning',
                'message': (
                    f"File identifier is '{fid}' "
                    f"— expected 'ORDERS' for Agent→Publisher messages"
                )
            })

    # Check 5 — mandatory fields on each order
    for i, order in enumerate(result['orders']):
        if not order.get('issn'):
            issues.append({
                'severity': 'warning',
                'message': f"Order {i + 1}: missing ISSN"
            })
        if not order.get('agent_subscription_ref'):
            issues.append({
                'severity': 'warning',
                'message': f"Order {i + 1}: missing Agent Subscription Reference"
            })
        if not order.get('journal_title'):
            issues.append({
                'severity': 'warning',
                'message': f"Order {i + 1}: missing Journal Title"
            })

    errors = [i for i in issues if i['severity'] == 'error']

    return {
        'is_valid': len(errors) == 0,
        'issues':   issues,
    }


# ── Master Parser ─────────────────────────────

def parse_icedis_file(raw_text):
    """
    Main entry point.
    Takes raw file content as a string.
    Returns fully structured and validated result dict.
    """

    # Split into lines, drop blanks
    lines = [l for l in raw_text.splitlines() if l.strip()]

    result = {
        'file_header':       None,
        'title_groups':      [],
        'orders':            [],
        'end_user_addresses':[],
        'ejournal_infos':    [],
        'ip_addresses':      [],
        'title_subtotals':   [],
        'control_total':     None,
        'unknown_records':   [],
        'parse_errors':      [],
        'meta': {
            'total_lines_read': len(lines),
            'source': 'text',
        },
    }

    current_group = None

    def open_new_group():
        return {
            'orders':            [],
            'end_user_addresses':[],
            'ejournal_infos':    [],
            'ip_addresses':      [],
            'subtotal':          None,
            'journal_title':     '',
            'issn':              '',
        }

    for index, line in enumerate(lines):
        if not line:
            continue

        record_type = line[0]

        try:
            # ── File-level records ──────────────
            if record_type == '0':
                result['file_header'] = parse_file_header(line)

            elif record_type == '9':
                result['control_total'] = parse_control_total(line)

            # ── Title-group records ─────────────
            elif record_type == '1':
                if current_group is None:
                    current_group = open_new_group()
                order = parse_order_record(line)
                current_group['orders'].append(order)
                result['orders'].append(order)

            elif record_type == '2':
                if current_group is None:
                    current_group = open_new_group()
                end_user = parse_end_user_address(line)
                current_group['end_user_addresses'].append(end_user)
                result['end_user_addresses'].append(end_user)

            elif record_type == '3':
                if current_group is None:
                    current_group = open_new_group()
                ejournal = parse_ejournal_info(line)
                current_group['ejournal_infos'].append(ejournal)
                result['ejournal_infos'].append(ejournal)

            elif record_type == '4':
                if current_group is None:
                    current_group = open_new_group()
                ip = parse_ip_addresses(line)
                current_group['ip_addresses'].append(ip)
                result['ip_addresses'].append(ip)

            # ── Type 7 = group terminator ────────
            elif record_type == '7':
                if current_group is None:
                    current_group = open_new_group()
                subtotal = parse_title_subtotal(line)
                current_group['subtotal']      = subtotal
                current_group['journal_title'] = subtotal['journal_title']
                current_group['issn']          = subtotal['issn']
                result['title_subtotals'].append(subtotal)
                result['title_groups'].append(current_group)
                current_group = None  # close the group

            else:
                result['unknown_records'].append({
                    'line':    index + 1,
                    'content': line,
                })

        except Exception as e:
            result['parse_errors'].append({
                'line':  index + 1,
                'type':  record_type,
                'error': str(e),
            })

    # Edge case — file ends without a closing type 7
    if current_group and current_group['orders']:
        current_group['journal_title'] = (
            current_group['orders'][0].get('journal_title', 'Unknown')
        )
        current_group['issn'] = (
            current_group['orders'][0].get('issn', '')
        )
        result['title_groups'].append(current_group)

    # Run validation
    result['validation'] = validate_parsed_file(result)

    return result