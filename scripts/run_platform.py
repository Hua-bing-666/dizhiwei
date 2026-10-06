"""Local HTTP API and operations site; never bind to a public interface."""
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs, unquote
import argparse, json, mimetypes, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from platform_service import Platform, pressure_reads, dump
from reference_calibration import fit_reference

def serve(port, db):
    platform=Platform(db)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,obj,status=200):
            data=dump(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
        def allowed(self):
            host=self.headers.get('Host','');origin=self.headers.get('Origin')
            valid={f'127.0.0.1:{port}',f'localhost:{port}'}
            return host in valid and (origin is None or origin in {f'http://{h}' for h in valid})
        def do_GET(self):
            if not self.allowed():return self.reply({'error':'仅允许本机同源访问'},403)
            url=urlsplit(self.path)
            try:
                if url.path=='/api/state':return self.reply(platform.state())
                if url.path=='/api/workspace':return self.reply(json.loads((ROOT/'application/config/workspace.json').read_text(encoding='utf-8')))
                if url.path=='/api/history':
                    value=parse_qs(url.query).get('session',[None])[0]
                    return self.reply(platform.history(int(value) if value is not None else None))
                if url.path=='/api/samples':
                    value=parse_qs(url.query).get('session',[None])[0]
                    return self.reply(platform.samples(int(value) if value is not None else None))
                if url.path=='/api/export':return self.reply(platform.export())
                # Only published website assets and CAD meshes, no repository
                # files, runtime databases, credentials, or proposal documents.
                relative=unquote(url.path).lstrip('/') or 'index.html'
                target=(ROOT/'deliverables'/relative).resolve()
                if target.parent!=ROOT/'deliverables' or target.suffix not in ('.html','.png','.svg','.css','.js','.json'):return self.reply({'error':'资源不可访问'},404)
                if target.suffix=='.json':return self.reply({'error':'请使用数据导出接口'},404)
                data=target.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(target))[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            except (ValueError,FileNotFoundError):self.reply({'error':'找不到请求的资源或会话'},404)
        def do_POST(self):
            if not self.allowed():return self.reply({'error':'拒绝跨来源写入'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=16384:raise ValueError('请求体大小无效')
                obj=json.loads(self.rfile.read(size));route=urlsplit(self.path).path
                if not isinstance(obj,dict):raise ValueError('请求必须是 JSON 对象')
                if route=='/api/replay/start':result=platform.start(obj.get('scene','leak'),obj.get('sigma',.3))
                elif route=='/api/replay/step':result=platform.step(obj.get('n',1))
                elif route=='/api/events/note':result=platform.annotate(obj['id'],obj['stage'],obj['note'],obj.get('proof',''))
                elif route=='/api/control':result=platform.command(obj['action'],obj.get('id'))
                elif route=='/api/reference/fit':result=fit_reference(obj['csv'])
                elif route=='/api/wire':
                    ack=platform.ingest_wire(bytes.fromhex(obj['hex']),obj['now_ms']);result=dict(ack_hex=ack.hex(),committed=True,rf_verified=False)
                elif route=='/api/raw':
                    values=[float('nan') if v is None else float(v) for v in obj['pressure_kpa']]
                    r=platform.ingest_raw(obj['t_s'],obj['count'],obj['latch_ms'],pressure_reads(obj['t_s'],values));result=dict(issue=r['issue'],state=platform.state())
                else:return self.reply({'error':'接口不存在'},404)
                self.reply(result)
            except (ValueError,KeyError,TypeError,OverflowError) as e:self.reply({'error':str(e)},400)
            except Exception as e:self.reply({'error':f'服务异常：{type(e).__name__}；请保留会话并检查服务端日志'},500);print(repr(e),flush=True)
    http=HTTPServer(('127.0.0.1',port),Handler)
    print(f'运行平台：http://127.0.0.1:{port}  SQLite：{db}',flush=True)
    try:http.serve_forever()
    finally:http.server_close();platform.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--db',default=str(ROOT/'tmp/platform_runtime/operations.sqlite'));args=p.parse_args()
    Path(args.db).parent.mkdir(parents=True,exist_ok=True);serve(args.port,args.db)
