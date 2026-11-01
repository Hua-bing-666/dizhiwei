"""Version-2 host wire reference. No LoRa driver or MCU implementation."""
from dataclasses import dataclass
from pathlib import Path
import binascii
import math
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'simulation/interface_review'))
from event_protocol import cobs_decode, cobs_encode, crc16

VERSION = 2
EVENT, ACK, TELEMETRY = 1, 2, 3
HEADER = struct.Struct('<BBHIII')
SAMPLE = struct.Struct('<IIIHIiiiBBBBB')
EVENT_DETAIL = struct.Struct('<BB')
LIMIT = 64
MISSING = -(2**31)
STATUS = {'valid': 0, 'healthy_reference_unconfirmed': 1, 'baseline_unavailable': 2,
          'pressure_quality': 3, 'window_incomplete': 4, 'operating_domain': 5}
PATTERN = {'no_current_evidence': 0, 'leak_pattern': 1, 'restriction_pattern': 2,
           'uncertain': 3, 'unavailable': 4}
EVENT_KIND = {'quality_transition': 1, 'measurement_quality': 2, 'rapid_review': 3,
              'leak_pattern': 4, 'restriction_pattern': 5, 'uncertain': 6}
REASON = {'nonfinite_pressure': 1, 'pressure_out_of_range': 2, 'counter_reset': 3, 'timing_fault': 4}


def uint(value, bits, nonzero=False):
    if not isinstance(value, int) or isinstance(value, bool) or not int(nonzero) <= value < 2**bits:
        raise ValueError(f'Invalid uint{bits}')


def quantize(value, multiplier):
    if value is None:
        return MISSING
    if not math.isfinite(value):
        raise ValueError('Use explicit null for missing measurements')
    result = round(value * multiplier)
    if not MISSING < result < 2**31:
        raise ValueError('Quantized measurement out of bounds')
    return result


@dataclass(frozen=True)
class Snapshot:
    uptime_ms: int
    sample_seq: int
    config_id: int
    reference_id: int
    cumulative_pulses: int
    p0: int
    p1: int
    q10: int
    status: int
    flags: int
    pattern: int
    p0_age_ms: int
    p1_age_ms: int

    def validate(self):
        for value in [self.uptime_ms, self.cumulative_pulses]:
            uint(value, 32)
        for value in [self.sample_seq, self.config_id]:
            uint(value, 32, True)
        uint(self.reference_id, 16)
        if self.status not in STATUS.values() or self.pattern not in PATTERN.values():
            raise ValueError('Unknown status or pattern')
        uint(self.flags, 8)
        if self.flags & 0x70:
            raise ValueError('Reserved flag bits set')
        for value, age in [(self.p0, self.p0_age_ms), (self.p1, self.p1_age_ms)]:
            if not isinstance(value, int) or not MISSING <= value < 2**31:
                raise ValueError('Invalid pressure integer')
            uint(age, 8)
            if (value == MISSING) != (age == 255) or age != 255 and age > 30:
                raise ValueError('Pressure age must be measured or explicitly unavailable')
        if not isinstance(self.q10, int) or not MISSING <= self.q10 < 2**31:
            raise ValueError('Invalid flow integer')
        numeric, approved, short_valid, short_active = [bool(self.flags & (1 << b)) for b in range(4)]
        if numeric and self.reference_id == 0:
            raise ValueError('Numeric baseline needs a registered reference')
        if not numeric and self.reference_id != 0:
            raise ValueError('Unavailable numeric baseline must use reference zero')
        if short_active and not short_valid or short_valid and not (numeric and approved):
            raise ValueError('Invalid rapid-attention flags')
        if self.status == STATUS['valid']:
            if not numeric or not approved or not (0 <= self.p0 <= 20000 and 1000 <= self.p1 <= 20000 and self.q10 >= 500):
                raise ValueError('Valid status conflicts with snapshot conditions')
            if self.pattern == PATTERN['unavailable']:
                raise ValueError('Valid status cannot have unavailable diagnosis')
        elif self.pattern != PATTERN['unavailable']:
            raise ValueError('Unavailable sample cannot carry a diagnostic pattern')
        if self.status in (STATUS['healthy_reference_unconfirmed'], STATUS['baseline_unavailable']) and (short_valid or short_active):
            raise ValueError('Unconfirmed baseline cannot carry rapid evidence')
        if self.status == STATUS['healthy_reference_unconfirmed'] and approved:
            raise ValueError('Unconfirmed health status conflicts with approval flag')
        if self.status == STATUS['baseline_unavailable'] and numeric:
            raise ValueError('Unavailable baseline conflicts with numeric flag')

    def pack(self):
        self.validate()
        return SAMPLE.pack(*self.__dict__.values())

    @classmethod
    def unpack(cls, payload):
        if len(payload) != SAMPLE.size:
            raise ValueError('Snapshot length')
        result = cls(*SAMPLE.unpack(payload))
        result.validate()
        return result


def snapshot_from_record(record, config_id=1, reference_id=1, ages=(0, 0), synthetic=True):
    # Internal sample index zero represents the first completed one-second bin.
    flags = sum(int(bool(record[key])) << bit for bit, key in enumerate([
        'numeric_baseline_available', 'healthy_reference_approved', 'rapid_window_valid', 'rapid_attention_active']))
    if synthetic:
        flags |= 0x80
    pressure = record['pressure_kpa']
    snap = Snapshot((record['t_s'] + 1) * 1000, record['t_s'] + 1, config_id,
                    reference_id if record['numeric_baseline_available'] else 0,
                    record['cumulative_pulses'], quantize(pressure[0], 100), quantize(pressure[1], 100),
                    quantize(record['flow_q10_l_min'], 1000), STATUS[record['measurement_status']], flags,
                    PATTERN[record['diagnostic_pattern']],
                    ages[0] if pressure[0] is not None else 255, ages[1] if pressure[1] is not None else 255)
    snap.validate()
    return snap


def event_payload(snapshot, event):
    code = EVENT_KIND[event['kind']]
    if code == EVENT_KIND['quality_transition']:
        detail = STATUS[event['previous']] if event['previous'] is not None else 255
    elif code == EVENT_KIND['measurement_quality']:
        detail = REASON[event['reason']]
    else:
        detail = 0
    return snapshot.pack() + EVENT_DETAIL.pack(code, detail)


def inspect_payload(kind, payload):
    if kind == ACK:
        if len(payload) != 4:
            raise ValueError('ACK fingerprint length')
        return None
    length = SAMPLE.size + (EVENT_DETAIL.size if kind == EVENT else 0)
    if len(payload) != length:
        raise ValueError('Uplink payload length')
    snap = Snapshot.unpack(payload[:SAMPLE.size])
    if kind == EVENT:
        code, detail = EVENT_DETAIL.unpack(payload[SAMPLE.size:])
        if code not in EVENT_KIND.values():
            raise ValueError('Unknown event code')
        if code == 1 and detail not in list(STATUS.values()) + [255]:
            raise ValueError('Invalid prior quality status')
        if code == 2 and detail not in REASON.values():
            raise ValueError('Unknown measurement-quality reason')
        if code >= 3:
            if detail != 0 or not (snap.flags & 3) == 3:
                raise ValueError('Diagnostic event conflicts with baseline')
            if code == 3 and not snap.flags & 8:
                raise ValueError('Rapid event needs active attention')
            if code >= 4 and snap.pattern != code - 3:
                raise ValueError('Diagnostic event differs from snapshot pattern')
    return snap


@dataclass(frozen=True)
class Frame:
    kind: int
    device: int
    session: int
    seq: int
    payload: bytes

    @property
    def key(self):
        return self.device, self.session, self.seq

    @property
    def body(self):
        if self.kind not in (EVENT, ACK, TELEMETRY):
            raise ValueError('Unknown frame type')
        for value in self.key:
            uint(value, 32, True)
        inspect_payload(self.kind, self.payload)
        return HEADER.pack(VERSION, self.kind, len(self.payload), *self.key) + self.payload

    @property
    def fingerprint(self):
        return binascii.crc32(self.body) & 0xffffffff

    def wire(self):
        body = self.body
        wire = cobs_encode(body + struct.pack('<H', crc16(body))) + b'\x00'
        if len(wire) > LIMIT:
            raise ValueError('Wire frame exceeds candidate module packet size')
        return wire


def decode(wire):
    if not wire.endswith(b'\x00') or len(wire) > LIMIT:
        raise ValueError('Wire boundary or length')
    raw = cobs_decode(wire[:-1])
    if len(raw) < HEADER.size + 2:
        raise ValueError('Short header')
    body = raw[:-2]
    if crc16(body) != struct.unpack('<H', raw[-2:])[0]:
        raise ValueError('CRC mismatch')
    version, kind, n, device, session, seq = HEADER.unpack(body[:HEADER.size])
    if version != VERSION or n != len(body) - HEADER.size:
        raise ValueError('Unsupported version or payload length')
    result = Frame(kind, device, session, seq, body[HEADER.size:])
    result.body
    return result


class StreamDecoder:
    def __init__(self):
        self.buffer = bytearray()
        self.discard = False
        self.errors = 0

    def feed(self, data):
        result = []
        for byte in data:
            if byte == 0:
                if self.buffer and not self.discard:
                    try:
                        result.append(decode(bytes(self.buffer) + b'\x00'))
                    except ValueError:
                        self.errors += 1
                self.buffer.clear()
                self.discard = False
            elif not self.discard:
                self.buffer.append(byte)
                if len(self.buffer) >= LIMIT:
                    self.buffer.clear()
                    self.discard = True
                    self.errors += 1
        return result
