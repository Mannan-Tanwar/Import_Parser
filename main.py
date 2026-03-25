import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from parser.icedis_parser import parse_icedis_file
from vision.ollama_vision import (
    extract_text_from_image,
    extract_text_with_layout,
    check_tesseract_installed,
    parse_image_with_ollama,
    check_ollama_running,
)

console = Console()

TEXT_EXTENSIONS  = {'.txt', '.dat', '.edi', '.csv'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}


def print_full_output(result):
    """Print every field from the parsed ICEDIS result."""

    # ── File Header ───────────────────────────────────────────
    console.print("\n[bold cyan]═══ FILE HEADER ════════════════════════════════════[/bold cyan]")
    if result.get('file_header'):
        h = result['file_header']
        t = Table(show_header=True, header_style="bold white")
        t.add_column("Field",  style="dim", width=30)
        t.add_column("Value",  width=50)
        t.add_row("Record Type",       h.get('record_type', ''))
        t.add_row("Sender Reference",  h.get('sender_reference', ''))
        t.add_row("Sender Name",       h.get('sender_name', ''))
        t.add_row("Creation Date",     h.get('creation_date', ''))
        t.add_row("File Identifier",   h.get('file_identifier', ''))
        t.add_row("Creation Time",     h.get('creation_time', ''))
        console.print(t)
    else:
        console.print("[yellow]  No file header found[/yellow]")

    # ── Title Groups ──────────────────────────────────────────
    groups = result.get('title_groups', [])
    console.print(f"\n[bold cyan]═══ TITLE GROUPS ({len(groups)} found) ═════════════════════[/bold cyan]")

    for gi, group in enumerate(groups):
        console.print(f"\n[bold green]  ── Title Group {gi + 1}: {group.get('journal_title', 'Unknown')} ──[/bold green]")
        console.print(f"  ISSN: [cyan]{group.get('issn', '—')}[/cyan]")

        # ── Orders ────────────────────────────────────────────
        orders = group.get('orders', [])
        console.print(f"\n  [bold]Orders ({len(orders)})[/bold]")
        for oi, order in enumerate(orders):
            console.print(f"\n  [yellow]  Order {oi + 1}[/yellow]")
            t = Table(show_header=True, header_style="bold white", padding=(0, 1))
            t.add_column("Field",  style="dim", width=35)
            t.add_column("Value",  width=50)
            t.add_row("Record Type",                        order.get('record_type', ''))
            t.add_row("ISSN",                               order.get('issn', ''))
            t.add_row("Publisher Title Reference",          order.get('publisher_title_reference', ''))
            t.add_row("Journal Title",                      order.get('journal_title', ''))
            t.add_row("Publisher Subscription Ref",         order.get('publisher_subscription_ref', ''))
            t.add_row("Agent Subscription Ref",             order.get('agent_subscription_ref', ''))
            t.add_row("Customer Name & Address",            order.get('customer_name_and_address', ''))
            t.add_row("Order Type",                         order.get('order_type', ''))
            t.add_row("Change of Address Indicator",        order.get('change_of_address_indicator', ''))
            t.add_row("Renewal Period Start Date",          order.get('renewal_period_start_date', ''))
            t.add_row("Renewal Period End Date",            order.get('renewal_period_end_date', ''))
            t.add_row("Renewal Period Start Volume",        order.get('renewal_period_start_volume', ''))
            t.add_row("Renewal Period End Volume",          order.get('renewal_period_end_volume', ''))
            t.add_row("Renewal Period Start Issue",         order.get('renewal_period_start_issue', ''))
            t.add_row("Renewal Period End Issue",           order.get('renewal_period_end_issue', ''))
            t.add_row("Delivery Method Indicator",          order.get('delivery_method_indicator', ''))
            t.add_row("Agent Payment Reference",            order.get('agent_payment_reference', ''))
            t.add_row("Currency Code",                      order.get('currency_code', ''))
            t.add_row("Agent Remittance",                   order.get('agent_remittance', ''))
            t.add_row("Subscription Quantity",              order.get('subscription_quantity', ''))
            t.add_row("Agent Sub Ref (Previous Year)",      order.get('agent_subscription_ref_prev_year', ''))
            t.add_row("Publisher Notes",                    order.get('publisher_notes', ''))
            t.add_row("Agent Remittance — Postal Fees",     order.get('agent_remittance_postal_fees', ''))
            t.add_row("Agent Remittance — Sales Tax",       order.get('agent_remittance_sales_tax', ''))
            t.add_row("Agent Remittance — Tax on Postal",   order.get('agent_remittance_tax_on_postal', ''))
            console.print(t)

        # ── End User Addresses ────────────────────────────────
        end_users = group.get('end_user_addresses', [])
        console.print(f"\n  [bold]End User Addresses ({len(end_users)})[/bold]")
        if end_users:
            for ei, eu in enumerate(end_users):
                console.print(f"\n  [yellow]  End User {ei + 1}[/yellow]")
                t = Table(show_header=True, header_style="bold white", padding=(0, 1))
                t.add_column("Field",  style="dim", width=35)
                t.add_column("Value",  width=50)
                t.add_row("Record Type",                    eu.get('record_type', ''))
                t.add_row("ISSN",                           eu.get('issn', ''))
                t.add_row("Publisher Title Reference",      eu.get('publisher_title_reference', ''))
                t.add_row("Journal Title",                  eu.get('journal_title', ''))
                t.add_row("Publisher Subscription Ref",     eu.get('publisher_subscription_ref', ''))
                t.add_row("Agent Subscription Ref",         eu.get('agent_subscription_ref', ''))
                t.add_row("End User Name & Address",        eu.get('end_user_name_and_address', ''))
                t.add_row("Change of Address Indicator",    eu.get('change_of_address_indicator', ''))
                console.print(t)
        else:
            console.print("  [dim]  No end user address records[/dim]")

        # ── E-Journal Info ────────────────────────────────────
        ejournals = group.get('ejournal_infos', [])
        console.print(f"\n  [bold]E-Journal Information ({len(ejournals)})[/bold]")
        if ejournals:
            for ji, ej in enumerate(ejournals):
                console.print(f"\n  [yellow]  E-Journal Record {ji + 1}[/yellow]")
                t = Table(show_header=True, header_style="bold white", padding=(0, 1))
                t.add_column("Field",  style="dim", width=35)
                t.add_column("Value",  width=50)
                t.add_row("Record Type",                    ej.get('record_type', ''))
                t.add_row("ISSN",                           ej.get('issn', ''))
                t.add_row("Publisher Title Reference",      ej.get('publisher_title_reference', ''))
                t.add_row("Journal Title",                  ej.get('journal_title', ''))
                t.add_row("Publisher Subscription Ref",     ej.get('publisher_subscription_ref', ''))
                t.add_row("Agent Subscription Ref",         ej.get('agent_subscription_ref', ''))
                t.add_row("Method of Access",               ej.get('method_of_access', ''))
                t.add_row("Order Type",                     ej.get('order_type', ''))
                t.add_row("Access Period Start Date",       ej.get('access_period_start_date', ''))
                t.add_row("Access Period End Date",         ej.get('access_period_end_date', ''))
                t.add_row("Backfile Start Date",            ej.get('backfile_start_date', ''))
                t.add_row("Backfile End Date",              ej.get('backfile_end_date', ''))
                t.add_row("Agent Customer ID Code",         ej.get('agent_customer_id_code', ''))
                t.add_row("Account Name",                   ej.get('account_name', ''))
                t.add_row("Admin Contact Name",             ej.get('admin_contact_name', ''))
                t.add_row("Admin Email Address",            ej.get('admin_email_address', ''))
                t.add_row("Admin Phone Number",             ej.get('admin_phone_number', ''))
                t.add_row("Admin Fax Number",               ej.get('admin_fax_number', ''))
                t.add_row("Publisher Elec Sub Ref",         ej.get('publisher_elec_sub_ref', ''))
                t.add_row("Online Service Provider",        ej.get('online_service_provider', ''))
                t.add_row("User ID & Password Flag",        ej.get('user_id_password_flag', ''))
                t.add_row("User ID Requested by Customer",  ej.get('user_id_requested_by_customer', ''))
                t.add_row("Password Requested by Customer", ej.get('password_requested_by_customer', ''))
                t.add_row("Provider Access Number",         ej.get('provider_access_number', ''))
                t.add_row("Number of FTEs",                 ej.get('number_of_ftes', ''))
                t.add_row("Number of Workstations",         ej.get('number_of_workstations', ''))
                t.add_row("Number of Users",                ej.get('number_of_users', ''))
                t.add_row("Number of Sites",                ej.get('number_of_sites', ''))
                t.add_row("Consortium Customer Flag",       ej.get('consortium_customer_flag', ''))
                t.add_row("Consortium Name",                ej.get('consortium_name', ''))
                t.add_row("Number of IP Ranges",            ej.get('number_of_ip_ranges', ''))
                t.add_row("Rate Indicator",                 ej.get('rate_indicator', ''))
                console.print(t)
        else:
            console.print("  [dim]  No e-journal information records[/dim]")

        # ── IP Addresses ──────────────────────────────────────
        ips = group.get('ip_addresses', [])
        console.print(f"\n  [bold]IP Address Records ({len(ips)})[/bold]")
        if ips:
            for ii, ip in enumerate(ips):
                console.print(f"\n  [yellow]  IP Record {ii + 1}[/yellow]")
                t = Table(show_header=True, header_style="bold white", padding=(0, 1))
                t.add_column("Field",  style="dim", width=35)
                t.add_column("Value",  width=50)
                t.add_row("Record Type",                    ip.get('record_type', ''))
                t.add_row("ISSN",                           ip.get('issn', ''))
                t.add_row("Publisher Title Reference",      ip.get('publisher_title_reference', ''))
                t.add_row("Journal Title",                  ip.get('journal_title', ''))
                t.add_row("Publisher Subscription Ref",     ip.get('publisher_subscription_ref', ''))
                t.add_row("Agent Subscription Ref",         ip.get('agent_subscription_ref', ''))
                for ri, r in enumerate(ip.get('ip_address_ranges', [])):
                    t.add_row(f"IP Range {ri + 1}",         r)
                console.print(t)
        else:
            console.print("  [dim]  No IP address records[/dim]")

        # ── Title Subtotal ─────────────────────────────────────
        sub = group.get('subtotal')
        console.print(f"\n  [bold]Title Subtotal[/bold]")
        if sub:
            t = Table(show_header=True, header_style="bold white", padding=(0, 1))
            t.add_column("Field",  style="dim", width=35)
            t.add_column("Value",  width=50)
            t.add_row("Record Type",                    sub.get('record_type', ''))
            t.add_row("ISSN",                           sub.get('issn', ''))
            t.add_row("Publisher Title Reference",      sub.get('publisher_title_reference', ''))
            t.add_row("Journal Title",                  sub.get('journal_title', ''))
            t.add_row("Number of Orders",               sub.get('number_of_orders', ''))
            t.add_row("Number of Copies",               sub.get('number_of_copies', ''))
            for c in sub.get('currencies', []):
                t.add_row(f"Total Value ({c['code']})", c.get('value', ''))
            console.print(t)
        else:
            console.print("  [dim]  No subtotal record[/dim]")

    # ── Control Total ─────────────────────────────────────────
    console.print("\n[bold cyan]═══ CONTROL TOTAL ══════════════════════════════════[/bold cyan]")
    ctrl = result.get('control_total')
    if ctrl:
        t = Table(show_header=True, header_style="bold white")
        t.add_column("Field",  style="dim", width=30)
        t.add_column("Value",  width=50)
        t.add_row("Record Type",        ctrl.get('record_type', ''))
        t.add_row("Number of Orders",   ctrl.get('number_of_orders', ''))
        t.add_row("Number of Copies",   ctrl.get('number_of_copies', ''))
        t.add_row("Number of Records",  ctrl.get('number_of_records', ''))
        for c in ctrl.get('currencies', []):
            t.add_row(f"Total Value ({c['code']})", c.get('value', ''))
        console.print(t)
    else:
        console.print("[yellow]  No control total found[/yellow]")

    # ── Validation ─────────────────────────────────────────────
    console.print("\n[bold cyan]═══ VALIDATION ════════════════════════════════════[/bold cyan]")
    v = result.get('validation', {})
    if v.get('is_valid'):
        console.print("  [green]✓ File is valid — all checks passed[/green]")
    else:
        console.print("  [red]✗ File has errors[/red]")
    issues = v.get('issues', [])
    if issues:
        for issue in issues:
            icon  = "✗" if issue['severity'] == 'error' else "!"
            color = "red" if issue['severity'] == 'error' else "yellow"
            console.print(f"  [{color}]{icon} {issue['message']}[/{color}]")
    else:
        console.print("  [dim]No issues found[/dim]")

    errors = result.get('parse_errors', [])
    if errors:
        console.print("\n[bold red]═══ PARSE ERRORS ════════════════════════════════════[/bold red]")
        for e in errors:
            console.print(f"  [red]Line {e['line']} (type {e['type']}): {e['error']}[/red]")

    console.print("\n[dim]── End of parsed output ──[/dim]\n")


def print_image_text(image_path, extracted_text):
    """Print the raw text extracted from an image."""

    console.print(f"\n[bold cyan]═══ IMAGE TEXT EXTRACTION ══════════════════════════[/bold cyan]")
    console.print(f"[dim]File: {image_path}[/dim]\n")

    # Check if the text is JSON format (from AI model)
    if extracted_text.strip().startswith('{') or '```json' in extracted_text:
        try:
            # Extract JSON from markdown code blocks if present
            if '```json' in extracted_text:
                json_start = extracted_text.find('{')
                json_end = extracted_text.rfind('}') + 1
                json_str = extracted_text[json_start:json_end]
            else:
                json_str = extracted_text
            
            data = json.loads(json_str)
            
            # Display structured data nicely
            for section, content in data.items():
                console.print(f"\n[bold cyan]{section}[/bold cyan]")
                console.print("─" * 60)
                
                if isinstance(content, dict):
                    for key, value in content.items():
                        console.print(f"  [yellow]{key}:[/yellow] {value}")
                else:
                    console.print(f"  {content}")
            
            console.print("\n[dim]── End of extracted information ──[/dim]\n")
            return
            
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, fall back to regular display
            pass

    # Regular text display
    console.print(Panel(
        extracted_text,
        title="[bold white]Extracted Text[/bold white]",
        border_style="cyan",
        padding=(1, 2),
    ))

    console.print(f"\n[dim]Total characters extracted: {len(extracted_text)}[/dim]")
    console.print(f"[dim]Total lines extracted: {len(extracted_text.splitlines())}[/dim]")
    console.print("\n[dim]── End of extracted text ──[/dim]\n")


def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red]")
        console.print("  python main.py <file>              # parse a file")
        console.print("  python main.py <file> --json       # full JSON output (text files only)")
        console.print("  python main.py <file> --ai         # use AI vision model (images only)")
        console.print("\nSupported file types:")
        console.print("  Text:  .txt .dat .edi .csv")
        console.print("  Image: .png .jpg .jpeg .pdf")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    output_json = '--json' in sys.argv
    use_ai = '--ai' in sys.argv

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        sys.exit(1)

    ext = file_path.suffix.lower()

    # ── Path A: Text file → ICEDIS parser ────────────────────
    if ext in TEXT_EXTENSIONS:
        console.print(f"\n[bold]Parsing text file:[/bold] {file_path.name}")
        raw_text = file_path.read_text(encoding='utf-8', errors='replace')
        result   = parse_icedis_file(raw_text)

        if output_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_full_output(result)

    # ── Path B: Image → extract text ────────────────────
    elif ext in IMAGE_EXTENSIONS:
        console.print(f"\n[bold]Extracting text from image:[/bold] {file_path.name}")

        if use_ai:
            # Use Ollama AI vision model
            console.print("[cyan]Using AI vision model (Ollama)...[/cyan]")
            
            is_running, model_ok, msg = check_ollama_running()
            if not is_running or not model_ok:
                console.print(f"[red]{msg}[/red]")
                sys.exit(1)
            
            extracted_text = parse_image_with_ollama(file_path)
        else:
            # Use Tesseract OCR
            console.print("[cyan]Using Tesseract OCR...[/cyan]")
            
            is_installed, msg = check_tesseract_installed()
            if not is_installed:
                console.print(f"[red]{msg}[/red]")
                sys.exit(1)
            
            extracted_text = extract_text_with_layout(file_path)
        
        print_image_text(file_path.name, extracted_text)

    else:
        console.print(f"[red]Unsupported file type: {ext}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()