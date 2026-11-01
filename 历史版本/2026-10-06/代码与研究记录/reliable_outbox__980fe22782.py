"""SQLite sender outbox and receiver deduplication; transport is external.

An ACK returned by accept() exists only after SQLite commits. A repeated packet
must match its original contents. This implementation does not implement LoRa,
radio CRC, hardware power-loss behaviour or authentication.
"""
import hashlib,json,sqlite3

def encode(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))

class Outbox:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS pending(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, priority INTEGER NOT NULL, created INTEGER NOT NULL, last_sent INTEGER)')
        self.db.commit()
    def enqueue(self,payload,t,priority=0):
        with self.db:return self.db.execute('INSERT INTO pending(payload,priority,created) VALUES(?,?,?)',(encode(payload),priority,t)).lastrowid
    def pick(self,t):
        r=self.db.execute('SELECT id,payload FROM pending WHERE last_sent IS NULL OR last_sent<=? ORDER BY priority DESC,id LIMIT 1',(t-2,)).fetchone()
        if r is None:return None
        with self.db:self.db.execute('UPDATE pending SET last_sent=? WHERE id=?',(t,r[0]))
        return dict(packet_id=r[0],payload=json.loads(r[1]))
    def ack(self,packet_id):
        with self.db:self.db.execute('DELETE FROM pending WHERE id=?',(packet_id,))
    def count(self):return self.db.execute('SELECT COUNT(*) FROM pending').fetchone()[0]
    def close(self):self.db.close()

class Receiver:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS packets(id INTEGER PRIMARY KEY,digest TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,payload TEXT NOT NULL,received INTEGER NOT NULL)')
        self.db.commit()
    def accept(self,packet,t):
        pid=packet['packet_id'];body=packet['payload'];digest=hashlib.sha256(encode(body).encode()).hexdigest()
        with self.db:
            previous=self.db.execute('SELECT digest FROM packets WHERE id=?',(pid,)).fetchone()
            if previous and previous[0]!=digest:raise ValueError('Conflicting contents for packet ID')
            if previous is None:self.db.execute('INSERT INTO packets VALUES(?,?)',(pid,digest))
            for event in body.get('events',[]):
                payload=encode(event);old=self.db.execute('SELECT payload FROM events WHERE id=?',(event['event_id'],)).fetchone()
                if old and old[0]!=payload:raise ValueError('Conflicting contents for event ID')
                if old is None:self.db.execute('INSERT INTO events VALUES(?,?,?)',(event['event_id'],payload,t))
        return pid
    def events(self):return [dict(event=json.loads(p),received=t) for p,t in self.db.execute('SELECT payload,received FROM events ORDER BY id')]
    def close(self):self.db.close()
