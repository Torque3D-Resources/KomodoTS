#!/usr/bin/env python

"""A Code Intelligence Language Engine for the TorqueScript language.

A "Language Engine" is responsible for scanning content of
its language and generating CIX output that represents an outline of
the code elements in that content. See the CIX (Code Intelligence XML)
format:
    http://community.activestate.com/faq/codeintel-cix-schema
    
Module Usage:
    from cile_torquescript import scan
    mtime = os.stat("bar.torquescript")[stat.ST_MTIME]
    content = open("bar.torquescript", "r").read()
    scan(content, "bar.torquescript", mtime=mtime)
"""

__version__ = "1.0.0"

import os
import sys
import time
import optparse
import logging
import pprint
import glob



from grammars import ytab, torque_lex, yconsts, astnodes
from grammars.astnodes import *

# Note: c*i*ElementTree is the codeintel system's slightly modified
# cElementTree. Use it exactly as you would the normal cElementTree API:
#   http://effbot.org/zone/element-index.htm
import ciElementTree as ET

from codeintel2.common import CILEError



#---- exceptions

class TorqueScriptCILEError(CILEError):
    pass



#---- global data

log = logging.getLogger("cile.torquescript")
log.setLevel(logging.DEBUG)
#---- public module interface

IMPORT_PACKAGE = 1
IMPORT_EXEC = 2
BASE_TYPE = "ConsoleVar"

EXPR_CLASS = {
        "ObjectDecl" : [ObjectDeclNode],
        "Variable" : [VarNode],
        "Assignment" : [SlotAssignOpNode, SlotAssignNode, AssignExprNode, AssignOpExprNode],
        "String" : [StrcatExprNode],
        #"Tag" : [TTagExprNode, TTagDerefNode], # It seems these are unused
        "Int" : [StreqExprNode, IntUnaryExprNode, IntBinaryExprNode],
        "Float" : [FloatUnaryExprNode, FloatBinaryExprNode],
        "Conditional" : [ConditionalExprNode],
        "Error" : [ExprNode,BinaryExprNode] ,# We should never get one of these that isn't a subclass of some sort
        "Constant" : [IntNode, FloatNode, StrConstNode, ConstantNode],
        "SlotAccess" : [SlotAccessNode,InternalSlotAccessNode],
        "Other" : [CommaCatExprNode, AssertCallExprNode, FuncCallExprNode],
        
        }

def test_elt_attrs(elt, **kwargs):
    return not sum(elt.get(attr) != val for attr,val in kwargs.iteritems())
    
def is_func(node, name):
    return isinstance(node, FuncCallExprNode) and node.func_name.lower() == name and not (node.call_type or node.namespace)

def add_var(elt, name, citdl=None, local=True, arg=False):
    if not citdl:
        citdl = BASE_TYPE
    return ET.SubElement(elt,"variable",name=name,citdl=citdl,attributes=("__local__" if local else ""),ilk=("argument" if arg else ""))

def add_function_args(func_elt, func_decl):
    for var in func_decl.args.stmts:
        if var.array_index_expr:
            pass
            #log.warn("--->Var %s has an array_index_expression, but it appears in a function header", var.var_name)
        #log.debug("--->Adding argument %s",var.var_name)
        arg = add_var(func_elt,var.var_name, citdl=func_decl.namespace, arg=True)
        
def handle_expr(statement, default_blob, script_root, local_namespace):    
    if is_func(statement, "activatepackage"):
        is_import = IMPORT_PACKAGE
    elif is_func(statement, "exec"):
        is_import = IMPORT_EXEC
    else:
        is_import = False
        #log.info("-->Evaluating expression for variable declarations and type inferencing")
                
    if is_import:
        #log.info("-->It's an %s-type import", ("exec" if is_import == IMPORT_EXEC else "package"))
        num_args = len(statement.args.stmts)
        if not num_args:
            #log.warn("--->With no arguments, skipping")
            pack_name_node = None
        elif num_args == 1:
            package_name_node, = statement.args.stmts
        elif is_import == IMPORT_EXEC and num_args > 1:
            package_name_node = statement.args.stmts[0]
        else:
            #log.warn("--->Something was wrong with it")
            package_name_node = None
                
        if not package_name_node:
            name_data = ""
        elif isinstance(package_name_node,(ConstantNode, StrConstNode)):
            name_data = package_name_node.value
        elif  isinstance(package_name_node,ExprNode):
            #log.warn("--->This is a programmatically generated import, let's skip it")
            name_name, name_data, name_type = handle_expr(package_name_node, default_blob, script_root, local_namespace)
            # this really needs to be processed more
        else:
            pass
            #log.warn("--->We have an import expression of unknown provenance")
        
        if name_data and is_import == IMPORT_EXEC:
            name_data = find_exec_file(name_data)
        
        if name_data:
            do_import = ET.SubElement(default_blob, "import", name=str(name_data), symbol="*")
        expr_name = ""
        expr_data = ""
        expr_types = [type_name for type_name in (BASE_TYPE,"IntType") if type_name == BASE_TYPE or is_import == IMPORT_EXEC]
    else:
        expr_name = ""
        expr_data = ""
        expr_types = [BASE_TYPE]
        if isinstance(statement, (AssignExprNode, AssignOpExprNode)):
            # it's a variable
            # handle assignment
            pass
        elif isinstance(statement, (SlotAssignNode, SlotAssignOpNode)):
            # it's an array
            # handle assignment
            pass
        #nv_name, expr_data 
    
    return (expr_name,expr_data," ".join(expr_types))
    
def find_exec_file(file_name):
    # this is a stub...
    return file_name

def extract_blob_data(ast, default_blob, script_root, local_namespace=None):
    # we know this is a statement list
    # that's all that yyparse will ever give us
    exports_symbols = False # Let's see what we find here
    # Assignment: 'AssignExprNode', 'AssignOpExprNode', SlotAssignNode','SlotAssignOpNode',
    # List: 'StmtList'
    # Recurse Tree: 'ReturnStmtNode', 'ExprNode'
    # 'FloatBinaryExprNode', 'FloatNode', 'FloatUnaryExprNode', 'FuncCallExprNode', 
    # Declaration: 'FunctionDeclStmtNode',ObjectDeclNode
    # Tricky: IfStmtNode, LoopStmtNode
    # Useless: 'BreakStmtNode','ContinueStmtNode',
    # Ignore: 'VarNode'
    # Dunno: InternalSlotAccessNode
    
    if not local_namespace:
        local_namespace = default_blob
    
    for statement in ast.stmts:
        if isinstance(statement, StmtList):
            extract_blob_data(statement, default_blob, script_root, local_namespace=local_namespace)

        # We need a better heuristic for who we might be doc'ing
        elif isinstance(statement, StrConstNode) and statement.doc:
            pass
        elif isinstance(statement, IfStmtNode):
            if statement.test_expr:
                handle_expr(statement.test_expr, default_blob, script_root, local_namespace)
            
        elif isinstance(statement, LoopStmtNode):
            pass
        elif isinstance(statement, FunctionDeclStmtNode):
            # declare function
            if statement.package_name:
                # add a new module or get an existing one
                lang = default_blob.get('lang')
                for parent_module in script_root.findall("./scope"):
                    if test_elt_attrs(parent_module, ilk="blob", lang=lang, name=statement.package_name):
                        break
                else:
                    parent_module = ET.SubElement(script_root,"scope",ilk="blob",lang=lang,name=statement.package_name)
            else:
                parent_module = default_blob
            if statement.namespace:
                # find the appropriate namespace, or add a new one
                for parent_elt in parent_module.findall("./scope"):
                    if test_elt_attrs(parent_elt, ilk="class", name=statement.namespace):
                        break
                else:
                    parent_elt = ET.SubElement(parent_module,"scope",ilk="class",name=statement.namespace)
            else:
                parent_elt = parent_module
                
            #log.debug("-->Declaring function: %s%s%s",
            #          ((statement.package_name + "::") if statement.package_name else ""),
            #          ((statement.namespace + "::") if statement.namespace else ""),
            #          statement.fn_name)
            new_function = ET.SubElement(parent_elt,"scope",ilk="function",name=statement.fn_name)
            add_function_args(new_function,statement)
            extract_blob_data(statement.stmts ,default_blob, script_root, local_namespace=new_function)
        elif isinstance(statement, ObjectDeclNode):
            # declare namespace
            pass
        # default behavior, this should be last, since many of the above are subclasses of ExprNode that we know how to handle better
        elif isinstance(statement, (ExprNode, ReturnStmtNode)):
            # recurse the tree for this expression, and extract any assignment expressions
            handle_expr((statement if isinstance(statement, ExprNode) else statement.expr),
                        default_blob, script_root, local_namespace)


def scan_buf(buf, mtime=None, lang="TorqueScript"):
    """Scan the given TorqueScriptBuffer return an ElementTree (conforming
    to the CIX schema) giving a summary of its code elements.
    
    @param buf {TorqueScriptBuffer} is the TorqueScript buffer to scan
    @param mtime {int} is a modified time for the file (in seconds since
        the "epoch"). If it is not specified the _current_ time is used.
        Note that the default is not to stat() the file and use that
        because the given content might not reflect the saved file state.
    """
    # Dev Notes:
    # - This stub implementation of the TorqueScript CILE return an "empty"
    #   summary for the given content, i.e. CIX content that says "there
    #   are no code elements in this TorqueScript content".
    # - Use the following command (in the extension source dir) to
    #   debug/test your scanner:
    #       codeintel scan -p -l TorqueScript <example-TorqueScript-file>
    #   "codeintel" is a script available in the Komodo SDK.
    #log.info("scan '%s'", buf.path)
    if mtime is None:
        mtime = int(time.time())

    # The 'path' attribute must use normalized dir separators.
    if sys.platform.startswith("win"):
        path = buf.path.replace('\\', '/')
    else:
        path = buf.path
        
    tree = ET.Element("codeintel", version="2.0",
                      xmlns="urn:activestate:cix:2.0")
    file_elt = ET.SubElement(tree, "file", lang=lang, mtime=str(mtime))
    blob = ET.SubElement(file_elt, "scope", ilk="blob", lang=lang,
                         name=os.path.basename(path))

    # Dev Note:
    # This is where you process the TorqueScript content and add CIX elements
    # to 'blob' as per the CIX schema (cix-2.0.rng). Use the
    # "buf.accessor" API (see class Accessor in codeintel2.accessor) to
    # analyze. For example:
    # - A token stream of the content is available via:
    #       buf.accessor.gen_tokens()
    #   Use the "codeintel html -b <example-TorqueScript-file>" command as
    #   a debugging tool.
    # - "buf.accessor.text" is the whole content of the file. If you have
    #   a separate tokenizer/scanner tool for TorqueScript content, you may
    #   want to use it.
    
    #log.info("Setting scan buffer")    
    
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    
    ytab.yy_clear_stacks()
    torque_lex.set_scan_buffer(buf.accessor.text, is_filename=False)
    try:
        #log.info("Attempting parse")
        successful_parse = not ytab.yyparse()
    except Exception:
        successful_parse = False
        import traceback
        traceback.print_exc(file=sys.stderr)
        traceback.print_tb(sys.exc_info()[2], file=sys.stderr)
    
    if successful_parse:
        #let's extract something here
        ts_ast = ytab.yyvs[1]
        #log.info("Extracting blob")
        extract_blob_data(ts_ast, blob, file_elt)
    else:
        file_elt.set("error","Error parsing file")
        
    sys.stdout = old_stdout
    
    return tree


