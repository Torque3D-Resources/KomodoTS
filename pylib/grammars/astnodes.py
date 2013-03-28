#!python
#enum TypeReq
#{
#   TypeReqNone,
#   TypeReqUInt,
#   TypeReqFloat,
#   TypeReqString
#};

#Representation of a node for the scripting language parser.
#
#When the scripting language is evaluated, it is turned from a string representation,
#into a parse tree, thence into byte code, which is ultimately interpreted by the VM.
#
#This is the base class for the nodes in the parse tree. There are a great many subclasses,
#each representing a different language construct.

from yconsts import *

class StmtNode(object):
	def __init__(self):
		self.dbg_file_name = ""
		self.dbg_line_number = ""
		#self.dbg_stmt_type = ""
		
		self.dbg_stmt_type = self.__class__.__name__
		self.package_name = ""
		
	def set_package(self,new_package_name):
		pass
		
	def add_break_count(self):
		pass
	
	def add_break_line(self, ip):
		pass

	def precompile_stmt(self, loopcount):
		pass
	
	def compile_stmt(self, code_stream, ip, continue_point, break_point):
		pass
	
	def describe_self(self):
		return "%d;{%s}" % (id(self),", ".join(["%s : %s" % (repr(name), repr(value))
									for name, value in self.__dict__.iteritems()
									if not callable(value) and not isinstance(value,StmtNode) and value != "" ]))
		
	
	def find_child_nodes(self):
		return [value for value in self.__dict__.itervalues() if isinstance(value,StmtNode)]
		
	def build_tree_list(self):
		return [self.describe_self(), [child.build_tree_list() for child in self.find_child_nodes()]]
	
class StmtList(StmtNode):
	# This is not defined by astnodes.h, but it makes our dynamism work a bit better
	def __init__(self, *args):
		StmtNode.__init__(self)
		self.stmts = list(args)
		
	def append(self, stmt):
		self.stmts.append(stmt)
		
	def find_child_nodes(self):
		return self.stmts
		
	def describe_self(self):
		return "%d;{%s}" % (id(self),", ".join(["%s : %s" % (repr(name), repr(value))
									for name, value in self.__dict__.iteritems()
									if not callable(value) and not isinstance(value,StmtNode) and value != "" and value is not self.stmts]))
	
		
class BreakStmtNode(StmtNode):
	pass
class ContinueStmtNode(StmtNode):
	pass
class ExprNode(StmtNode):
	pass

class ReturnStmtNode(StmtNode):
	def __init__(self, expr):
		StmtNode.__init__(self)
		self.expr = expr


class IfStmtNode(StmtNode):
	def __init__(self, line_number, test_expr, if_block, else_block, propagate_through):
		StmtNode.__init__(self)
		self.line_number = line_number
		self.test_expr = test_expr
		self.if_block = if_block
		self.else_block = else_block
		self.propagate = propagate_through
		self.integer = False
		self.end_if_offset = 0
		self.else_offset = 0
		
	def find_child_nodes(self):
		if self.if_block:
			ib = [self.if_block]
		else:
			ib = []
			
		if self.else_block:
			eb = [self.else_block]
		else:
			eb = []
			
		if self.test_expr:
			return [self.test_expr] + ib + eb
		else:
			return ib + eb
		
	def propagate_switch_expr(self, left, string):
		self.test_expr = self.get_switch_OR(left, self.test_expr, string);
		if self.propagate and self.else_block:
			self.else_block.propagate_switch_expr(left, string);
			
	def get_switch_OR(self, left, expr_list, string):
		next_expr = StmtList()
		next_expr.stmts = expr_list.stmts[1:]
		if string:
			test = StreqExprNode(left, expr_list, True)
		else:
			test = IntBinaryExprNode(opEQ, left, expr_list)
		
		if len(expr_list.stmts) == 1:
			return test
		else:
			return IntBinaryExprNode(opOR, test, self.get_switch_OR(left, next_expr, string))


class LoopStmtNode(StmtNode):
	def __init__(self, line_number, test_expr, init_expr, end_loop_expr, loop_block, is_do_loop):
		StmtNode.__init__(self)
		self.line_number = line_number
		self.test_expr = [IntNode(1), test_expr][int(bool(test_expr))] # silly backwards compatibility hack for old Komodos with old Pythons
		self.init_expr = init_expr
		self.end_loop_expr = end_loop_expr
		self.loop_block = loop_block
		self.is_do_loop = is_do_loop
		self.break_offset = 0
		self.continue_offset = 0
		self.loop_block_offset = 0
		self.integer = False

class BinaryExprNode(ExprNode):
	def __init__(self):
		ExprNode.__init__(self)
		self.op = 0
		self.left = None
		self.right = None
		
class IntBinaryExprNode(BinaryExprNode):
	def __init__(self,op,left,right):
		BinaryExprNode.__init__(self)
		self.op = op
		self.left = left
		self.right = right
		
class FloatBinaryExprNode(BinaryExprNode):
	def __init__(self,op,left,right):
		BinaryExprNode.__init__(self)
		self.op = op
		self.left = left
		self.right = right
		
class StreqExprNode(BinaryExprNode):
	def __init__(self, left, right, eq):
		BinaryExprNode.__init__(self)
		self.left = left
		self.right = right
		self.eq = eq
		
class StrcatExprNode(BinaryExprNode):
	def __init__(self, left, right, append_char):
		BinaryExprNode.__init__(self)
		self.left = left
		self.right = right
		self.append_char = append_char
		
class CommaCatExprNode(BinaryExprNode):
	def __init__(self, left, right):
		BinaryExprNode.__init__(self)
		self.left = left
		self.right = right

class ConditionalExprNode(ExprNode):
	def __init__(self, test_expr, true_expr, false_expr):
		ExprNode.__init__(self)
		self.test_expr = test_expr
		self.true_expr = true_expr
		self.false_expr = false_expr
		self.integer = False

class IntUnaryExprNode(ExprNode):
	def __init__(self, op, expr):
		ExprNode.__init__(self)
		self.op = op
		self.expr = expr
		self.integer = False

class FloatUnaryExprNode(ExprNode):
	def __init__(self, op, expr):
		ExprNode.__init__(self)
		self.op = op
		self.expr = expr
		self.integer = False

class VarNode(ExprNode):
	def __init__(self, var_name, array_index_expr):
		ExprNode.__init__(self)
		self.var_name = var_name
		self.array_index_expr = array_index_expr

class ConstantNode(ExprNode):
	def __init__(self, value):
		ExprNode.__init__(self)
		self.value = value
		self.float_val = float('nan')
		self.index = -1	
	
class IntNode(ConstantNode):
	def __init__(self, value):
		ConstantNode.__init__(self, value)
		self.float_val = float(value)
	
class FloatNode(ConstantNode):
	def __init__(self, value):
		ConstantNode.__init__(self, value)
		self.float_val = value

class StrConstNode(ConstantNode):
	def __init__(self, value, tag, doc=False):
		ConstantNode.__init__(self,value)
		self.tag = tag
		self.doc = doc

class AssignExprNode(ExprNode):
	def __init__(self, var_name, array_index_expr, expr):
		ExprNode.__init__(self)
		self.var_name = var_name
		self.array_index_expr = array_index_expr
		self.expr = expr
		
class AssignDecl(object):
	def __init__(self,token,expr,integer=False):
		self.token = token
		self.expr = expr
		self.integer = integer

class AssignOpExprNode(ExprNode):
	def __init__(self, var_name, array_index_expr, expr, op):
		ExprNode.__init__(self)
		self.var_name = var_name
		self.array_index_expr = array_index_expr
		self.expr = expr
		self.op = op
		self.operand = 0;
		
class TTagSetStmtNode(StmtNode):
	def __init__(self, tag, value_expr, string_expr):
		StmtNode.__init__(self)
		self.tag = tag
		self.value_expr = value_expr
		self.string_expr = string_expr
		
class TTagDerefNode(ExprNode):
	def __init__(self, expr):
		ExprNode.__init__(self)
		self.expr = expr
		
class TTagExprNode(ExprNode):
	def __init__(self, tag):
		ExprNode.__init__(self)
		self.tag = tag

class FuncCallExprNode(ExprNode):
	FunctionCall = 0
	MethodCall = 1
	ParentCall = 2
	def __init__(self, func_name, namespace, args, dot):
		ExprNode.__init__(self)
		self.func_name = func_name
		self.namespace = namespace
		self.args = args
		if dot:
			self.call_type = FuncCallExprNode.MethodCall
		elif namespace and namespace.lower() == "parent":
			self.call_type = FuncCallExprNode.ParentCall
		else:
			self.call_type = FuncCallExprNode.FunctionCall

class AssertCallExprNode(ExprNode):
	def __init__(self, test_expr, message="Torquescript Assert!"):
		ExprNode.__init__(self)
		self.test_expr = test_expr
		self.message = message
		self.message_index = 0
		

class SlotDecl(object):
	def __init__(self, object_expr, slot_name, array):
		self.object_expr = object_expr
		self.slot_name = slot_name
		self.array = array


class SlotAccessNode(ExprNode):
	def __init__(self, object_expr, array_expr, slot_name):
		ExprNode.__init__(self)
		self.object_expr = object_expr
		self.array_expr = array_expr
		self.slot_name = slot_name
		


class InternalSlotDecl(object):
	def __init__(self, object_expr, slot_expr, recurse):
		self.object_expr = object_expr
		self.slot_expr = slot_expr
		self.recurse = recurse

class InternalSlotAccessNode(ExprNode):
	def __init__(self, object_expr, slot_expr, recurse):
		ExprNode.__init__(self)
		self.object_expr = object_expr
		self.slot_expr = slot_expr
		self.recurse = recurse

class SlotAssignNode(ExprNode):
	def __init__(self, object_expr, array_expr, slot_name, value_expr, type_id=-1):
		ExprNode.__init__(self)
		self.object_expr = object_expr
		self.array_expr = array_expr
		self.slot_name = slot_name
		self.value_expr = value_expr
		self.type_id = type_id

class SlotAssignOpNode(ExprNode):
	def __init__(self, object_expr, slot_name, array_expr, op, value_expr):
		ExprNode.__init__(self)
		self.object_expr = object_expr
		self.array_expr = array_expr
		self.slot_name = slot_name
		self.value_expr = value_expr
		self.op = op
		
class ObjectBlockDecl(object):
	def __init__(self, slots, decls):
		self.slots = slots
		self.decls = decls
		
class ObjectDeclNode(ExprNode):
	def __init__(self, class_name_expr, object_name_expr, arg_list, parent_object, slot_decls, sub_objects, is_datablock, class_name_internal, is_singleton):
		ExprNode.__init__(self)
		self.class_name_expr = class_name_expr
		self.object_name_expr = object_name_expr
		self.arg_list = arg_list
		self.slot_decls = slot_decls
		self.sub_objects = sub_objects
		self.is_datablock = is_datablock
		self.is_class_name_internal = class_name_internal
		self.is_singleton = is_singleton
		self.fail_offset = 0;
		if(parent_object):
			self.parent_object = parent_object;
		else:
			self.parent_object = ""


class FunctionDeclStmtNode(StmtNode):
	def __init__(self, fn_name, namespace, args, stmts):
		StmtNode.__init__(self)
		#if not args:
		#	args = []
		#if not stmts:
		#	stmts = []
		self.fn_name = fn_name
		self.namespace = namespace
		self.package = ""
		self.args = args
		self.stmts = stmts
		self.end_offset = 0
		self.argc = len(args.stmts)
		
	def set_package(self,new_package_name):
		self.package_name = new_package_name



def write_dotlines(handle, tree):
	root_name, children = tree
	for child in children:
		handle.write("\"%s\" -> \"%s\";\n" % (repr(root_name)[1:-1], repr(child[0])[1:-1] ))
		write_dotlines(handle, child)

def write_dotfile(path, tree):
	handle = open(path,'w')
	handle.write("""digraph G {
rankdir=LR
""")
	
	write_dotlines(handle, tree)
	handle.write("""}
""")
	handle.close()