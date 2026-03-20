const { parseICEDISFile } = require('./icedisParser');
const fs = require('fs');

// ── Option A: test with your real file ────────
// Place your ICEDIS file in the same folder as test.js
// then run:  node test.js myfile.txt

const filename = process.argv[2];

if (filename) {
  const raw = fs.readFileSync(filename, 'utf-8');
  const result = parseICEDISFile(raw);
  console.log(JSON.stringify(result, null, 2));

} else {
  // ── Option B: built-in demo data ─────────────
  // Manually constructed lines that match the spec exactly

  const pad = (str, len) => String(str).padEnd(len, ' ');
  const padN = (num, len) => String(num).padStart(len, '0');

  // File Header (type 0)
  const header =
    '0' +
    pad('SwetsLisse001', 20) +
    pad('Swets & Zeitlinger BV', 30) +
    '060321' +
    'ORDERS' +
    '0930' +
    pad('', 593);

  // Order record (type 1) — Title A
  const order1 =
    '1' +
    pad('13601385', 8) +          // ISSN
    pad('7014385', 20) +          // Publisher title ref
    pad('Nature Biotechnology', 90) + // Journal title
    pad('PUB-SUB-001', 20) +      // Publisher sub ref
    pad('AGT-23792305', 20) +     // Agent sub ref
    pad('Brian Green', 45) +      // Address line 1
    pad('BIC/EDItEUR', 45) +      // Address line 2
    pad('39-41 North Road', 45) + // Address line 3
    pad('London N7 9DP', 45) +    // Address line 4
    pad('UK', 45) +               // Address line 5
    pad('', 45) +                 // Address line 6
    pad('', 45) +                 // Address line 7
    'R' +                         // Order type: Renewal
    'N' +                         // Change of address: No
    '031006' +                    // Renewal start: 06/10/03
    '041005' +                    // Renewal end:   05/10/04
    padN(147, 5) +                // Start volume
    padN(158, 5) +                // End volume
    padN(1, 5) +                  // Start issue
    padN(4, 5) +                  // End issue
    '1' +                         // Delivery: Airmail
    pad('CHQ-MT03034987', 10) +   // Agent payment ref
    'USD' +                       // Currency
    padN(3625000, 10) +           // Remittance: 36250.00
    padN(10, 4) +                 // Qty: 10
    pad('', 20) +                 // Prev year ref
    pad('Renewal confirmed', 72) +// Publisher notes
    padN(362500, 10) +            // Postal fees: 3625.00
    padN(725000, 10) +            // Sales tax: 7250.00
    padN(45000, 10) +             // Tax on postal: 450.00
    pad('', 2);                   // Unused

  // E-Journal record (type 3) — Title A
  const ejournal1 =
    '3' +
    pad('13601385', 8) +
    pad('7014385', 20) +
    pad('Nature Biotechnology', 90) +
    pad('PUB-SUB-001', 20) +
    pad('AGT-23792305', 20) +
    '1' +                          // Method of access: Independent system
    'R' +                          // Order type: Renewal
    '20031006' +                   // Access start
    '20041005' +                   // Access end
    '19970608' +                   // Backfile start
    '20041005' +                   // Backfile end
    pad('CUST-001', 20) +          // Agent customer ID
    pad('BIC/EDItEUR', 45) +       // Account name
    pad('Brian Green', 45) +       // Admin contact
    pad('brian@bic.org.uk', 40) +  // Admin email
    pad('+44 207 607 0021', 30) +  // Admin phone
    pad('', 30) +                  // Admin fax
    pad('EPUB-001', 20) +          // Publisher elec sub ref
    pad('Ingenta', 45) +           // Online service provider
    'Y' +                          // User-ID flag
    pad('Bookworm', 25) +          // User ID
    pad('Swordfish', 25) +         // Password
    pad('PROVID-12345', 40) +      // Provider access number
    padN(500, 8) +                 // FTEs
    padN(350, 8) +                 // Workstations
    padN(200, 8) +                 // Users
    padN(5, 8) +                   // Sites
    'Y' +                          // Consortium flag
    pad('PALINET', 50) +           // Consortium name
    padN(7, 5) +                   // IP ranges count
    '2';                           // Rate: Consortium

  // IP Address record (type 4) — Title A
  const ip1 =
    '4' +
    pad('13601385', 8) +
    pad('7014385', 20) +
    pad('Nature Biotechnology', 90) +
    pad('PUB-SUB-001', 20) +
    pad('AGT-23792305', 20) +
    pad('27.293.141.222-27.293.141.229;192.168.1.0-192.168.1.255', 501);

  // Title Subtotal (type 7) — closes Title A group
  const subtotal1 =
    '7' +
    pad('13601385', 8) +
    pad('7014385', 20) +
    pad('Nature Biotechnology', 90) +
    padN(1, 8) +                   // 1 order
    padN(10, 8) +                  // 10 copies
    pad('', 8) +                   // unused
    'USD' + padN(3625000, 12) +    // USD value
    pad('', 367);                  // unused

  // Order record (type 1) — Title B
  const order2 =
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
    'N' +                          // New order
    'U' +                          // Address unknown
    '060101' +
    '061231' +
    padN(0, 5) +
    padN(0, 5) +
    padN(0, 5) +
    padN(0, 5) +
    '0' +                          // Standard delivery
    pad('', 10) +
    'EUR' +
    padN(15000000, 10) +           // 150000.00
    padN(5, 4) +
    pad('', 20) +
    pad('', 72) +
    padN(0, 10) +
    padN(0, 10) +
    padN(0, 10) +
    pad('', 2);

  // Title Subtotal (type 7) — closes Title B group
  const subtotal2 =
    '7' +
    pad('00278122', 8) +
    pad('8823991', 20) +
    pad('Journal of Biological Chemistry', 90) +
    padN(1, 8) +
    padN(5, 8) +
    pad('', 8) +
    'EUR' + padN(15000000, 12) +
    pad('', 367);

  // Control Total (type 9)
  const control =
    '9' +
    pad('', 118) +
    padN(2, 8) +                   // 2 orders total
    padN(15, 8) +                  // 15 copies total
    padN(8, 8) +                   // 8 records total
    'USD' + padN(3625000, 12) +
    'EUR' + padN(15000000, 12) +
    pad('', 367);

  const demoFile = [
    header, order1, ejournal1, ip1, subtotal1,
    order2, subtotal2,
    control,
  ].join('\n');

  const result = parseICEDISFile(demoFile);
  console.log(JSON.stringify(result, null, 2));
}