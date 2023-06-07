typedef struct mylist {
    char a[0x10];
    struct mylist* next;
}mylist;
int __entry_main_init(){
    mylist n;
    return 0;
}
// gcc -g -shared -fPIC -Wl,-e,__entry_main_init struct.c  -o structs.so
// or use objcopy