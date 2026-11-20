#!/usr/bin/env python3
"""Drop-in candidate for PR #152 empty-mGBA Qt focus observer.

Strict public-source-only integration: preserved Ctrl+O Select ROM dialog
and original title/WM_CLASS/visible/focus checks; Xlib limited to a bounded
child process. No ROM, save, debugger, game execution or host game writes.
"""
from __future__ import annotations
import argparse
import ctypes as C
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time

APPIMAGE_SHA256 = 'fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd'
APPIMAGE_SIZE = 25208000
MGBA_COMMIT = '26b7884bc25a5933960f3cdcd98bac1ae14d42e2'
IS_VIEWABLE = 2
MAIN_TITLE = re.compile(r'^mGBA - (?:0\.10\.5|[A-Za-z0-9][A-Za-z0-9 ._()\-]{0,95}(?: \([0-9]{1,3}(?:\.[0-9])? fps\))? - 0\.10\.5)$')
DISPLAY_PATTERN = re.compile(r'^:[0-9]{1,4}(?:\.[0-9])?$')

class ObserverError(RuntimeError):
    pass

class XWindowAttributes(C.Structure):
    _fields_ = [
        ('x',C.c_int), ('y',C.c_int), ('width',C.c_int), ('height',C.c_int),
        ('border_width',C.c_int), ('depth',C.c_int), ('visual',C.c_void_p),
        ('root',C.c_ulong), ('window_class',C.c_int),
        ('bit_gravity',C.c_int), ('win_gravity',C.c_int),
        ('backing_store',C.c_int), ('backing_planes',C.c_ulong),
        ('backing_pixel',C.c_ulong), ('save_under',C.c_int),
        ('colormap',C.c_ulong), ('map_installed',C.c_int),
        ('map_state',C.c_int), ('all_event_masks',C.c_long),
        ('your_event_mask',C.c_long), ('do_not_propagate_mask',C.c_long),
        ('override_redirect',C.c_int), ('screen',C.c_void_p),
    ]

class XClassHint(C.Structure):
    _fields_ = [('res_name',C.c_void_p), ('res_class',C.c_void_p)]

class XErrorEvent(C.Structure):
    _fields_ = [('type',C.c_int), ('display',C.c_void_p),
                ('resourceid',C.c_ulong), ('serial',C.c_ulong),
                ('error_code',C.c_ubyte), ('request_code',C.c_ubyte),
                ('minor_code',C.c_ubyte)]

XERROR_CB=C.CFUNCTYPE(C.c_int,C.c_void_p,C.POINTER(XErrorEvent))


def require_parent_x11(display: str, authority: str) -> tuple[str,str]:
    """No guesses from nested environments or Xlib's default .Xauthority."""
    if not isinstance(display,str) or not DISPLAY_PATTERN.fullmatch(display):
        raise ObserverError('unexpected or nonlocal DISPLAY')
    if not isinstance(authority,str) or not authority or not os.path.isabs(authority):
        raise ObserverError('XAUTHORITY must be an absolute path')
    if os.environ.get('DISPLAY') != display or os.environ.get('XAUTHORITY') != authority:
        raise ObserverError('parent DISPLAY/XAUTHORITY credentials disagree')
    try:
        info=os.lstat(authority)
    except OSError as exc:
        raise ObserverError('XAUTHORITY missing/inaccessible') from exc
    if not stat.S_ISREG(info.st_mode) or (info.st_mode & 0o077) or info.st_uid!=os.getuid():
        raise ObserverError('XAUTHORITY not an owned private regular file')
    return display,authority

class XClient:
    """Strict PR #152 Xlib identity + focus verifier, worker-process ONLY."""
    def __init__(self, display: str):
        require_parent_x11(display,os.environ.get('XAUTHORITY',''))
        if not ctypes.util.find_library('X11') or not ctypes.util.find_library('Xtst'):
            raise ObserverError('X11/Xtst not found')
        self.x=C.CDLL(ctypes.util.find_library('X11'))
        self.xt=C.CDLL(ctypes.util.find_library('Xtst'))
        self.dpy=None
        self._handler=None
        self._old_handler=None
        self._closed=False
        self.errors=[]
        self.x.XOpenDisplay.argtypes=[C.c_char_p]
        self.x.XOpenDisplay.restype=C.c_void_p
        self.x.XDefaultRootWindow.argtypes=[C.c_void_p]
        self.x.XDefaultRootWindow.restype=C.c_ulong
        self.x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
        self.x.XQueryTree.restype=C.c_int
        self.x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_void_p)]
        self.x.XFetchName.restype=C.c_int
        self.x.XGetClassHint.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(XClassHint)]
        self.x.XGetClassHint.restype=C.c_int
        self.x.XGetWindowAttributes.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(XWindowAttributes)]
        self.x.XGetWindowAttributes.restype=C.c_int
        self.x.XFree.argtypes=[C.c_void_p]
        self.x.XFree.restype=C.c_int
        self.x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong]
        self.x.XSetInputFocus.restype=C.c_int
        self.x.XGetInputFocus.argtypes=[C.c_void_p,C.POINTER(C.c_ulong),C.POINTER(C.c_int)]
        self.x.XGetInputFocus.restype=C.c_int
        self.x.XSync.argtypes=[C.c_void_p,C.c_int]
        self.x.XSync.restype=C.c_int
        self.x.XStringToKeysym.argtypes=[C.c_char_p]
        self.x.XStringToKeysym.restype=C.c_ulong
        self.x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong]
        self.x.XKeysymToKeycode.restype=C.c_uint
        self.xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        self.xt.XTestFakeKeyEvent.restype=C.c_int
        self.x.XStoreName.argtypes=[C.c_void_p,C.c_ulong,C.c_char_p]
        self.x.XStoreName.restype=C.c_int
        self.x.XCloseDisplay.argtypes=[C.c_void_p]
        self.x.XCloseDisplay.restype=C.c_int
        # XSetErrorHandler is process-global; restore old handler before the
        # Python CFUNCTYPE callback can be collected. Restrict to subprocess.
        self.x.XSetErrorHandler.argtypes=[C.c_void_p]
        self.x.XSetErrorHandler.restype=C.c_void_p
        def on_error(_display,event):
            try:
                self.errors.append((int(event.contents.error_code),int(event.contents.request_code)))
            except Exception:
                self.errors.append((-1,-1))
            return 0
        self._handler=XERROR_CB(on_error)
        try:
            self._old_handler=self.x.XSetErrorHandler(C.cast(self._handler,C.c_void_p))
            self.dpy=self.x.XOpenDisplay(display.encode('ascii'))
            if not self.dpy:
                raise ObserverError('XOpenDisplay failed: DISPLAY/XAUTHORITY mismatch')
        except BaseException:
            self.close()
            raise

    def check(self):
        if self._closed or not self.dpy:
            raise ObserverError('Xlib client closed')
        self.x.XSync(self.dpy,0)
        if self.errors:
            raise ObserverError(f'X11 asynchronous error: {self.errors[0]}')

    def windows(self):
        root=self.x.XDefaultRootWindow(self.dpy)
        root_out,parent=C.c_ulong(),C.c_ulong()
        children=C.POINTER(C.c_ulong)()
        count=C.c_uint()
        if not self.x.XQueryTree(self.dpy,root,C.byref(root_out),C.byref(parent),C.byref(children),C.byref(count)):
            raise ObserverError('XQueryTree failed')
        try:
            ids=[int(children[i]) for i in range(count.value)]
        finally:
            if children:
                self.x.XFree(C.cast(children,C.c_void_p))
        found=[]
        for wid in ids:
            attr=XWindowAttributes()
            if not self.x.XGetWindowAttributes(self.dpy,wid,C.byref(attr)):
                continue
            raw_name=C.c_void_p()
            name=''
            if self.x.XFetchName(self.dpy,wid,C.byref(raw_name)) and raw_name.value:
                name=C.string_at(raw_name.value).decode('utf-8','replace')
            if raw_name.value:
                self.x.XFree(raw_name)
            hint=XClassHint()
            klass=('','')
            if self.x.XGetClassHint(self.dpy,wid,C.byref(hint)):
                try:
                    klass=(C.string_at(hint.res_name).decode('utf-8','replace') if hint.res_name else '',
                           C.string_at(hint.res_class).decode('utf-8','replace') if hint.res_class else '')
                finally:
                    if hint.res_name:self.x.XFree(hint.res_name)
                    if hint.res_class:self.x.XFree(hint.res_class)
            found.append({'id':wid,'name':name,'class':klass,'map_state':attr.map_state,
                          'width':attr.width,'height':attr.height})
        self.check()
        return found

    def focus_main_window(self):
        windows=self.windows()
        candidates=[w for w in windows if MAIN_TITLE.fullmatch(w['name'])
                    and w['class']==('mgba-qt','mGBA') and w['map_state']==IS_VIEWABLE
                    and w['width']>=240 and w['height']>=160]
        if len(candidates)!=1:
            raise ObserverError(f'Expected one visible Qt main window; got {len(candidates)}')
        target=candidates[0]
        self.x.XSetInputFocus(self.dpy,target['id'],2,0)
        self.check()
        focused,revert=C.c_ulong(),C.c_int()
        self.x.XGetInputFocus(self.dpy,C.byref(focused),C.byref(revert))
        self.check()
        if focused.value!=target['id']:
            raise ObserverError('XGetInputFocus does not match verified Qt main-window ID')
        return target

    def key(self,key,down):
        sym=self.x.XStringToKeysym(key.encode('ascii'))
        code=self.x.XKeysymToKeycode(self.dpy,sym)
        if not code or self.xt.XTestFakeKeyEvent(self.dpy,code,int(down),0)!=1:
            raise ObserverError('XTest refused key event')
        self.check()

    def open_dialog(self):
        """PR #152 harmless Ctrl+O test; never select a ROM or type a path."""
        self.key('Control_L', True)
        try:
            self.key('o', True)
            self.key('o', False)
        finally:
            self.key('Control_L', False)
        for _ in range(50):
            dialogs=[w for w in self.windows()
                     if 'Select ROM' in w['name'] and w['map_state']==IS_VIEWABLE
                     and w['width']>100 and w['height']>100]
            if len(dialogs)==1:
                return True
            time.sleep(0.12)
        raise ObserverError('Ctrl+O did not open exactly one visible Select ROM dialog')

    def close(self):
        if self._closed:return
        self._closed=True
        try:
            if self.dpy:
                try:self.x.XSync(self.dpy,0)
                finally:
                    self.x.XCloseDisplay(self.dpy)
                    self.dpy=None
        finally:
            # Restore global Xlib handler while callback and CDLL are still alive.
            # Do not release self._handler before XSetErrorHandler returns.
            if self._handler is not None:
                self.x.XSetErrorHandler(C.c_void_p(self._old_handler))
                self._handler=None
                self._old_handler=None


def child_work(display, authority, *, simulate_title=False, verify_dialog=False):
    require_parent_x11(display,authority)
    client=XClient(display)
    try:
        try:
            match=client.focus_main_window()
        except ObserverError as exc:
            if str(exc)=='Expected one visible Qt main window; got 0':
                return {'status':'NOT_READY'}
            raise
        original=dict(match)
        if simulate_title:
            title='mGBA - TEST (45.3 fps) - 0.10.5'
            client.x.XStoreName(client.dpy,match['id'],title.encode())
            client.check()
            match=client.focus_main_window()
            if match['id']!=original['id'] or match['name']!=title:
                raise ObserverError('simulated title failed stable window identity')
        if verify_dialog:
            # Same genuine focus target and private worker. No file is selected.
            if not client.open_dialog():
                raise ObserverError('Select ROM dialog was not verified')
        return {'status':'PASS','window_id':match['id'],'title':match['name'],
                'class':list(match['class']),'map_state':match['map_state'],
                'dimensions':[match['width'],match['height']],
                'title_changed':simulate_title,'focus_verified':True,
                'dialog_verified':verify_dialog}
    finally:
        client.close()
        client.close()  # guarantee idempotent cleanup


def call_isolated_xlib(display, authority, *, simulate_title=False, verify_dialog=False, timeout=8):
    """Parent never loads Xlib; fail closed on child SIGSEGV/timeout/invalid JSON."""
    require_parent_x11(display,authority)
    if type(simulate_title) is not bool or type(verify_dialog) is not bool or timeout<=0 or timeout>15:
        raise ObserverError('invalid bounded helper arguments')
    args=[sys.executable,str(Path(__file__).resolve()),'--_xlib_helper',
          '--display',display,'--authority',authority]
    if simulate_title:args.append('--simulate-title')
    if verify_dialog:args.append('--verify-dialog')
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'DISPLAY':display,
         'XAUTHORITY':authority,'PYTHONNOUSERSITE':'1'}
    try:
        result=subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              text=True,timeout=timeout,check=False,start_new_session=True)
    except subprocess.TimeoutExpired as exc:
        raise ObserverError('isolated Xlib helper timeout; inconclusive') from exc
    if result.returncode!=0:
        raise ObserverError(f'isolated Xlib helper failure exit={result.returncode}; inconclusive')
    try:
        output=json.loads(result.stdout)
    except (ValueError,TypeError) as exc:
        raise ObserverError('invalid isolated helper output') from exc
    if output=={'status':'NOT_READY'}:
        raise ObserverError('empty Qt main window not yet available')
    if not isinstance(output,dict) or set(output)!={'status','window_id','title','class','map_state','dimensions','title_changed','focus_verified','dialog_verified'}:
        raise ObserverError('unexpected helper output schema')
    if (output['status']!='PASS' or output['class']!=['mgba-qt','mGBA'] or
        output['map_state']!=IS_VIEWABLE or not MAIN_TITLE.fullmatch(output['title']) or
        output['focus_verified'] is not True or output['title_changed'] is not simulate_title or
        output['dialog_verified'] is not verify_dialog or
        type(output['window_id']) is not int or output['window_id']<=0 or
        type(output['dimensions']) is not list or len(output['dimensions'])!=2 or
        any(type(d) is not int for d in output['dimensions']) or
        output['dimensions'][0]<240 or output['dimensions'][1]<160):
        raise ObserverError('helper failed strict window identity checks')
    return output


def verify_empty_mgba(appimage):
    """One no-game empty-Qt/Xvfb test; uses verified AppImage only."""
    if appimage.name!='mGBA-0.10.5-appimage-x64.appimage' or not appimage.is_file() or appimage.stat().st_size!=APPIMAGE_SIZE:
        raise ObserverError('wrong AppImage file name/size')
    with appimage.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=APPIMAGE_SHA256:
            raise ObserverError('AppImage checksum mismatch')
    for tool in ('Xvfb','xauth','xdpyinfo'):
        if not shutil.which(tool):raise ObserverError(f'missing {tool}')
    with tempfile.TemporaryDirectory(prefix='sg_empty_xlib_hardened_') as td:
        root=Path(td)
        copied=root/'mgba.appimage'
        shutil.copyfile(appimage,copied)
        copied.chmod(0o700)
        subprocess.run([str(copied),'--appimage-extract'],cwd=root,check=True,timeout=70,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        exe=root/'squashfs-root/usr/bin/mgba-qt'
        ver=subprocess.run([str(exe),'--version'],text=True,capture_output=True,check=True,timeout=7)
        if '0.10.5' not in ver.stdout+ver.stderr or MGBA_COMMIT not in ver.stdout+ver.stderr:
            raise ObserverError('mGBA 0.10.5 commit mismatch')
        free=[i for i in range(125,200) if not Path(f'/tmp/.X11-unix/X{i}').exists() and not Path(f'/tmp/.X{i}-lock').exists()]
        if not free:raise ObserverError('no available Xvfb display')
        display=f':{free[0]}'
        authority=root/'Xauthority'
        authority.touch(mode=0o600)
        subprocess.run(['xauth','-f',str(authority),'add',display,'.',secrets.token_hex(16)],check=True,
                       timeout=5,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        env={**os.environ,'DISPLAY':display,'XAUTHORITY':str(authority),'HOME':td,'XDG_CONFIG_HOME':td,
             'QT_QPA_PLATFORM':'xcb','SDL_AUDIODRIVER':'dummy','LIBGL_ALWAYS_SOFTWARE':'1','QT_OPENGL':'software'}
        proc=[]
        old_disp,old_auth=os.environ.get('DISPLAY'),os.environ.get('XAUTHORITY')
        try:
            proc.append(subprocess.Popen(['Xvfb',display,'-screen','0','800x600x24',
                                          '-nolisten','tcp','-auth',str(authority)],env=env,
                                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            for _ in range(60):
                if proc[0].poll() is not None:raise ObserverError('Xvfb crashed')
                if subprocess.run(['xdpyinfo','-display',display],env=env,
                                  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2).returncode==0:break
                time.sleep(.1)
            else:raise ObserverError('Xvfb never ready')
            proc.append(subprocess.Popen([str(exe)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            # Parent credentials are explicitly synchronized, not guessed by worker.
            os.environ['DISPLAY'],os.environ['XAUTHORITY']=display,str(authority)
            first=None
            for _ in range(55):
                if proc[1].poll() is not None:raise ObserverError('empty mGBA exited before focus check')
                try:
                    first=call_isolated_xlib(display,str(authority),timeout=5)
                    break
                except ObserverError as e:
                    if str(e)!='empty Qt main window not yet available':
                        raise
                time.sleep(.1)
            if first is None:raise ObserverError('no correct empty Qt window')
            second=call_isolated_xlib(display,str(authority),simulate_title=True,
                                      verify_dialog=True,timeout=12)
            if first['window_id']!=second['window_id']:
                raise ObserverError('Qt window ID changed during simulated FPS-title validation')
            if first['dialog_verified'] is not False or second['dialog_verified'] is not True:
                raise ObserverError('original Ctrl+O empty-dialog verification was not retained')
            print(json.dumps({'empty_xlib_test':'PASS','first':first,'second':second},sort_keys=True))
        finally:
            for name,old in [('DISPLAY',old_disp),('XAUTHORITY',old_auth)]:
                if old is None:os.environ.pop(name,None)
                else:os.environ[name]=old
            for child in reversed(proc):
                if child.poll() is None:child.terminate()
            for child in reversed(proc):
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill();child.wait(timeout=3)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--appimage',type=Path)
    parser.add_argument('--_xlib_helper',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--display',help=argparse.SUPPRESS)
    parser.add_argument('--authority',help=argparse.SUPPRESS)
    parser.add_argument('--simulate-title',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--verify-dialog',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args._xlib_helper:
        if args.appimage is not None or args.display is None or args.authority is None:
            raise ObserverError('invalid internal helper arguments')
        print(json.dumps(child_work(args.display,args.authority,
                                   simulate_title=args.simulate_title,
                                   verify_dialog=args.verify_dialog)))
    elif (args.appimage is not None and args.display is None and args.authority is None
          and not args.simulate_title and not args.verify_dialog):
        verify_empty_mgba(args.appimage)
    else:raise ObserverError('only a no-game --appimage test is supported')

if __name__=='__main__':
    try:main()
    except (ObserverError,OSError,ValueError,subprocess.SubprocessError) as exc:
        raise SystemExit(f'INCONCLUSIVE: {type(exc).__name__}: {exc}') from None
