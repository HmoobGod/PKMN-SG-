#!/usr/bin/env python3
"""Candidate host-only measurement. No container, game, or emulator operation.
Runtime is deliberately gated by a future independently reviewed manual workflow.
"""
import hashlib, json, os, re, select, selectors, stat, subprocess, sys, time, socket, struct
from pathlib import Path
from contextlib import contextmanager

ROOT=Path('/sys/fs/cgroup')
UNITS=Path('/run/systemd/system')
ENV={'PATH':'/usr/bin:/bin','HOME':'/','LANG':'C','LC_ALL':'C'}
DOCKER=['/usr/bin/docker','--host','unix:///var/run/docker.sock','--config','/nonexistent-sg-public-config']
SYSTEM=['/usr/bin/systemctl','--no-pager']
HOST_TOKEN='I_AUTHORIZE_ONE_LINUX_HOST_COMPATIBILITY_MEASUREMENT'
SLICE_TOKEN='I_AUTHORIZE_ONE_EMPTY_SYSTEMD_SLICE_CREATE_OBSERVE_REMOVE'
UNIT=b'[Unit]\nDescription=SoulGold public empty slice compatibility probe\nStopWhenUnneeded=no\n[Slice]\n'
HEX=re.compile(r'[0-9a-f]{40}\Z')
RUN=re.compile(r'[1-9][0-9]{0,19}\Z')
BOOT=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')
SHA=re.compile(r'[0-9a-f]{64}\Z')
VERSION=re.compile(r'[0-9][0-9A-Za-z.+~_-]{0,63}\Z')
class Hold(RuntimeError): pass

# Fixed stage labels only. Never emit exception text or host-derived values.
DIAGNOSTIC_CODES=frozenset({'AUTH', 'HOST', 'CGROUP', 'DOCKER_IDENTITY', 'DOCKER_API', 'KERNEL_LISTENER', 'PIDFD', 'SLICE_PRECHECK', 'SLICE_PRECHECK_QUERY', 'SLICE_PRECHECK_STATE', 'SLICE_CREATION', 'SLICE_PERSISTENCE', 'SLICE_REMOVAL', 'SLICE_FD_CLOSE', 'RECEIPT', 'UNCLASSIFIED'})
class DiagnosticHold(Hold):
    def __init__(self,code):
        self.code=code if type(code) is str and code in DIAGNOSTIC_CODES else 'UNCLASSIFIED'
        super().__init__(self.code)

@contextmanager
def diagnostic(code):
    try:
        yield
    except DiagnosticHold:
        raise
    except Exception:
        raise DiagnosticHold(code) from None

def report_hold(exc):
    code=exc.code if type(exc) is DiagnosticHold else 'UNCLASSIFIED'
    if type(code) is not str or code not in DIAGNOSTIC_CODES: code='UNCLASSIFIED'
    print('HOST_COMPATIBILITY_HOLD_QUARANTINE',file=sys.stderr)
    print('SG_HOST_DIAGNOSTIC='+code,file=sys.stderr)

def require(ok, reason):
    if not ok: raise Hold(reason)

def left(end,clock=time.monotonic):
    remain=end-clock(); require(remain>0,'deadline expired'); return remain

def digest(data): return hashlib.sha256(data).hexdigest()
def boot():
    s=Path('/proc/sys/kernel/random/boot_id').read_text().strip(); require(BOOT.fullmatch(s),'boot identity'); return s

def name_for(commit,run):
    require(HEX.fullmatch(commit) and RUN.fullmatch(run),'run identity')
    return 'sglab'+digest((commit+':'+run+':1').encode())[:24]+'.slice'

def auth(args):
    require(len(args)==5,'exact arguments required')
    commit,run,attempt,host,slice_token=args
    require(attempt=='1' and host==HOST_TOKEN and slice_token==SLICE_TOKEN,'authorization missing')
    return name_for(commit,run)

def read_at(fd,name,limit=8192):
    with os.fdopen(os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd),'rb') as f: data=f.read(limit+1)
    require(len(data)<=limit,'bounded read overflow'); return data.decode('ascii')

def props(text,keys):
    out={}
    for line in text.splitlines():
        k,sep,v=line.partition('='); require(sep and k in keys and k not in out,'malformed systemd property'); out[k]=v
    require(set(out)==set(keys),'missing systemd properties'); return out

def empty_events(text,procs,children):
    pairs={}
    for line in text.splitlines():
        a=line.split(); require(len(a)==2 and a[0] not in pairs and a[1] in ('0','1'),'malformed cgroup.events'); pairs[a[0]]=a[1]
    require(set(pairs)=={'populated','frozen'} and pairs['populated']=='0' and pairs['frozen']=='0','slice not empty/unfrozen')
    require(procs=='' and not children,'slice contains processes or subgroups')

def mount_gate(text):
    rows=[]
    for line in text.splitlines():
        a,sep,b=line.partition(' - '); require(sep,'malformed mountinfo'); x=a.split(); y=b.split(); require(len(x)>=6 and len(y)>=3,'malformed mountinfo fields')
        if y[0] in ('cgroup','cgroup2'): rows.append((x,y))
    require(len(rows)==1,'not exclusively unified cgroup v2')
    x,y=rows[0]; require(x[3]=='/' and x[4]=='/sys/fs/cgroup' and y[0]=='cgroup2' and 'rw' in x[5].split(','),'unexpected cgroup mount')

def docker_gate(info,version):
    require(isinstance(info,dict) and isinstance(version,dict),'Docker schema')
    require(info.get('OSType')=='linux' and info.get('Architecture')=='x86_64' and info.get('CgroupVersion')=='2' and info.get('CgroupDriver')=='systemd','Docker host mismatch')
    options=info.get('SecurityOptions'); require(isinstance(options,list) and bool(options) and all(type(x) is str and 'rootless' not in x.lower() for x in options),'rootless or unknown security options')
    server=version.get('Server'); client=version.get('Client'); require(isinstance(server,dict) and isinstance(client,dict),'Docker version missing')
    for v in (server.get('Version'),client.get('Version'),info.get('ServerVersion')): require(type(v) is str and VERSION.fullmatch(v),'Docker version invalid')
    require(server['Version']==info['ServerVersion'],'Docker server drift'); return client['Version'],server['Version']

def strict_json(data):
    def unique(pairs):
        d={}
        for k,v in pairs: require(k not in d,'duplicate JSON key'); d[k]=v
        return d
    return json.loads(data,object_pairs_hook=unique,parse_constant=lambda _: (_ for _ in ()).throw(Hold('nonfinite JSON')))

def cmd(argv,end):
    left(end); p=subprocess.Popen(argv,env=ENV,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
    bufs={p.stdout:bytearray(),p.stderr:bytearray()}
    try:
        with selectors.DefaultSelector() as sel:
            for f in bufs: os.set_blocking(f.fileno(),False); sel.register(f,selectors.EVENT_READ)
            while sel.get_map():
                for key,_ in sel.select(left(end)):
                    b=os.read(key.fileobj.fileno(),4096)
                    if not b: sel.unregister(key.fileobj); continue
                    bufs[key.fileobj].extend(b); require(sum(map(len,bufs.values()))<=131072,'command output overflow')
        rc=p.wait(timeout=left(end)); left(end)
        require(rc==0 and not bufs[p.stderr],'command failed or unexpected stderr'); return bytes(bufs[p.stdout]).decode('utf-8','strict')
    finally:
        try:
            if p.poll() is None: p.kill(); p.wait(timeout=1)
        finally:
            for f in bufs: f.close()

def show(unit,keys,end): return props(cmd(SYSTEM+['show','--all',unit]+['--property='+k for k in keys],end),keys)
def identity(st): return (st.st_dev,st.st_ino)
def absent(path):
    try: path.lstat()
    except FileNotFoundError: return True
    return False

# Linux v6.14 unix_diag.h / net/unix/diag.c: exact SOCK_DIAG_BY_FAMILY
# request, AF_UNIX, UDIAG_SHOW_NAME|UDIAG_SHOW_VFS.  VFS dev is kernel
# MKDEV (12-bit major,20-bit minor), NOT user-space st_dev encoding.
SOCK_PATHS=('/run/docker.sock','/var/run/docker.sock')
SERVICE_KEYS=('ActiveState','MainPID','TriggeredBy')
SOCKET_KEYS=('LoadState','ActiveState','SubState','Accept','Listen','Triggers')

def bounded_file(path,limit):
    with open(path,'rb') as f: data=f.read(limit+1)
    require(len(data)<=limit,'bounded proc read overflow'); return data

def proc_start(pid):
    s=bounded_file(Path('/proc')/str(pid)/'stat',8192).decode('ascii'); a=s[s.rfind(')')+2:].split()
    require(s.startswith(str(pid)+' (') and len(a)>19 and a[19].isdigit(),'proc stat'); return int(a[19])

def file_signature(st): return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

def hash_running_exe(path,end):
    # proc magic link must be opened, not resolved and reopened by filename.
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC)
    try:
        st=os.fstat(fd); require(stat.S_ISREG(st.st_mode) and st.st_uid==0 and not st.st_mode&0o022 and 0<st.st_size<=268435456,'unsafe running executable')
        h=hashlib.sha256(); total=0
        while True:
            left(end); data=os.read(fd,1048576)
            if not data: break
            total+=len(data); require(total<=st.st_size,'executable size drift'); h.update(data)
        require(total==st.st_size and file_signature(os.fstat(fd))==file_signature(st) and file_signature(os.stat(path))==file_signature(st),'running executable drift')
        left(end); return h.hexdigest(),st.st_dev,st.st_ino
    finally: os.close(fd)

def proc_identity(pid,end):
    p=Path('/proc')/str(pid); start=proc_start(pid)
    u=[l for l in bounded_file(p/'status',65536).decode('ascii').splitlines() if l.startswith('Uid:')]; require(len(u)==1 and u[0].split()[1:]==['0']*4,'daemon not root')
    target=os.readlink(p/'exe'); require(target.startswith('/') and Path(target).name=='dockerd','not dockerd or deleted executable')
    h,dev,ino=hash_running_exe(p/'exe',end)
    require(proc_start(pid)==start and os.readlink(p/'exe')==target,'process executable drift'); return (start,target,h,dev,ino)

def listener_inode(text):
    lines=text.splitlines(); require(lines and lines[0].split()==['Num','RefCount','Protocol','Flags','Type','St','Inode','Path'],'unix table header')
    matches=[]
    for line in lines[1:]:
        f=line.split(maxsplit=7); require(len(f)>=7,'malformed unix table')
        if len(f)==8 and f[7] in SOCK_PATHS and f[3]=='00010000' and f[4]=='0001' and f[5]=='01':
            require(f[6].isdigit() and 0<int(f[6])<=0xffffffff,'kernel listener inode out of range'); matches.append(int(f[6]))
    require(len(matches)==1,'missing or ambiguous kernel listener'); return matches[0]

def vfs_dev(dev):
    major,minor=os.major(dev),os.minor(dev); require(major<4096 and minor<1048576,'VFS device out of range'); return (major<<20)|minor

def parse_diag(data,port,ino,st):
    require(len(data)>=32,'short diagnostic reply')
    size,kind,flags,seq,dest=struct.unpack_from('=IHHII',data)
    require(size==len(data) and kind==20 and flags==0 and seq==1 and dest==port,'unexpected netlink reply')
    family,typ,state,pad,got,c0,c1=struct.unpack_from('=BBBBIII',data,16)
    require((family,typ,state,pad,got)==(socket.AF_UNIX,socket.SOCK_STREAM,10,0,ino) and (c0,c1)!=(0xffffffff,0xffffffff),'not exact live stream listener')
    attrs={}; pos=32
    while pos<len(data):
        require(len(data)-pos>=4,'short diagnostic attribute'); n,k=struct.unpack_from('=HH',data,pos); aligned=(n+3)&~3
        require(n>=4 and pos+aligned<=len(data) and k not in attrs,'invalid diagnostic attribute'); attrs[k]=data[pos+4:pos+n]; pos+=aligned
    require(set(attrs)=={0,1,6} and attrs[0] in tuple(x.encode()+suffix for x in SOCK_PATHS for suffix in (b'',b'\0')) and attrs[6]==b'\0' and len(attrs[1])==8,'missing or unexpected listener attributes')
    disk_ino,dev=struct.unpack('=II',attrs[1]); require(0<st.st_ino<=0xffffffff and disk_ino==st.st_ino and dev==vfs_dev(st.st_dev),'listener VFS mismatch')
    return (ino,c0,c1,disk_ino,dev)

def kernel_listener(st,end):
    ino=listener_inode(bounded_file(Path('/proc/net/unix'),1048576).decode('ascii'))
    with socket.socket(socket.AF_NETLINK,socket.SOCK_RAW,4) as net:
        net.bind((0,0)); port=net.getsockname()[0]; net.settimeout(min(2,left(end)))
        req=struct.pack('=BBHIIIII',socket.AF_UNIX,0,0,1<<10,ino,3,0xffffffff,0xffffffff)
        net.sendto(struct.pack('=IHHII',16+len(req),20,1,1,port)+req,(0,0))
        data,anc,flags,sender=net.recvmsg(4096)
        require(not anc and flags==0 and sender==(0,0),'untrusted/truncated kernel response')
    left(end); return parse_diag(data,port,ino,st)

def listener_fds(pid,ino,end):
    path=Path('/proc')/str(pid)/'fd'; found=[]
    # No file-descriptor duplication or mutation. Exact kernel socket links.
    for i,entry in enumerate(path.iterdir()):
        left(end); require(i<8192 and entry.name.isdigit(),'FD inventory overflow or malformed entry')
        try: target=os.readlink(entry)
        except FileNotFoundError: continue # unrelated concurrent close; require positive ownership both times
        if target==f'socket:[{ino}]': found.append(int(entry.name))
    return tuple(sorted(found))

def activation_gate(peer,pid,d,s,daemon_fds,manager_fds):
    require(type(peer) is tuple and len(peer)==3 and peer[1]==0 and daemon_fds,'unverified root daemon listener ownership')
    if peer[0]==pid: return 'direct'
    require(peer[0]==1 and manager_fds and d['TriggeredBy']=='docker.socket' and type(s) is dict,'unverified socket activation peer')
    require(s=={'LoadState':'loaded','ActiveState':'active','SubState':'running','Accept':'no','Listen':s.get('Listen'),'Triggers':'docker.service'} and s['Listen'] in tuple(x+' (Stream)' for x in SOCK_PATHS),'socket-to-service relationship unverified')
    return 'systemd-activation'

def peer_snapshot(sock,st,pid,d,end):
    require(identity(sock.stat())==identity(st),'socket VFS drift')
    k=kernel_listener(st,end); daemon_fds=listener_fds(pid,k[0],end)
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as conn:
        conn.settimeout(min(2,left(end))); conn.connect(str(sock)); peer=struct.unpack('=3i',conn.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
    s=show('docker.socket',SOCKET_KEYS,end) if peer[0]==1 else None
    manager_fds=listener_fds(1,k[0],end) if peer[0]==1 else ()
    mode=activation_gate(peer,pid,d,s,daemon_fds,manager_fds)
    require(identity(sock.stat())==identity(st) and kernel_listener(st,end)==k and listener_fds(pid,k[0],end)==daemon_fds,'listener drift within snapshot')
    if mode=='systemd-activation': require(listener_fds(1,k[0],end)==manager_fds,'manager listener drift')
    return (peer,k,daemon_fds,manager_fds,mode,s)

def host_measure(end):
    with diagnostic('HOST'):
        require(os.geteuid()==0 and os.uname().machine=='x86_64','root x64 host required')
        require(Path('/proc/1/comm').read_text().strip()=='systemd','PID1 not systemd')
        require(identity(os.stat('/proc/self/ns/pid'))==identity(os.stat('/proc/1/ns/pid')),'not host PID namespace')
    with diagnostic('CGROUP'):
        mount_gate(Path('/proc/self/mountinfo').read_text())
        require(Path('/proc/1/cgroup').read_text().startswith('0::') and len(Path('/proc/1/cgroup').read_text().splitlines())==1,'PID1 cgroup not unified')
    with diagnostic('HOST'):
        b=boot(); osrel=Path('/etc/os-release').read_text().splitlines(); require('ID=ubuntu' in osrel and 'VERSION_ID="24.04"' in osrel,'unexpected host distribution')
        systemd=cmd(['/usr/bin/systemctl','--version'],end).splitlines()[0]; require(re.fullmatch(r'systemd [0-9]+(?: \([^\r\n]{1,180}\))?',systemd),'systemd version grammar')
    with diagnostic('DOCKER_IDENTITY'):
        sock=Path('/var/run/docker.sock'); st=sock.stat(); require(stat.S_ISSOCK(st.st_mode) and st.st_uid==0 and sock.resolve()==Path('/run/docker.sock'),'local root socket required')
        d=show('docker.service',SERVICE_KEYS,end); require(d['ActiveState']=='active' and re.fullmatch(r'[1-9][0-9]{0,9}',d['MainPID']),'docker service unavailable')
        pid=int(d['MainPID']); require(pid>1,'invalid daemon PID')
    with diagnostic('PIDFD'):
        fd=os.pidfd_open(pid,0)
    try:
        with diagnostic('PIDFD'):
            poll=select.poll(); poll.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR); require(not poll.poll(0),'daemon already dead')
        with diagnostic('DOCKER_IDENTITY'):
            before=proc_identity(pid,end); manager_start=proc_start(1)
        with diagnostic('KERNEL_LISTENER'):
            snapshot=peer_snapshot(sock,st,pid,d,end)
        with diagnostic('DOCKER_API'):
            info=strict_json(cmd(DOCKER+['info','--format','{{json .}}'],end)); ver=strict_json(cmd(DOCKER+['version','--format','{{json .}}'],end)); client,server=docker_gate(info,ver)
        with diagnostic('DOCKER_IDENTITY'):
            require(not poll.poll(0) and proc_identity(pid,end)==before and proc_start(1)==manager_start and boot()==b and show('docker.service',SERVICE_KEYS,end)==d,'daemon/socket drift')
        with diagnostic('KERNEL_LISTENER'):
            require(peer_snapshot(sock,st,pid,d,end)==snapshot and not poll.poll(0) and proc_start(pid)==before[0] and proc_start(1)==manager_start and boot()==b and identity(os.stat(Path('/proc')/str(pid)/'exe'))==before[3:5],'listener/peer continuity failure')
            peer,k,daemon_fds,manager_fds,mode,socket_unit=snapshot
    finally:
        with diagnostic('PIDFD'):
            os.close(fd)
    with diagnostic('PIDFD'):
        self_fd=os.pidfd_open(os.getpid(),0)
        try:
            q=select.poll();q.register(self_fd,select.POLLIN|select.POLLHUP|select.POLLERR);require(not q.poll(0),'self PIDFD invalid')
        finally: os.close(self_fd)
    with diagnostic('HOST'):
        left(end)
        return dict(boot_id=b,systemd=systemd,kernel=os.uname().release,docker_client=client,docker_server=server,dockerd_pid=pid,dockerd_start_ticks=before[0],dockerd_sha256=before[2],docker_cli_sha256=digest(Path('/usr/bin/docker').read_bytes()),socket_dev=st.st_dev,socket_ino=st.st_ino,peer_pid=peer[0],peer_uid=peer[1],dockerd_exe_dev=before[3],dockerd_exe_ino=before[4],kernel_listener_ino=k[0],listener_cookie=list(k[1:3]),listener_vfs_ino=k[3],listener_vfs_dev=k[4],daemon_listener_fds=list(daemon_fds),manager_listener_fds=list(manager_fds),peer_mode=mode,service_triggered_by=d['TriggeredBy'],socket_unit=socket_unit,manager_start_ticks=manager_start,cgroup_version='2',cgroup_driver='systemd',pidfd=True,host_pid_namespace=True,rootful=True)

def sample(fd,path,name,b,end):
    left(end); st=os.fstat(fd); cur=path.lstat(); require(stat.S_ISDIR(cur.st_mode) and identity(st)==identity(cur) and boot()==b,'slice identity drift')
    require(show(name,('ActiveState','ControlGroup','FragmentPath','StopWhenUnneeded'),end)=={'ActiveState':'active','ControlGroup':'/'+name,'FragmentPath':str(UNITS/name),'StopWhenUnneeded':'no'},'slice unit identity/state drift')
    for _ in range(2):
        empty_events(read_at(fd,'cgroup.events'),read_at(fd,'cgroup.procs'),[n for n in os.listdir(fd) if stat.S_ISDIR(os.stat(n,dir_fd=fd,follow_symlinks=False).st_mode)])
    require(identity(path.lstat())==identity(st) and boot()==b,'slice changed during sample'); left(end)
    return {'dev':st.st_dev,'ino':st.st_ino,'populated':0,'procs':0,'children':0,'active':True}

def slice_measure(name,b,end):
    path=ROOT/name; unit=UNITS/name; keys=('LoadState','ActiveState','ControlGroup')
    with diagnostic('SLICE_PRECHECK'):
        require(absent(path) and absent(unit),'preexisting slice')
        # systemctl show may successfully describe not-found or fail; never guess from failure.
        with diagnostic('SLICE_PRECHECK_QUERY'):
            state=show(name,keys,end)
        with diagnostic('SLICE_PRECHECK_STATE'):
            require(state=={'LoadState':'not-found','ActiveState':'inactive','ControlGroup':''},'preexisting or unresolved unit')
    with diagnostic('SLICE_CREATION'):
        fd=os.open(unit,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o644)
        try:
            require(os.write(fd,UNIT)==len(UNIT),'short unit write'); os.fsync(fd); unit_id=identity(os.fstat(fd))
        finally: os.close(fd)
        # On any uncertainty after this point, do NOT stop an unknown or populated
        # slice, unlink an unverified unit, or retry. Quarantine the disposable VM.
        cmd(SYSTEM+['daemon-reload'],end); cmd(SYSTEM+['start',name],end)
        dfd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        with diagnostic('SLICE_PERSISTENCE'):
            t0=time.monotonic(); first=sample(dfd,path,name,b,end)
            require(left(end)>2,'persistence interval unavailable'); time.sleep(2)
            last=sample(dfd,path,name,b,end); elapsed=int((time.monotonic()-t0)*1000)
            require(first==last and elapsed>=2000,'persistent empty slice unverified')
            require(identity(unit.lstat())==unit_id and unit.read_bytes()==UNIT,'unit file changed')
            # Last observation before stop; not an atomic exclusion of concurrent writers.
            require(sample(dfd,path,name,b,end)==last,'pre-stop drift')
        with diagnostic('SLICE_REMOVAL'):
            cmd(SYSTEM+['stop',name],end)
            require(absent(path),'slice cgroup still present')
            require(show(name,keys,end)=={'LoadState':'loaded','ActiveState':'inactive','ControlGroup':''},'stopped unit unverified')
            require(identity(unit.lstat())==unit_id and unit.read_bytes()==UNIT,'unit identity changed before unlink')
            unit.unlink(); cmd(SYSTEM+['daemon-reload'],end)
            require(absent(path) and absent(unit) and boot()==b,'slice removal incomplete')
            require(show(name,keys,end)=={'LoadState':'not-found','ActiveState':'inactive','ControlGroup':''},'unit remains loaded')
            left(end)
    finally:
        with diagnostic('SLICE_FD_CLOSE'):
            os.close(dfd)
    return dict(name=name,first=first,last=last,persistence_ms=elapsed,unit_sha256=digest(UNIT),cgroup_removed=True,unit_removed=True,unit_not_found=True)

def validate_receipt(r,commit,run):
    require(type(r) is dict and set(r)=={'schema','result','commit','run','attempt','host','slice','elapsed_ms','runtime_containment_approved','private_inputs_approved','native_approved'},'receipt fields')
    require(r['schema']=='sg-linux-host-compatibility-v2' and r['result']=='HOST_COMPATIBILITY_REVIEW_REQUIRED' and r['commit']==commit and r['run']==run and r['attempt']=='1','receipt provenance')
    require(all(r[k] is False for k in ('runtime_containment_approved','private_inputs_approved','native_approved')),'approval drift')
    h=r['host']; s=r['slice']; require(type(h) is dict and type(s) is dict,'receipt records')
    require(set(h)=={'boot_id','systemd','kernel','docker_client','docker_server','dockerd_pid','dockerd_start_ticks','dockerd_sha256','docker_cli_sha256','socket_dev','socket_ino','peer_pid','peer_uid','dockerd_exe_dev','dockerd_exe_ino','kernel_listener_ino','listener_cookie','listener_vfs_ino','listener_vfs_dev','daemon_listener_fds','manager_listener_fds','peer_mode','service_triggered_by','socket_unit','manager_start_ticks','cgroup_version','cgroup_driver','pidfd','host_pid_namespace','rootful'},'host fields')
    require(all(type(h[k]) is str and SHA.fullmatch(h[k]) for k in ('dockerd_sha256','docker_cli_sha256')) and type(h['boot_id']) is str and BOOT.fullmatch(h['boot_id']),'host fingerprints')
    require(all(type(h[k]) is int and h[k]>0 for k in ('dockerd_pid','dockerd_start_ticks','socket_dev','socket_ino','peer_pid')) and h['dockerd_pid']>1 and type(h['peer_uid']) is int and h['peer_uid']==0,'host PID identity')
    require(all(type(h[k]) is int and h[k]>0 for k in ('dockerd_exe_dev','dockerd_exe_ino','manager_start_ticks','kernel_listener_ino','listener_vfs_ino')) and h['kernel_listener_ino']<=0xffffffff and h['listener_vfs_ino']==h['socket_ino']<=0xffffffff and type(h['listener_vfs_dev']) is int and h['listener_vfs_dev']==vfs_dev(h['socket_dev']),'receipt listener identity')
    cookie=h['listener_cookie']; require(type(cookie) is list and len(cookie)==2 and all(type(x) is int and 0<=x<=0xffffffff for x in cookie) and cookie!=[0xffffffff,0xffffffff],'receipt listener cookie')
    for fds in (h['daemon_listener_fds'],h['manager_listener_fds']):
        require(type(fds) is list and len(fds)<=8192 and all(type(x) is int and 0<=x<=0x7fffffff for x in fds) and fds==sorted(set(fds)),'receipt FD ownership')
    require(type(h['service_triggered_by']) is str,'receipt service relation')
    mode=activation_gate((h['peer_pid'],h['peer_uid'],0),h['dockerd_pid'],{'TriggeredBy':h['service_triggered_by']},h['socket_unit'],h['daemon_listener_fds'],h['manager_listener_fds'])
    require(h['peer_mode']==mode and (mode!='direct' or (h['socket_unit'] is None and h['manager_listener_fds']==[])),'receipt peer mode')
    require(all(type(h[k]) is str and VERSION.fullmatch(h[k]) for k in ('docker_client','docker_server','kernel')) and type(h['systemd']) is str and re.fullmatch(r'systemd [0-9]+(?: \([^\r\n]{1,180}\))?',h['systemd']),'version receipt')
    require(h['cgroup_version']=='2' and h['cgroup_driver']=='systemd' and all(h[k] is True for k in ('pidfd','host_pid_namespace','rootful')),'host gate')
    require(set(s)=={'name','first','last','persistence_ms','unit_sha256','cgroup_removed','unit_removed','unit_not_found'} and s['name']==name_for(commit,run) and s['unit_sha256']==digest(UNIT),'slice provenance')
    require(s['first']==s['last'],'slice identity drift')
    for x in (s['first'],s['last']):
        require(type(x) is dict and set(x)=={'dev','ino','populated','procs','children','active'},'slice snapshot schema')
        require(all(type(x[k]) is int and x[k]>0 for k in ('dev','ino')) and all(type(x[k]) is int and x[k]==0 for k in ('populated','procs','children')) and x['active'] is True,'slice not empty')
    require(all(s[k] is True for k in ('cgroup_removed','unit_removed','unit_not_found')),'cleanup unverified')
    require(type(s['persistence_ms']) is int and type(r['elapsed_ms']) is int and 2000<=s['persistence_ms']<=r['elapsed_ms']<45000,'deadline receipt')
    return r

def main(args):
    with diagnostic('AUTH'):
        name=auth(args)
    with diagnostic('HOST'):
        commit,run,attempt,_,_=args; t=time.monotonic(); end=t+45
        h=host_measure(min(end,t+15))
    with diagnostic('SLICE_CREATION'):
        s=slice_measure(name,h['boot_id'],end)
    with diagnostic('RECEIPT'):
        r=dict(schema='sg-linux-host-compatibility-v2',result='HOST_COMPATIBILITY_REVIEW_REQUIRED',commit=commit,run=run,attempt=attempt,host=h,slice=s,elapsed_ms=int((time.monotonic()-t)*1000),runtime_containment_approved=False,private_inputs_approved=False,native_approved=False)
        left(end); validate_receipt(r,commit,run); print(json.dumps(r,sort_keys=True,separators=(',',':')))

if __name__=='__main__':
    try: main(sys.argv[1:])
    except Exception as exc:
        # No raw host output, no receipt, no retry, no blanket cleanup.
        report_hold(exc); sys.exit(1)
