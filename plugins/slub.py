import gdb
import functools
from loguru import logger
from typing import (Callable, Any, Generator)


import squ.gdb.types as types
import squ.gdb.proc  as proc
import squ.utils.log as log

from squ.utils.color import Color as C
from squ.utils.decorator import handle_exception

from squ.gdb.kernel.cpu import per_cpu
import squ.gdb.kernel.macro as macro

R = C.redify
G = C.greenify
B = C.blueify

# temporary
def for_page_list(page_ptr : gdb.Value, typename: str) -> Generator["gdb.Value", None, None]:
    addr = page_ptr
    while addr != page_ptr and int(addr) != 0:
        yield macro.container_of(addr, typename, "next")
        addr = addr.dereference()["next"]

@handle_exception
def caches() -> Generator["KmemCache", None, None]:
    slab_caches = gdb.lookup_global_symbol("slab_caches").value()
    for slab_cache in macro.for_each_entry(slab_caches, "struct kmem_cache", "list"):
        yield KmemCache(slab_cache)

'''
            objs = [obj for obj in macro.traverse_freelist(freelist)]

            chain = C.blueify("->").join(list(
                map(lambda obj : C.greenify(hex(obj)), objs)
            ))
            print(chain)
'''


class KmemCacheCpu:
    '''
    struct kmem_cache_cpu {
        void **freelist;
        unsigned long tid;
        struct page *page;
        struct page *partial;
    }
    '''
    @handle_exception
    def __init__(self, cpu_slab : gdb.Value, name) -> None:
        assert cpu_slab.type == gdb.lookup_type("struct kmem_cache_cpu")
        self.__cpu_slab = cpu_slab
        self.name = name
    
    @handle_exception
    def available(self) -> int:
        '''
        return avaiable free'd objects in this slub pool
        '''
        page = self.__cpu_slab["page"]
        return int(page["objects"]) - int(page["inuse"])

    @property
    def freelist(self) -> gdb.Value:
        return self.__cpu_slab["freelist"]
    
    @property
    def partial(self) -> gdb.Value:
        return self.__cpu_slab["partial"]

    @handle_exception
    def show_partial(self) -> None:

        if int(self.partial) == 0:
            return
         
        # log.dbg("partial at " + hex(self.partial))
        for page in macro.for_each_entry_no_head(self.partial, "struct page", "next"):
            
            # log.dbg("page at " + hex(page))
            # log.dbg("name = " + self.name)
            available = int(page["objects"]) - int(page["inuse"])
            if available > 0:
                freelist = page["freelist"]
                print(G("    cpu partial slab freelist : ") + B(hex(freelist)))

'''
(gdb) ptype struct kmem_cache
type = struct kmem_cache {
    struct kmem_cache_cpu *cpu_slab;
    slab_flags_t flags;
    unsigned long min_partial;
    unsigned int size;
    unsigned int object_size;
    struct reciprocal_value reciprocal_size;
    unsigned int offset;
    unsigned int cpu_partial;
    ···
    unsigned int inuse;
    ···
    const char *name;
    struct list_head list;
    struct kobject kobj;
    unsigned int remote_node_defrag_ratio;
    unsigned int useroffset;
    unsigned int usersize;
    struct kmem_cache_node *node[64];
}
'''

class KmemCache:
    @handle_exception
    def __init__(self, slub_cache : gdb.Value) -> None:
        assert slub_cache.type == gdb.lookup_type("struct kmem_cache").pointer()
        self.__slub_cache = slub_cache

    @property
    def addr(self) -> int:
        return self.__slub_cache.cast(types.u64)

    # @property
    # def inuse(self) -> int:
    #     return int(self.__slub_cache["inuse"])

    @property
    def object_size(self) -> int:
        return int(self.__slub_cache["object_size"])
    
    @property
    def cpu_slab(self) -> KmemCacheCpu:
        '''
        return `struct kmem_cache_cpu` type field(convert to real addr by percpu)
        '''
        return KmemCacheCpu(per_cpu(self.__slub_cache["cpu_slab"]), self.name) # ptr deref
    
    @property
    def name(self) -> str:
        return self.__slub_cache["name"].string()


class Slub(gdb.Command):
    def __init__(self):
        super().__init__("slub", gdb.COMMAND_USER)

    @proc.only_if_running
    @handle_exception
    def show_cpu_slab(self, slub_cache : KmemCache) -> None:
        '''
        show cpu direct freelist and partial freelist if any available object exist


        {
            freelist = 0xffff888003cecf00,
            tid = 128,
            page = 0xffffea00000f3b00,
            partial = 0x0 <fixed_percpu_data>
        }
        '''

        cpu_slab = slub_cache.cpu_slab
        freelist = cpu_slab.freelist
        
        if cpu_slab.available():
            tail = hex(freelist)
        else :
            tail = "full"
        
        print(G("  cpu direct slab freelist : ") + B(tail))
        cpu_slab.show_partial()
            

    @proc.only_if_running
    @handle_exception
    def invoke(self, arg, from_tty):
        c : KmemCache = None

        for c in caches():
            # TODO: all name 
            if c.name.startswith("kmalloc") and "rcl" not in c.name:
                if c.object_size < 1024:
                    print(R(c.name + " : "))
                    self.show_cpu_slab(c)
        
Slub()