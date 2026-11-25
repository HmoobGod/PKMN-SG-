/* Synthetic host memory only; never opens any game file. */
#define _GNU_SOURCE
#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <sys/mman.h>
int r7_native_capture_current44(uint32_t actor,uint8_t *out,uint32_t capacity);
#define W8(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define W16(a) (*(volatile uint16_t *)(uintptr_t)(a))
#define W32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define REQ 0x0201bf14u
static unsigned passed;
static void setup(void){
    memset((void *)(uintptr_t)0x02000000u,0,0x40000);
    memset((void *)(uintptr_t)0x03000000u,0,0x8000);
    W32(0x02001d2c)=3; W32(0x02001ab4)=4; W8(0x02001ab8)=2;
    W8(0x02001b59)=1; W8(0x030001a4)=1; W8(0x030001a5)=3;
    W32(0x03002e48)=0x080625f9; W32(0x03002e58)=0x080619d5;
    W32(0x03002e5c)=0x08060ac5; W32(0x02001c6c)=0x0201bf04;
    W8(REQ)=19;
    for(unsigned i=0;i<4;i++){
        W16(REQ+4+2*i)=(uint16_t)(100+i);
        W16(0x02001ecc+12+2*i)=(uint16_t)(100+i);
        W8(REQ+12+i)=W8(REQ+16+i)=W8(0x02001ecc+37+i)=10;
    }
    for(unsigned i=20;i<44;i++)W8(REQ+i)=(uint8_t)(i+33);
}
static void deny(unsigned actor,unsigned size){
    uint8_t b[44];memset(b,0xa5,sizeof b);
    assert(!r7_native_capture_current44(actor,b,size));
    for(unsigned i=0;i<44;i++)assert(b[i]==0xa5);
    passed++;
}
static void accept(void){
    uint8_t b[44];assert(r7_native_capture_current44(0,b,44));
    for(unsigned i=0;i<44;i++)assert(b[i]==W8(REQ+i));
    passed++;
}
int main(void){
    assert(mmap((void *)(uintptr_t)0x02000000u,0x40000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=(void *)MAP_FAILED);
    assert(mmap((void *)(uintptr_t)0x03000000u,0x8000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=(void *)MAP_FAILED);
    setup();accept(); W32(0x02001d2c)=1;accept();
    setup();deny(1,44);deny(2,44);deny(0,43);deny(0,45);
    assert(!r7_native_capture_current44(0,NULL,44));passed++;
    for(unsigned i=0;i<4;i++){setup();W8(REQ+i)^=1;deny(0,44);}
    for(unsigned i=4;i<16;i++){setup();W8(REQ+i)^=1;deny(0,44);}
    for(unsigned i=16;i<20;i++){setup();W8(REQ+i)=9;deny(0,44);}
    for(unsigned i=20;i<44;i++){setup();W8(REQ+i)^=1;accept();}
    for(unsigned i=0;i<4;i++){setup();W16(REQ+4+2*i)=936;W16(0x02001ecc+12+2*i)=936;deny(0,44);}
    setup();W16(REQ+4)=0;W16(0x02001ecc+12)=0;deny(0,44);
    W8(REQ+12)=W8(REQ+16)=W8(0x02001ecc+37)=0;accept();
    setup();W32(0x02001d2c)=0;deny(0,44);W32(0x02001d2c)=2;deny(0,44);W32(0x02001d2c)=5;deny(0,44);
    setup();W32(0x02001ab4)=13;deny(0,44);setup();W8(0x02001ab8)=4;deny(0,44);
    setup();W8(0x02001b58)=1;deny(0,44);setup();W8(0x02001b59)=0;deny(0,44);
    setup();W8(0x02001d42)=2;deny(0,44);setup();W8(0x030001a4)=3;deny(0,44);
    setup();W8(0x030001a5)=1;deny(0,44);setup();W32(0x03002e48)=0;deny(0,44);
    setup();W32(0x03002e58)=0;deny(0,44);setup();W32(0x03002e5c)=0;deny(0,44);
    setup();W32(0x02001c6c)=0x0201bf08;deny(0,44);
    printf("PASS: %u synthetic native-memory reader cases\n",passed);
    return 0;
}
