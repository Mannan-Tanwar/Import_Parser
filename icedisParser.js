// ─────────────────────────────────────────────
// ICEDIS Fixed-Width Parser
// Agent → Publisher messages only
// Based on ICEDIS Messages & Implementation Guidelines v4
// ─────────────────────────────────────────────

// ── Helpers ──────────────────────────────────

const trim = (s) => (s || '').trimEnd().trim();

const date6 = (s) => {
  const v = trim(s);
  if (!v || v === '000000') return '';
  return `${v.slice(4, 6)}/${v.slice(2, 4)}/${v.slice(0, 2)}`;
};

const date8 = (s) => {
  const v = trim(s);
  if (!v || v === '00000000') return '';
  return `${v.slice(6, 8)}/${v.slice(4, 6)}/${v.slice(0, 4)}`;
};

const parseValue = (s) => {
  const v = trim(s);
  if (!v) return '';
  const n = parseInt(v, 10);
  if (isNaN(n)) return v;
  return (n / 100).toFixed(2);
};

const decode = (code, map) =>
  map[code] ? `${code} – ${map[code]}` : trim(code) || '';

// ── Code Maps ────────────────────────────────

const CODE_MAPS = {
  orderType: {
    R: 'Renewal',
    N: 'New order',
    T: 'Transfer to this agent',
    E: 'Electronic upgrade',
  },
  deliveryMethod: {
    '0': 'Standard',
    '1': 'Airmail',
    '2': 'Registered',
    '3': 'Air freight',
    '4': 'First class mail',
    '5': 'Other',
    '6': 'Deeply discounted rate',
  },
  changeOfAddress: {
    Y: 'Yes – changed',
    N: 'No – unchanged',
    U: 'Unknown',
  },
  methodOfAccess: {
    '0': 'Agent system',
    '1': 'Independent system',
    '2': 'Both agent & independent',
    '3': 'Publisher system',
    '4': 'Both agent & publisher',
    U: 'Unknown',
  },
  rateIndicator: {
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
  yesNo: { Y: 'Yes', N: 'No' },
};

// ── Address decoder ───────────────────────────
// 315 chars = 7 lines × 45 chars each

const decodeAddress = (raw) => {
  const lines = [];
  for (let i = 0; i < 7; i++) {
    const line = trim(raw.slice(i * 45, (i + 1) * 45));
    if (line) lines.push(line);
  }
  return lines.join(', ');
};

// ── Currency block decoder ────────────────────
// Up to 10 currency/value pairs, each = 3 char code + 12 char value

const decodeCurrencies = (line, startPos) => {
  const results = [];
  for (let i = 0; i < 10; i++) {
    const base = startPos + i * 15;
    const code = trim(line.slice(base, base + 3));
    const value = parseValue(line.slice(base + 3, base + 15));
    if (code) results.push({ code, value });
  }
  return results;
};

// ── Record Parsers ────────────────────────────

// Table 1 — File Header (Record type 0)
const parseFileHeader = (line) => ({
  recordType: '0',
  label: 'File Header',
  senderReference:  trim(line.slice(1, 21)),
  senderName:       trim(line.slice(21, 51)),
  creationDate:     date6(line.slice(51, 57)),
  fileIdentifier:   trim(line.slice(57, 63)),
  creationTime:     trim(line.slice(63, 67)),
});

// Table 6 — Subscription Order / Renewal / Transfer (Record type 1)
const parseOrderRecord = (line) => ({
  recordType: '1',
  label: 'Subscription Order / Renewal / Transfer',
  issn:                         trim(line.slice(1, 9)),
  publisherTitleReference:      trim(line.slice(9, 29)),
  journalTitle:                 trim(line.slice(29, 119)),
  publisherSubscriptionRef:     trim(line.slice(119, 139)),
  agentSubscriptionRef:         trim(line.slice(139, 159)),
  customerNameAndAddress:       decodeAddress(line.slice(159, 474)),
  orderType:                    decode(line[474], CODE_MAPS.orderType),
  changeOfAddressIndicator:     decode(line[475], CODE_MAPS.changeOfAddress),
  renewalPeriodStartDate:       date6(line.slice(476, 482)),
  renewalPeriodEndDate:         date6(line.slice(482, 488)),
  renewalPeriodStartVolume:     trim(line.slice(488, 493)),
  renewalPeriodEndVolume:       trim(line.slice(493, 498)),
  renewalPeriodStartIssue:      trim(line.slice(498, 503)),
  renewalPeriodEndIssue:        trim(line.slice(503, 508)),
  deliveryMethodIndicator:      decode(line[508], CODE_MAPS.deliveryMethod),
  agentPaymentReference:        trim(line.slice(509, 519)),
  currencyCode:                 trim(line.slice(519, 522)),
  agentRemittance:              parseValue(line.slice(522, 532)),
  subscriptionQuantity:         trim(line.slice(532, 536)),
  agentSubscriptionRefPrevYear: trim(line.slice(536, 556)),
  publisherNotes:               trim(line.slice(556, 628)),
  agentRemittancePostalFees:    parseValue(line.slice(628, 638)),
  agentRemittanceSalesTax:      parseValue(line.slice(638, 648)),
  agentRemittanceTaxOnPostal:   parseValue(line.slice(648, 658)),
});

// Table 6a — End User Address (Record type 2)
const parseEndUserAddress = (line) => ({
  recordType: '2',
  label: 'End User Address',
  issn:                     trim(line.slice(1, 9)),
  publisherTitleReference:  trim(line.slice(9, 29)),
  journalTitle:             trim(line.slice(29, 119)),
  publisherSubscriptionRef: trim(line.slice(119, 139)),
  agentSubscriptionRef:     trim(line.slice(139, 159)),
  endUserNameAndAddress:    decodeAddress(line.slice(159, 474)),
  changeOfAddressIndicator: decode(line[474], CODE_MAPS.changeOfAddress),
});

// Table 6b — E-Journal Information (Record type 3)
const parseEJournalInfo = (line) => ({
  recordType: '3',
  label: 'E-Journal Information',
  issn:                        trim(line.slice(1, 9)),
  publisherTitleReference:     trim(line.slice(9, 29)),
  journalTitle:                trim(line.slice(29, 119)),
  publisherSubscriptionRef:    trim(line.slice(119, 139)),
  agentSubscriptionRef:        trim(line.slice(139, 159)),
  methodOfAccess:              decode(line[159], CODE_MAPS.methodOfAccess),
  orderType:                   decode(line[160], CODE_MAPS.orderType),
  accessPeriodStartDate:       date8(line.slice(161, 169)),
  accessPeriodEndDate:         date8(line.slice(169, 177)),
  backfileStartDate:           date8(line.slice(177, 185)),
  backfileEndDate:             date8(line.slice(185, 193)),
  agentCustomerIdCode:         trim(line.slice(193, 213)),
  accountName:                 trim(line.slice(213, 258)),
  adminContactName:            trim(line.slice(258, 303)),
  adminEmailAddress:           trim(line.slice(303, 343)),
  adminPhoneNumber:            trim(line.slice(343, 373)),
  adminFaxNumber:              trim(line.slice(373, 403)),
  publisherElecSubRef:         trim(line.slice(403, 423)),
  onlineServiceProvider:       trim(line.slice(423, 468)),
  userIdPasswordFlag:          decode(line[468], CODE_MAPS.yesNo),
  userIdRequestedByCustomer:   trim(line.slice(469, 494)),
  passwordRequestedByCustomer: trim(line.slice(494, 519)),
  providerAccessNumber:        trim(line.slice(519, 559)),
  numberOfFTEs:                trim(line.slice(559, 567)),
  numberOfWorkstations:        trim(line.slice(567, 575)),
  numberOfUsers:               trim(line.slice(575, 583)),
  numberOfSites:               trim(line.slice(583, 591)),
  consortiumCustomerFlag:      decode(line[591], CODE_MAPS.yesNo),
  consortiumName:              trim(line.slice(592, 642)),
  numberOfIPRanges:            trim(line.slice(642, 647)),
  rateIndicator:               decode(line[647], CODE_MAPS.rateIndicator),
});

// Table 6c — IP Addresses (Record type 4)
const parseIPAddresses = (line) => ({
  recordType: '4',
  label: 'IP Addresses',
  issn:                     trim(line.slice(1, 9)),
  publisherTitleReference:  trim(line.slice(9, 29)),
  journalTitle:             trim(line.slice(29, 119)),
  publisherSubscriptionRef: trim(line.slice(119, 139)),
  agentSubscriptionRef:     trim(line.slice(139, 159)),
  ipAddressRanges:          trim(line.slice(159, 660))
                              .split(';')
                              .map((s) => trim(s))
                              .filter(Boolean),
});

// Table 2b — Title Subtotal (Record type 7)
const parseTitleSubtotal = (line) => ({
  recordType: '7',
  label: 'Title Subtotal',
  issn:                   trim(line.slice(1, 9)),
  publisherTitleReference: trim(line.slice(9, 29)),
  journalTitle:           trim(line.slice(29, 119)),
  numberOfOrders:         trim(line.slice(119, 127)),
  numberOfCopies:         trim(line.slice(127, 135)),
  currencies:             decodeCurrencies(line, 143),
});

// Table 3b — Control Total (Record type 9)
const parseControlTotal = (line) => ({
  recordType: '9',
  label: 'Control Total',
  numberOfOrders:  trim(line.slice(119, 127)),
  numberOfCopies:  trim(line.slice(127, 135)),
  numberOfRecords: trim(line.slice(135, 143)),
  currencies:      decodeCurrencies(line, 143),
});

// ── Validation ────────────────────────────────

const validateParsedFile = (result) => {
  const issues = [];

  if (!result.fileHeader) {
    issues.push({ severity: 'warning', message: 'Missing File Header (type 0)' });
  }

  if (!result.controlTotal) {
    issues.push({ severity: 'error', message: 'Missing Control Total (type 9)' });
  } else {
    const declared = parseInt(result.controlTotal.numberOfOrders, 10);
    const actual   = result.orders.length;
    if (!isNaN(declared) && declared !== actual) {
      issues.push({
        severity: 'error',
        message: `Order count mismatch: Control Total says ${declared}, found ${actual} order records`,
      });
    }
  }

  result.orders.forEach((order, i) => {
    if (!order.issn)
      issues.push({ severity: 'warning', message: `Order ${i + 1}: missing ISSN` });
    if (!order.agentSubscriptionRef)
      issues.push({ severity: 'warning', message: `Order ${i + 1}: missing Agent Subscription Reference` });
    if (!order.journalTitle)
      issues.push({ severity: 'warning', message: `Order ${i + 1}: missing Journal Title` });
  });

  return {
    isValid: issues.filter((i) => i.severity === 'error').length === 0,
    issues,
  };
};

// ── Master Parser ─────────────────────────────

const parseICEDISFile = (rawText) => {
  const lines = rawText
    .split(/\r?\n/)
    .filter((l) => l.trim().length > 0);

  const result = {
    fileHeader:       null,
    titleGroups:      [],
    orders:           [],
    endUserAddresses: [],
    eJournalInfos:    [],
    ipAddresses:      [],
    titleSubtotals:   [],
    controlTotal:     null,
    unknownRecords:   [],
    parseErrors:      [],
    meta: { totalLinesRead: lines.length },
  };

  let currentGroup = null;

  const openNewGroup = () => ({
    orders:           [],
    endUserAddresses: [],
    eJournalInfos:    [],
    ipAddresses:      [],
    subtotal:         null,
    journalTitle:     '',
    issn:             '',
  });

  lines.forEach((line, index) => {
    const type = line[0];
    try {
      switch (type) {
        case '0':
          result.fileHeader = parseFileHeader(line);
          break;

        case '9':
          result.controlTotal = parseControlTotal(line);
          break;

        case '1': {
          if (!currentGroup) currentGroup = openNewGroup();
          const order = parseOrderRecord(line);
          currentGroup.orders.push(order);
          result.orders.push(order);
          break;
        }

        case '2': {
          if (!currentGroup) currentGroup = openNewGroup();
          const endUser = parseEndUserAddress(line);
          currentGroup.endUserAddresses.push(endUser);
          result.endUserAddresses.push(endUser);
          break;
        }

        case '3': {
          if (!currentGroup) currentGroup = openNewGroup();
          const ejournal = parseEJournalInfo(line);
          currentGroup.eJournalInfos.push(ejournal);
          result.eJournalInfos.push(ejournal);
          break;
        }

        case '4': {
          if (!currentGroup) currentGroup = openNewGroup();
          const ip = parseIPAddresses(line);
          currentGroup.ipAddresses.push(ip);
          result.ipAddresses.push(ip);
          break;
        }

        // type 7 = group terminator
        case '7': {
          if (!currentGroup) currentGroup = openNewGroup();
          const subtotal = parseTitleSubtotal(line);
          currentGroup.subtotal   = subtotal;
          currentGroup.journalTitle = subtotal.journalTitle;
          currentGroup.issn       = subtotal.issn;
          result.titleSubtotals.push(subtotal);
          result.titleGroups.push(currentGroup);
          currentGroup = null;
          break;
        }

        default:
          result.unknownRecords.push({ line: index + 1, content: line });
      }
    } catch (err) {
      result.parseErrors.push({ line: index + 1, type, error: err.message });
    }
  });

  // Edge case: last group has no closing type-7
  if (currentGroup && currentGroup.orders.length > 0) {
    currentGroup.journalTitle = currentGroup.orders[0]?.journalTitle || 'Unknown';
    currentGroup.issn         = currentGroup.orders[0]?.issn || '';
    result.titleGroups.push(currentGroup);
  }

  result.validation = validateParsedFile(result);
  return result;
};

// ── Exports ───────────────────────────────────
module.exports = { parseICEDISFile };