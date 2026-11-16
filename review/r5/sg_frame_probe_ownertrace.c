#define _GNU_SOURCE
#include <dlfcn.h>
#include <elf.h>
#include <link.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

/* Experimental adapter for the EXACT unstripped, hash-pinned Linux binary
   included in the owner-provided soulgold-master.zip. No original ROM writes.
   Executable/private-save never leave the local container. */
#define CORE_SLOT 0x173e48UL
#define RUN_FRAME_FUNC 0x66580UL
#define RUN_LOOP_FUNC 0x66570UL
#define SET_KEYS_FUNC 0x66510UL
#define MAX_FRAME 12000

static uintptr_t exe_base;
static void *(*original_runframe)(void *);
static void (*setkeys)(void *, unsigned int);
static FILE *log_file;
static _Atomic unsigned long frame_count;
static _Atomic int installed;
static unsigned long stop_frames=600;
static const char *sg_save_path;
static int sg_save_load_ok=-1;
static int sg_save_full_match=-1;
static unsigned char *sg_pixels;
static unsigned long sg_capture_frame=600;
static const char *sg_capture_path;
static const char *sg_series_prefix;
static unsigned long sg_series_start=3000, sg_series_end=4200, sg_series_step=50;
static unsigned int a_start=80, a_end=85, b_start=0, b_end=0;
static unsigned int start_start=40, start_end=45;
static int exit_status=0;
static struct {unsigned long first,last;unsigned int mask;} sg_events[96];
static int sg_event_count=0;
static bool sg_event_mode=false;
static unsigned long sg_battle_seen_frame=0;
static unsigned long sg_battle_input_frames=0;
static unsigned long sg_nonzero_inputs_after_battle=0;
static unsigned long sg_nonzero_observed_after_battle=0;
static bool sg_stop_input_in_battle=true;
static int output_every=60;

/* EXPERIMENTAL EXACT-BINARY instrumentation: original GBA memory stores only.
 * Never modifies guest ROM/save, executes original store unmodified. Observes
 * candidate battle structs in private working EWRAM, not production acceptance. */
typedef void (*sg_store_fn)(void*, uint32_t, int, int*);
static sg_store_fn sg_original_store8,sg_original_store16,sg_original_store32;
static unsigned long sg_pp_events=0;
static unsigned long sg_store_events=0;
static FILE *sg_pp_log=NULL;
static int sg_pp_trace_enabled=0;
static uint32_t sg_targets[4]={0,0,0,0};
static _Thread_local int sg_trace_reentry=0;
static FILE *sg_owner_log=NULL;
static unsigned long sg_owner_count=0;
static bool sg_owner_hit(uint32_t pc) {
  return (pc>=0x0806BD00u && pc<=0x0806BF80u) ||
         (pc>=0x080625F0u && pc<=0x08062680u) ||
         (pc>=0x08064200u && pc<=0x08064680u) ||
         (pc>=0x080942F0u && pc<=0x08094430u) ||
         (pc>=0x0809E690u && pc<=0x0809E700u);
}
static void sg_owner_store_probe(void *cpu,uint32_t address,int value,int width) {
  if(!sg_owner_log || sg_trace_reentry || atomic_load(&frame_count)<2750 || sg_owner_count>=12000)return;
  uint32_t raw_pc=*(uint32_t*)((char*)cpu+0x3c);
  uint32_t thumb=*(uint32_t*)((char*)cpu+0x124);
  if(thumb!=1 || raw_pc<4 || !sg_owner_hit(raw_pc-4))return;
  uint32_t instpc=raw_pc-4;
  uint32_t* regs=(uint32_t*)cpu;
  fprintf(sg_owner_log,"{\"f\":%lu,\"pc\":\"0x%08x\",\"raw_pc\":\"0x%08x\",\"dst\":\"0x%08x\",\"width\":%d,\"value\":%u,\"lr\":\"0x%08x\",\"sp\":\"0x%08x\",\"r\":[",atomic_load(&frame_count),instpc,raw_pc,address,width,(unsigned)value,regs[14],regs[13]);
  for(int j=0;j<8;j++)fprintf(sg_owner_log,"%s%u",j?",":"",regs[j]);
  fputs("]}\n",sg_owner_log);
  if(++sg_owner_count%256==0)fflush(sg_owner_log);
}
static void safe_flush(void);
static void sg_trace_store(void* cpu,uint32_t address,int value,int *cycles,int width,sg_store_fn original){
  if(!original)return;
  sg_owner_store_probe(cpu,address,value,width);
  uint32_t at=(address & 0x0FFFFFFFu);
  int matched=-1;
  for(int k=0;k<4;k++){
    if(sg_targets[k] && at>=sg_targets[k]+0x25 && at<sg_targets[k]+0x29+width-1){matched=k;break;}
  }
  if(!sg_pp_trace_enabled || matched<0 || sg_trace_reentry){original(cpu,address,value,cycles);return;}
  ++sg_trace_reentry;
  uint32_t pre_pc=*(uint32_t*)((char*)cpu+0x3c);
  uint32_t arm_inst=*(uint32_t*)((char*)cpu+0x11c);
  uint32_t thumb=*(uint32_t*)((char*)cpu+0x124);
  unsigned char* gba=*(unsigned char**)((char*)cpu+0x1e8);
  unsigned char* ewram=gba?*(unsigned char**)(gba+0x28):NULL;
  uint8_t before[4]={0},after[4]={0};
  uint32_t region=(address & 0xFF000000u);
  uint32_t offset=address & 0x3FFFF;
  if(ewram && region==0x02000000u && offset+width<=0x40000){memcpy(before,ewram+offset,width);}
  original(cpu,address,value,cycles);
  if(ewram && region==0x02000000u && offset+width<=0x40000){memcpy(after,ewram+offset,width);}
  if(sg_pp_log && sg_store_events++ < 3000){
    fprintf(sg_pp_log,"{\"f\":%lu,\"address\":\"0x%08x\",\"width\":%d,\"before\":%u,\"after\":%u,\"value\":%u,\"raw_pc\":\"0x%08x\",\"op\":\"0x%08x\",\"thumb_flag\":%u,\"target\":%d,\"r\":[",
      atomic_load(&frame_count),address,width,before[0],after[0],(unsigned)value,pre_pc,arm_inst,thumb,matched);
    for(int r=0;r<8;r++)fprintf(sg_pp_log,"%s%u",r?",":"",((uint32_t*)cpu)[r]);
    fputs("]}\n",sg_pp_log);
    fflush(sg_pp_log);
  }
  if(before[0]!=after[0])++sg_pp_events;
  --sg_trace_reentry;
}
static void sg_write8(void *cpu,uint32_t addr,int value,int *cycle){sg_trace_store(cpu,addr,value,cycle,1,sg_original_store8);}
static void sg_write16(void *cpu,uint32_t addr,int value,int *cycle){sg_trace_store(cpu,addr,value,cycle,2,sg_original_store16);}
static void sg_write32(void *cpu,uint32_t addr,int value,int *cycle){sg_trace_store(cpu,addr,value,cycle,4,sg_original_store32);}

static void sg_refresh_candidate(void* core,unsigned long f){
  if(!sg_pp_trace_enabled || f<2500)return;
  unsigned char *board=*(unsigned char**)((unsigned char*)core+8);
  unsigned char *mem=board?*(unsigned char**)(board+0x28):NULL;
  if(!mem)return;
  uint32_t fresh[4]={0};
  int k=0;
  for(size_t off=0;off+0x29<=0x40000 && k<4;off+=2){
    /* species 356, four expected move IDs from project battle struct */
    if(mem[off]==0x64 && mem[off+1]==0x01 &&
       mem[off+12]==0x45 && mem[off+13]==0x01 &&
       mem[off+14]==0x9d && mem[off+15]==0x00 &&
       mem[off+16]==0x5c && mem[off+17]==0x00 &&
       mem[off+18]==0x0d && mem[off+19]==0x01){
       fresh[k++]=0x02000000u+(uint32_t)off;
    }
  }
  for(int j=0;j<4;j++){
    if(fresh[j]!=sg_targets[j]){
      if(sg_pp_log && fresh[j]){
        unsigned int ix=fresh[j]-0x02000000u;
        fprintf(sg_pp_log,"{\"event\":\"pp_candidate\",\"f\":%lu,\"base\":\"0x%08x\",\"pp\":[%u,%u,%u,%u]}\n",f,fresh[j],mem[ix+0x25],mem[ix+0x26],mem[ix+0x27],mem[ix+0x28]);
        fflush(sg_pp_log);
      }
      sg_targets[j]=fresh[j];
    }
  }
}

static void sg_install_pp_trace(void* core){
 if(!sg_pp_trace_enabled)return;
 unsigned char* cpu=*(unsigned char**)core;
 if(!cpu)return;
 uintptr_t* loc8=(uintptr_t*)(cpu+0x158),*loc16=(uintptr_t*)(cpu+0x150),*loc32=(uintptr_t*)(cpu+0x148);
 if(*loc8 != exe_base+0x6c320 || *loc16 != exe_base+0x6bb60 || *loc32 != exe_base+0x6c860){
   if(log_file){fprintf(log_file,"{\"event\":\"pp_hook_pointer_mismatch\",\"actual_offsets\":[\"0x%lx\",\"0x%lx\",\"0x%lx\"],\"expected_offsets\":[\"0x%lx\",\"0x%lx\",\"0x%lx\"]}\n",(unsigned long)(*loc8-exe_base),(unsigned long)(*loc16-exe_base),(unsigned long)(*loc32-exe_base),(unsigned long)0x6c320,(unsigned long)0x6bb60,(unsigned long)0x6c860);safe_flush();}
   return;
 }
 sg_original_store8=(sg_store_fn)*loc8;
 sg_original_store16=(sg_store_fn)*loc16;
 sg_original_store32=(sg_store_fn)*loc32;
 *loc8=(uintptr_t)&sg_write8;
 *loc16=(uintptr_t)&sg_write16;
 *loc32=(uintptr_t)&sg_write32;
 if(log_file){fprintf(log_file,"{\"event\":\"pp_hook_installed\"}\n");safe_flush();}
}

static int dl_iter(struct dl_phdr_info *p, size_t sz, void *user) {
  (void)sz;(void)user;
  if (!p->dlpi_name || p->dlpi_name[0]=='\0') {
    exe_base=(uintptr_t)p->dlpi_addr;
    return 1;
  }
  return 0;
}
static uint64_t fnv(const unsigned char *p, size_t len){
  uint64_t v=14695981039346656037ULL;
  for(size_t i=0;i<len;i++) v=(v ^ p[i])*1099511628211ULL;
  return v;
}
static unsigned int input_for_frame(unsigned long f){
  unsigned int keys=0;
  if(sg_stop_input_in_battle && sg_battle_seen_frame && f>sg_battle_seen_frame)return 0;
  if(sg_event_mode){
    for(int i=0;i<sg_event_count;i++)
      if(f>=sg_events[i].first && f<sg_events[i].last)keys|=sg_events[i].mask;
    return keys;
  }
  if(f>=start_start && f<start_end) keys|=8; /* START */
  if(f>=a_start && f<a_end) keys|=1; /* A */
  if(f>=b_start && f<b_end) keys|=2; /* B */
  return keys;
}
static void safe_flush(void){ if(log_file) fflush(log_file); }
static void *frame_hook(void *core){
  unsigned long f=atomic_fetch_add(&frame_count,1)+1;
  if(f==1){
    sg_install_pp_trace(core);
    bool (*load_save)(void *, const char *, int) = (bool (*)(void *,const char *,int))dlsym(RTLD_DEFAULT,"mCoreLoadSaveFile");
    sg_save_load_ok=(load_save && sg_save_path && load_save(core,sg_save_path,0))?1:0;
    unsigned char *board=*(unsigned char**)((unsigned char*)core+8);
    unsigned char *mem=board?*(unsigned char**)(board+0x4a8):NULL;
    FILE *fp=sg_save_path?fopen(sg_save_path,"rb"):NULL;
    if(fp && mem){
      unsigned char *buf=malloc(131072);
      if(buf){
        size_t n=fread(buf,1,131072,fp);
        sg_save_full_match=(n==131072 && !memcmp(buf,mem,131072))?1:0;
        free(buf);
      }
    }
    if(fp)fclose(fp);
    if(sg_capture_path){
       sg_pixels=calloc(240*160,4);
       void (*associate)(void *, void *) = (void(*)(void*,void*))dlsym(RTLD_DEFAULT,"GBAVideoAssociateRenderer");
       if(sg_pixels && associate && board){
          unsigned char *renderer=(unsigned char*)core+0x1678;
          *(unsigned char**)(renderer+0x110)=sg_pixels;
          *(int*)(renderer+0x118)=240;
          associate(board+0xc90,renderer);
          if(log_file){fprintf(log_file,"{\"event\":\"software_renderer_attached\"}\n");safe_flush();}
       }
    }
    if(log_file){fprintf(log_file,"{\"event\":\"save_load\",\"loaded\":%s,\"full_128kb_match\":%s}\n",sg_save_load_ok?"true":"false",sg_save_full_match==1?"true":"false");safe_flush();}
  }
  sg_refresh_candidate(core,f);
  unsigned int requested_keys=input_for_frame(f);
  if(sg_battle_seen_frame && f>sg_battle_seen_frame){
      ++sg_battle_input_frames;
      if(requested_keys)++sg_nonzero_inputs_after_battle;
  }
  if(setkeys) setkeys(core,requested_keys);
  original_runframe(core);
  if(sg_battle_seen_frame && f>sg_battle_seen_frame){
     unsigned char *br=*(unsigned char**)((unsigned char*)core+8);
     if(br && *(uint16_t*)(br+0x1ab4))++sg_nonzero_observed_after_battle;
  }
  if(sg_pixels && !sg_battle_seen_frame && f>2950){
     unsigned char *p=sg_pixels+((145*240+5)*4);
     unsigned char *q=sg_pixels+((145*240+120)*4);
     if(p[0]>50 && p[0]<150 && abs((int)p[0]-p[1])<=6 && abs((int)p[1]-p[2])<=12 &&
        q[0]>15 && q[0]<70 && abs((int)q[0]-q[1])<=6 && abs((int)q[1]-q[2])<=6){
        sg_battle_seen_frame=f;
        if(log_file){fprintf(log_file,"{\"event\":\"battle_ui_candidate\",\"frame\":%lu}\n",f);safe_flush();}
     }
  }
  if(sg_pixels && sg_capture_path && f==sg_capture_frame){
    FILE *out=fopen(sg_capture_path,"wb");
    if(out){fwrite(sg_pixels,4,240*160,out);fclose(out);}
    if(log_file){fprintf(log_file,"{\"event\":\"screen_capture\",\"frame\":%lu,\"ok\":%s}\n",f,out?"true":"false");safe_flush();}
  }
  if(sg_series_prefix && sg_pixels && f>=sg_series_start && f<=sg_series_end && ((f-sg_series_start)%sg_series_step)==0){
    char name[512];
    int n=snprintf(name,sizeof(name),"%s_screen_%05lu.rgba",sg_series_prefix,f);
    if(n>0 && n<(int)sizeof(name)){
       FILE *im=fopen(name,"wb");if(im){fwrite(sg_pixels,4,240*160,im);fclose(im);}
    }
    unsigned char *board=*(unsigned char**)((unsigned char*)core+8);
    unsigned char *ewram=board?*(unsigned char**)(board+0x28):NULL;
    n=snprintf(name,sizeof(name),"%s_ewram_%05lu.bin",sg_series_prefix,f);
    if(ewram && n>0 && n<(int)sizeof(name)){
       FILE *dump=fopen(name,"wb");if(dump){fwrite(ewram,1,0x40000,dump);fclose(dump);}
    }
    if(log_file){fprintf(log_file,"{\"event\":\"series_capture\",\"frame\":%lu}\n",f);safe_flush();}
  }
  if(f==1 || f%output_every==0 || f>=stop_frames){
    unsigned char *board=*(unsigned char**)((unsigned char*)core+8);
    unsigned char *cpu=*(unsigned char**)core;
    uint32_t pc=cpu?*(uint32_t*)(cpu+15*4):0;
    unsigned char *ewram=board?*(unsigned char**)(board+0x28):0;
    unsigned char *iwram=board?*(unsigned char**)(board+0x30):0;
    unsigned char *flash=board?*(unsigned char**)(board+0x4a8):0;
    uint32_t save_type=board?*(uint32_t*)(board+0x4a0):0;
    unsigned int observed_keys=board?*(uint16_t*)(board+0x1ab4):0;
    uint32_t hw_frame=board?*(uint32_t*)(board+0x14d8):0;
    uint32_t cpsr=cpu?*(uint32_t*)(cpu+0x44):0;
    if(log_file){
      fprintf(log_file,"{\"event\":\"frame\",\"f\":%lu,\"pc\":\"%08x\",\"keys\":%u,\"observed_keys\":%u,\"ewram_fnv256\":\"%016llx\",\"ewram_full_fnv\":\"%016llx\",\"iwram_fnv256\":\"%016llx\",\"iwram_full_fnv\":\"%016llx\",\"flash_fnv256\":\"%016llx\",\"save_type\":%u,\"hw_frame\":%u,\"cpsr_guess\":%u}\n",
        f,pc,input_for_frame(f),observed_keys,
        (unsigned long long)(ewram?fnv(ewram,256):0),
        (unsigned long long)(ewram?fnv(ewram,262144):0),
        (unsigned long long)(iwram?fnv(iwram,256):0),
        (unsigned long long)(iwram?fnv(iwram,32768):0),
        (unsigned long long)(flash?fnv(flash,256):0),save_type,hw_frame,cpsr);
      safe_flush();
    }
  }
  if(f>=stop_frames){
    if(sg_owner_log)fflush(sg_owner_log);
    if(sg_pp_log)fflush(sg_pp_log);
    if(log_file){fprintf(log_file,"{\"event\":\"pp_trace_summary\",\"observed_changed_writes\":%lu,\"total_matched_writes\":%lu}\n",sg_pp_events,sg_store_events);safe_flush();}

    if(log_file){fprintf(log_file,"{\"event\":\"completed\",\"frames\":%lu,\"exit_code\":%d,\"postbattle_frames\":%lu,\"postbattle_nonzero_requested_frames\":%lu,\"postbattle_nonzero_observed_frames\":%lu}\n",f,exit_status,sg_battle_input_frames,sg_nonzero_inputs_after_battle,sg_nonzero_observed_after_battle);safe_flush();}
    _exit(exit_status);
  }
  return NULL;
}
static void *patch_loop(void *unused){
  (void)unused;
  for(unsigned long it=0;it<10000000 && !atomic_load(&installed);++it){
    void *core=*(void*volatile*)(exe_base+CORE_SLOT);
    if(core){
      uintptr_t *words=(uintptr_t*)core;
      uintptr_t runp=exe_base+RUN_FRAME_FUNC;
      uintptr_t keyp=exe_base+SET_KEYS_FUNC;
      uintptr_t loopp=exe_base+RUN_LOOP_FUNC;
      int run_index=-1,loop_index=-1,key_index=-1;
      for(size_t k=0x12f0/8;k<0x1500/8;k++){
        if(words[k]==runp) run_index=(int)k;
        if(words[k]==loopp) loop_index=(int)k;
        if(words[k]==keyp) key_index=(int)k;
      }
      if(run_index>=0 && loop_index>=0 && key_index>=0){
        original_runframe=(void *(*)(void *))words[run_index];
        setkeys=(void (*)(void*,unsigned int))words[key_index];
        words[loop_index]=(uintptr_t)&frame_hook;
        atomic_store(&installed,1);
        if(log_file){fprintf(log_file,"{\"event\":\"installed\",\"run_offset\":%d,\"loop_offset\":%d,\"key_offset\":%d}\n",run_index*8,loop_index*8,key_index*8);safe_flush();}
        break;
      }
    }
    if(it%10000==0) sched_yield();
  }
  return NULL;
}
static void read_env(void){
  const char* s;
  if((s=getenv("SG_INPUT_EVENTS"))){
    sg_event_mode=true;
    char *tmp=strdup(s);
    if(tmp){
      char *saveptr=NULL;
      for(char *tok=strtok_r(tmp,",",&saveptr);tok && sg_event_count<96;tok=strtok_r(NULL,",",&saveptr)){
        unsigned long start,end;
        unsigned int mask;
        char trailing;
        if(sscanf(tok,"%lu:%lu:%u%c",&start,&end,&mask,&trailing)==3 && start<end && end<=MAX_FRAME && (mask & ~0x3FF)==0){
          sg_events[sg_event_count].first=start;
          sg_events[sg_event_count].last=end;
          sg_events[sg_event_count].mask=mask;
          sg_event_count++;
        } else {
          sg_event_count=0;
          if(log_file)fprintf(log_file,"{\"event\":\"invalid_input_script\"}\n");
          break;
        }
      }
      free(tmp);
    }
  }
  if((s=getenv("SG_FRAMES"))) {unsigned long n=strtoul(s,0,10);if(n>0&&n<=MAX_FRAME)stop_frames=n;}
  if((s=getenv("SG_A_START")))a_start=(unsigned int)strtoul(s,0,10);
  if((s=getenv("SG_A_END")))a_end=(unsigned int)strtoul(s,0,10);
  if((s=getenv("SG_START_START")))start_start=(unsigned int)strtoul(s,0,10);
  if((s=getenv("SG_START_END")))start_end=(unsigned int)strtoul(s,0,10);
  if((s=getenv("SG_B_START")))b_start=(unsigned int)strtoul(s,0,10);
  if((s=getenv("SG_B_END")))b_end=(unsigned int)strtoul(s,0,10);
  if((s=getenv("SG_EVERY"))){unsigned long n=strtoul(s,0,10); if(n>0&&n<=3600)output_every=(int)n;}
  if((s=getenv("SG_OUTPUT_LOG")))log_file=fopen(s,"w");
  if((s=getenv("SG_SAVE_PATH")))sg_save_path=s;
  if((s=getenv("SG_PP_LOG"))){sg_pp_log=fopen(s,"w");sg_pp_trace_enabled=sg_pp_log!=NULL;}
  if((s=getenv("SG_OWNER_LOG")))sg_owner_log=fopen(s,"w");
  if((s=getenv("SG_SCREEN_FILE")))sg_capture_path=s;
  if((s=getenv("SG_SCREEN_FRAME")))sg_capture_frame=strtoul(s,0,10);
  if((s=getenv("SG_SERIES_PREFIX")))sg_series_prefix=s;
  if((s=getenv("SG_SERIES_FROM")))sg_series_start=strtoul(s,0,10);
  if((s=getenv("SG_SERIES_TO")))sg_series_end=strtoul(s,0,10);
  if((s=getenv("SG_SERIES_STEP"))){unsigned long n=strtoul(s,0,10);if(n>0)sg_series_step=n;}
}
__attribute__((constructor)) static void init(void){
  read_env();
  dl_iterate_phdr(dl_iter,NULL);
  if(!exe_base) {if(log_file)fprintf(log_file,"{\"event\":\"no_base\"}\n");return;}
  pthread_t t;
  if(pthread_create(&t,NULL,patch_loop,NULL)==0) pthread_detach(t);
}
