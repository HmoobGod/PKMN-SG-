/* PUBLIC SYNTHETIC JSON fixture for the exact 44-byte original player0
 * read-only CPU request copier. Every field comes from the real C Proof
 * produced by the fake RAM/CPU (NO original ROM, save or emulator).
 * Deliberately does not claim engine one-use request ownership.
 */
#ifdef NDEBUG
#error "Original player request copy proof fixture requires assertions"
#endif
#define main sg_existing_request_copy_fixture_main
#include "test_original_player0_request_44byte_poststore.c"
#undef main
#include <inttypes.h>
#include <stdlib.h>

static void emit_u8(const uint8_t *bytes, size_t n)
{
    putchar('[');
    for(size_t i=0;i<n;i++)
        printf("%s%" PRIu8,i?",":"",bytes[i]);
    putchar(']');
}
static void emit_u32(const uint32_t *words, size_t n)
{
    putchar('[');
    for(size_t i=0;i<n;i++)
        printf("%s%" PRIu32,i?",":"",words[i]);
    putchar(']');
}
static void emit(const Proof *p, const char *mode)
{
    printf("{\"bridge_schema\":\"sg-public-synthetic-request-copy-v1\",");
    printf("\"mode\":\"%s\",\"proof\":{",mode);
#define FIELD(name) printf("\"" #name "\":%" PRIu32 ",",p->name)
    FIELD(state);FIELD(error);FIELD(begin_frame);FIELD(end_frame);
    FIELD(entry_frame);FIELD(post_frame);FIELD(source);FIELD(dest);
    FIELD(actor);FIELD(direction);FIELD(length);FIELD(entry_sp);
    FIELD(entry_lr);FIELD(post_sp);FIELD(post_lr);FIELD(stores);
    FIELD(pending_entry);FIELD(pending_post);FIELD(opcode_post);
    FIELD(total_steps);FIELD(tag);
#undef FIELD
    printf("\"source_before\":");emit_u8(p->source_before,SRC_N);
    printf(",\"source_after\":");emit_u8(p->source_after,SRC_N);
    printf(",\"dest_after\":");emit_u8(p->dest_after,SRC_N);
    printf(",\"store_values\":");emit_u8(p->store_values,SRC_N);
    printf(",\"store_indices\":");emit_u32(p->store_indices,SRC_N);
    puts("}}");
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    static FakeCore m;
    Proof proof={0};
    uint32_t mode=0;
    const char *name=argv[1];
    if(strcmp(name,"valid")==0)mode=0;
    else if(strcmp(name,"skipped_store")==0)mode=1;
    else if(strcmp(name,"bad_opcode")==0)mode=2;
    else if(strcmp(name,"wrapped_buffer")==0)mode=3;
    else if(strcmp(name,"wrong_register")==0)mode=4;
    else if(strcmp(name,"frame_rollback")==0)mode=5;
    else if(strcmp(name,"short_budget")==0)mode=6;
    else if(strcmp(name,"missing_callback")==0)mode=7;
    else return 2;
    install(&m,mode);
    if(mode==2)m.ram[m.source-EWRAM_BASE]=18;
    if(mode==3)m.buffer=0x01FFFFF0u;
    if(mode==7)memset(m.abi+0x13e8,0,sizeof(void (*)(void *)));
    run(&m,&proof,2u,mode==6?1u:1000u);
    emit(&proof,name);
    return 0;
}
