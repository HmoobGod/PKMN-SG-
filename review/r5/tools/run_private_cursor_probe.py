#!/usr/bin/env python3
"""Guarded LOCAL disposable game replay. Never accesses network or writes originals.

Compile the supplied adapter on the private host. The caller must supply exact
SHA256 fingerprints for ROM, save and the mGBA executable. Only outputs to the
provided fresh private output directory. No raw logs are part of a public zip.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for chunk in iter(lambda:fh.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def check(path,want):
    if not re.fullmatch(r'[0-9a-f]{64}',want):raise ValueError('invalid SHA256 pin')
    if sha(path)!=want:raise ValueError('private input fingerprint mismatch')


def cpu_correlated_battle_candidate(frame_rows, cursor_rows, owner_rows):
    """Only a bounded, UNVERIFIED host-trace candidate; not native acceptance.

    Pixel-based battle UI heuristics can match the title screen. Require
    original CPU player0 emitter and an original selector slot store too.
    """
    ui=any(x.get('event')=='battle_ui_candidate' for x in frame_rows)
    from audit_private_slot3_timeline_r5 import evaluate as slot_audit
    from audit_private_player0_switch_emitter import evaluate as action_audit
    try:
        slots=slot_audit(cursor_rows)
        actions=action_audit(owner_rows)
    except (TypeError,ValueError,KeyError,IndexError):
        return False
    return bool(ui and slots['original_player0_slot_writes']>0 and
                actions['player0_fight_action0_emitter_rows']>0 and
                actions['player0_move_action10_emitter_rows']>0 and
                actions['player0_unclassified_emitter_rows']==0)


def run(args):
    inp=[args.private_rom.resolve(),args.private_save.resolve(),args.emulator.resolve(),args.cursor_adapter.resolve()]
    if not all(p.is_file() for p in inp):raise ValueError('missing private input')
    if len(set(inp))!=4:raise ValueError('private inputs must be distinct')
    if not 1<=args.frames<=12000:raise ValueError('invalid frame limit')
    if not re.fullmatch(r'\d+:\d+:\d+(,\d+:\d+:\d+)*',args.events):raise ValueError('bad input script')
    for item in args.events.split(','):
        a,b,mask=(int(x) for x in item.split(':'))
        if a>=b or b>12000 or mask<0 or mask&~0x3ff:raise ValueError('invalid button event')
    for f,h in zip(inp[:3],[args.rom_sha,args.save_sha,args.emulator_sha]):check(f,h)
    out=args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('private output directory must be empty')
    if any(out==p or out in p.parents for p in inp):raise ValueError('unsafe output directory')
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    copy_rom=out/'Pokemon_SoulGold_TEST_COPY.gba'; copy_save=out/'Pokemon_SoulGold_TEST_COPY.sav'
    shutil.copyfile(inp[0],copy_rom);shutil.copyfile(inp[1],copy_save)
    copy_rom.chmod(stat.S_IRUSR);copy_save.chmod(stat.S_IRUSR)
    check(copy_rom,args.rom_sha);check(copy_save,args.save_sha)
    env={**os.environ,
         'LD_PRELOAD':str(inp[3]),'SG_FRAMES':str(args.frames),
         'SG_SAVE_PATH':str(copy_save),'SG_INPUT_EVENTS':args.events,
         'SG_CURSOR_LOG':str(out/'cursor_private.jsonl'),
         'SG_OWNER_LOG':str(out/'owner_private.jsonl'),
         'SG_OUTPUT_LOG':str(out/'frame_private.jsonl'),
         'SG_SCREEN_FILE':str(out/'screen_private.rgba'),
         'SG_SCREEN_FRAME':str(args.frames-1)}
    env.pop('SG_PP_LOG',None) # modes intentionally exclusive
    try:
        with (out/'stderr_private.log').open('w') as err:
            proc=subprocess.run([str(inp[2]),'-S','0xFF',str(copy_rom)],cwd=out,env=env,
                                stdout=subprocess.DEVNULL,stderr=err,timeout=25,check=False)
        rows=[json.loads(s) for s in (out/'frame_private.jsonl').read_text().splitlines()]
        details={k:next((r for r in rows if r.get('event')==k),{})
                 for k in ('pp_hook_installed','save_load','battle_ui_candidate','completed')}
        completed=details['completed'];save=details['save_load']
        cursor_rows=[json.loads(line) for line in (out/'cursor_private.jsonl').read_text().splitlines()]
        owner_rows=[json.loads(line) for line in (out/'owner_private.jsonl').read_text().splitlines()]
        cpu_correlated=cpu_correlated_battle_candidate(rows,cursor_rows,owner_rows)
        if proc.returncode or not details['pp_hook_installed'] or not completed or save.get('loaded') is not True or save.get('full_128kb_match') is not True:
            raise RuntimeError('emulator run not independently complete; do not promote')
        summary={'private_disposable_execution_completed':True,
                 'frames':completed.get('frames'),
                 'battle_ui_first_frame':details['battle_ui_candidate'].get('frame'),
                 'cpu_correlated_battle_candidate_only':cpu_correlated,
                 'pixel_battle_ui_only_is_not_confirmation':True,
                 'postbattle_zero_requested':completed.get('postbattle_nonzero_requested_frames')==0,
                 'postbattle_zero_observed':completed.get('postbattle_nonzero_observed_frames')==0,
                 'formal_native_acceptance_scenarios':0,
                 'manual_fallback_certified':False,
                 'production_authorized':False}
        check(copy_rom,args.rom_sha);check(copy_save,args.save_sha)
        check(inp[0],args.rom_sha);check(inp[1],args.save_sha);check(inp[2],args.emulator_sha)
        (out/'summary_private.json').write_text(json.dumps(summary,indent=2)+'\n')
        return summary
    finally:
        check(inp[0],args.rom_sha);check(inp[1],args.save_sha)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--private-rom',required=True,type=Path)
    ap.add_argument('--private-save',required=True,type=Path)
    ap.add_argument('--emulator',required=True,type=Path)
    ap.add_argument('--cursor-adapter',required=True,type=Path)
    ap.add_argument('--rom-sha',required=True)
    ap.add_argument('--save-sha',required=True)
    ap.add_argument('--emulator-sha',required=True)
    ap.add_argument('--output-dir',required=True,type=Path)
    ap.add_argument('--frames',type=int,default=8000)
    ap.add_argument('--events',required=True)
    print(json.dumps(run(ap.parse_args()),indent=2,sort_keys=True))

if __name__=='__main__':main()
