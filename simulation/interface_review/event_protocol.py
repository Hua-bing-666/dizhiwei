"""Host-only wire/SQLite reference, not MCU firmware or measured LoRa.

Frames: COBS(header + payload + CRC16) + 00. CRCs detect accidental
corruption/conflicting keys; they do not authenticate a sender.
"""
from dataclasses import dataclass
import binascii,sqlite3,struct

VERSION=1;EVENT=1;ACK=2;TELEMETRY=3
HEADER=struct.Struct('<BBHIII');SNAPSHOT=struct.Struct('<IIHBBiii')
LIMIT=64;QUEUE_LIMIT=16;MAX_ATTEMPTS=8;TTL_S=300

def crc16(data):return binascii.crc_hqx(data,0xffff)
def cobs_encode(data):
    out=bytearray([0]);code_index=0;code=1
    for b in data:
        if b==0:
            out[code_index]=code;code_index=len(out);out.append(0);code=1
        else:
            out.append(b);code+=1
            if code==255:out[code_index]=code;code_index=len(out);out.append(0);code=1
    out[code_index]=code;return bytes(out)
def cobs_decode(data):
    if not data or 0 in data:raise ValueError('COBS zero/empty')
    out=bytearray();i=0
    while i<len(data):
        code=data[i];end=i+code
        if end>len(data):raise ValueError('COBS truncated')
        out.extend(data[i+1:end]);i=end
        if code<255 and i<len(data):out.append(0)
    return bytes(out)

@dataclass(frozen=True)
class Frame:
    kind:int
    device:int
    session:int
    seq:int
    payload:bytes
    @property
    def key(self):return self.device,self.session,self.seq
    @property
    def body(self):return HEADER.pack(VERSION,self.kind,len(self.payload),*self.key)+self.payload
    @property
    def fingerprint(self):return binascii.crc32(self.body)&0xffffffff
    def wire(self):return cobs_encode(self.body+struct.pack('<H',crc16(self.body)))+b'\x00'

def decode(wire):
    if not wire.endswith(b'\x00') or len(wire)>LIMIT:raise ValueError('wire boundary/length')
    raw=cobs_decode(wire[:-1])
    if len(raw)<HEADER.size+2:raise ValueError('short header')
    body=raw[:-2]
    if crc16(body)!=struct.unpack('<H',raw[-2:])[0]:raise ValueError('CRC')
    version,kind,n,device,session,seq=HEADER.unpack(body[:HEADER.size]);payload=body[HEADER.size:]
    if version!=VERSION or kind not in (EVENT,ACK,TELEMETRY) or n!=len(payload):raise ValueError('header')
    if session==0 or seq==0:raise ValueError('unallocated identity')
    if kind==ACK:
        if n!=4:raise ValueError('ACK payload')
    else:
        if n!=SNAPSHOT.size:raise ValueError('snapshot length')
        _,_,_,state,quality,*_=SNAPSHOT.unpack(payload)
        if state>4 or quality&0x60:raise ValueError('state/quality')
    return Frame(kind,device,session,seq,payload)

class StreamDecoder:
    def __init__(self):self.buffer=bytearray();self.discard=False;self.errors=0
    def feed(self,data):
        result=[]
        for b in data:
            if b==0:
                if self.buffer and not self.discard:
                    try:result.append(decode(bytes(self.buffer)+b'\x00'))
                    except ValueError:self.errors+=1
                self.buffer.clear();self.discard=False
            elif not self.discard:
                self.buffer.append(b)
                if len(self.buffer)>=LIMIT:self.buffer.clear();self.discard=True;self.errors+=1
        return result

def connect(path):
    db=sqlite3.connect(path);db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=EXTRA');return db

class Receiver:
    def __init__(self,path):
        self.db=connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS events(device INTEGER, session INTEGER, seq INTEGER, body BLOB NOT NULL, first_received_s REAL NOT NULL, PRIMARY KEY(device,session,seq))')
        self.db.execute('CREATE TABLE IF NOT EXISTS telemetry(device INTEGER, session INTEGER, seq INTEGER, body BLOB NOT NULL, received_s REAL NOT NULL, PRIMARY KEY(device,session,seq))');self.db.commit()
    def receive(self,wire,now,crash=None):
        frame=decode(wire)
        if frame.kind not in (EVENT,TELEMETRY):raise ValueError('not uplink')
        table='events' if frame.kind==EVENT else 'telemetry'
        try:
            self.db.execute('BEGIN IMMEDIATE')
            old=self.db.execute(f'SELECT body FROM {table} WHERE device=? AND session=? AND seq=?',frame.key).fetchone()
            if old and old[0]!=frame.body:raise ValueError('same key different body; do not ACK')
            if not old:self.db.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?)',(*frame.key,frame.body,now))
            if crash=='before_commit':raise RuntimeError('injected pre-commit stop')
            self.db.commit()
        except Exception:self.db.rollback();raise
        if crash=='after_commit':raise RuntimeError('injected post-commit pre-ACK stop')
        if frame.kind==TELEMETRY:return None
        # This line is reached only after commit, including exact duplicates.
        return Frame(ACK,*frame.key,struct.pack('<I',frame.fingerprint)).wire()
    def close(self):self.db.close()

class Sender:
    def __init__(self,path,device=1,queue_limit=QUEUE_LIMIT):
        self.db=connect(path);self.device=device;self.queue_limit=queue_limit
        self.db.execute('CREATE TABLE IF NOT EXISTS meta(device INTEGER PRIMARY KEY, boot INTEGER NOT NULL, seq INTEGER NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS outbox(device INTEGER, session INTEGER, seq INTEGER, wire BLOB NOT NULL, created_s REAL NOT NULL, expires_s REAL NOT NULL, state TEXT NOT NULL, attempts INTEGER NOT NULL, due_s REAL NOT NULL, PRIMARY KEY(device,session,seq))')
        self.db.execute('CREATE TABLE IF NOT EXISTS rejected(device INTEGER, time_s REAL, reason TEXT, payload BLOB)');self.db.commit()
        try:
            self.db.execute('BEGIN IMMEDIATE');old=self.db.execute('SELECT boot FROM meta WHERE device=?',(device,)).fetchone();self.session=(old[0] if old else 0)+1
            if self.session>0xffffffff:raise OverflowError('session exhausted; explicit re-enrolment required')
            self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?,0)',(device,self.session));self.db.commit()
        except Exception:self.db.rollback();raise
    def enqueue(self,payload,now):
        try:
            self.db.execute('BEGIN IMMEDIATE')
            count=self.db.execute("SELECT count(*) FROM outbox WHERE device=? AND state='pending'",(self.device,)).fetchone()[0]
            if count>=self.queue_limit:
                self.db.execute('INSERT INTO rejected VALUES(?,?,?,?)',(self.device,now,'queue_full_keep_existing',payload));self.db.commit();return None
            boot,seq=self.db.execute('SELECT boot,seq FROM meta WHERE device=?',(self.device,)).fetchone()
            if boot!=self.session:raise RuntimeError('sender superseded by newer session')
            seq+=1
            if seq>0xffffffff:raise OverflowError('sequence exhausted')
            frame=Frame(EVENT,self.device,self.session,seq,payload);decode(frame.wire())
            self.db.execute('UPDATE meta SET seq=? WHERE device=?',(seq,self.device))
            self.db.execute('INSERT INTO outbox VALUES(?,?,?,?,?,?,?,?,?)',(*frame.key,frame.wire(),now,now+TTL_S,'pending',0,now));self.db.commit();return frame
        except Exception:self.db.rollback();raise
    def next_frame(self,now,aux_ready=True):
        # Host scheduler gate only. Real driver must define UART/AUX completion.
        while True:
            row=self.db.execute("SELECT session,seq,wire,expires_s,attempts,due_s FROM outbox WHERE device=? AND state='pending' ORDER BY created_s,session,seq LIMIT 1",(self.device,)).fetchone()
            if not row:return None
            session,seq,wire,expires,attempts,due=row;key=(self.device,session,seq)
            state='expired' if now>=expires else 'unconfirmed' if attempts>=MAX_ATTEMPTS and now>=due else None
            if state:
                with self.db:self.db.execute('UPDATE outbox SET state=? WHERE device=? AND session=? AND seq=?',(state,*key))
                continue
            if not aux_ready or now<due:return None
            attempts+=1
            with self.db:self.db.execute('UPDATE outbox SET attempts=?,due_s=? WHERE device=? AND session=? AND seq=?',(attempts,now+(4 if attempts<4 else 10),*key))
            return wire
    def acknowledge(self,wire):
        frame=decode(wire)
        if frame.kind!=ACK or frame.device!=self.device:return False
        old=self.db.execute('SELECT wire,state FROM outbox WHERE device=? AND session=? AND seq=?',frame.key).fetchone()
        if not old or struct.unpack('<I',frame.payload)[0]!=decode(old[0]).fingerprint:return False
        state='acknowledged' if old[1] in ('pending','acknowledged') else 'acknowledged_late'
        with self.db:self.db.execute('UPDATE outbox SET state=? WHERE device=? AND session=? AND seq=?',(state,*frame.key))
        return True
    def close(self):self.db.close()
