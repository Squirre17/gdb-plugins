import gdb
import functools
from typing import Callable, Any


import squ.gdb.types as types
import squ.gdb.proc  as proc
import squ.utils.log as log

from squ.utils.color import Color
from squ.utils.decorator import handle_exception



class DereferLinkedList(gdb.Command):
    def __init__(self):
        super().__init__("dll", gdb.COMMAND_USER)

    node_ptr_type = "mylist"
    tag           = "next"

    @proc.only_if_running
    @handle_exception
    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            log.err("Usage: dll <address> [struct name] [next tag] [max depth]")
            return

        # memorize struct name and tag
        try:
            ptr_type = args[1]
            self.node_ptr_type = ptr_type
            tag = args[2]
            self.tag = tag
            md = args[3]
            try:
                self.max_depth = int(md)
            except ValueError:
                self.max_depth = int(md, 16)
            except Exception as e:
                raise e
        except IndexError:
            pass

        struct_ptr = args[0]
        ptr_val = gdb.parse_and_eval(struct_ptr)

        ptr_of_type = gdb.lookup_type(self.node_ptr_type).pointer()
        node_ptr = gdb.Value(int(ptr_val)).cast(ptr_of_type)
        idx = 0
        while node_ptr:
            print(Color.blueify(f"[{idx}] "), end="")
            print(node_ptr.dereference())
            # node_ptr = node_ptr.cast(ptr_of_type)
            node_ptr = node_ptr[self.tag]            # Replace with your node tag
            node_ptr = node_ptr.cast(ptr_of_type)
            idx += 1
            if idx > self.max_depth:
                break

DereferLinkedList()