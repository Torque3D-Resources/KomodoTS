%{
 /* Reserved Word Definitions */
import astnodes
from astnodes import *
import torque_lex
from torque_lex import yylex
debug = 0                
        
%}
%token rwDEFINE rwENDDEF rwDECLARE rwDECLARESINGLETON
%token rwBREAK rwELSE rwCONTINUE rwGLOBAL
%token rwIF rwNIL rwRETURN rwWHILE rwDO
%token rwENDIF rwENDWHILE rwENDFOR rwDEFAULT
%token rwFOR rwDATABLOCK rwSWITCH rwCASE rwSWITCHSTR
%token rwCASEOR rwPACKAGE rwNAMESPACE rwCLASS
%token rwASSERT
%token ILLEGAL_TOKEN
%{
 /* Constants and Identifier Definitions */
%}
%token CHRCONST
%token INTCONST
%token TTAG
%token VAR
%token IDENT
%token TYPE
%token DOCBLOCK
%token STRATOM
%token TAGATOM
%token FLTCONST

%{
 /* Operator Definitions */
%}
%token '+' '-' '*' '/' '<' '>' '=' '.' '|' '&' '%'
%token '(' ')' ',' ':' ';' '{' '}' '^' '~' '!' '@'
%token opINTNAME opINTNAMER
%token opMINUSMINUS opPLUSPLUS
%token STMT_SEP
%token opSHL opSHR opPLASN opMIASN opMLASN opDVASN opMODASN opANDASN
%token opXORASN opORASN opSLASN opSRASN opCAT
%token opEQ opNE opGE opLE opAND opOR opSTREQ
%token opCOLONCOLON

%left '['
%right opMODASN opANDASN opXORASN opPLASN opMIASN opMLASN opDVASN opMDASN opNDASN opNTASN opORASN opSLASN opSRASN '='
%left '?' ':'
%left opOR
%left opAND
%left '|'
%left '^'
%left '&'
%left opEQ opNE
%left '<' opLE '>' opGE
%left '@' opCAT opSTREQ opSTRNE
%left opSHL opSHR
%left '+' '-'
%left '*' '/' '%'
%right '!' '~' opPLUSPLUS opMINUSMINUS UNARY
%left '.'
%left opINTNAME opINTNAMER

%%

start:
decl_list {
        $$ = ($1)#.build_tree_list()
        #$$[0] = "%s: %s" % (torque_lex.get_current_file(), $$[0])
};

decl_list:
{
        $$ = StmtList()
} | decl_list decl {
        ($1).append($2)
        $$ = $1
};

decl:
error {
        $$ = ExprNode()
        $$.illegal_expr = $1
} | stmt {
        $$ = $1
} | fn_decl_stmt{
        $$ = $1
} | package_decl
{
        $$ = $1;
};

package_decl:
rwPACKAGE IDENT '{' fn_decl_list '}' ';' {
        $$ = $4
        for walk in ($4).stmts:
                walk.set_package($2)
};

fn_decl_list:
fn_decl_stmt {
        $$ = StmtList($1)
} | fn_decl_list fn_decl_stmt {
        $$ = $1
        ($1).append($2)
};

statement_list:
{
        $$ = StmtList()
} | statement_list stmt {
        ($1).append($2)
        $$ = $1;
};

stmt:
if_stmt
  | while_stmt
  | for_stmt
  | datablock_decl
  | switch_stmt
  | rwBREAK ';' {
        $$ = BreakStmtNode()
} | rwCONTINUE ';' {
        $$ = ContinueStmtNode()
} | rwRETURN ';' {
        $$ = ReturnStmtNode(None)
} | rwRETURN expr ';' {
        $$ = ReturnStmtNode($2)
} | expression_stmt ';' {
        $$ = $1;
} | TTAG '=' expr ';' {
        $$ = TTagSetStmtNode($1, $3, None)
} | TTAG '=' expr ',' expr ';' {
        $$ = TTagSetStmtNode($1, $3, $5)
} | DOCBLOCK {
        $$ = StrConstNode($1, False, True)
};

fn_decl_stmt:
rwDEFINE IDENT '(' var_list_decl ')' '{' statement_list '}' {
        $$ = FunctionDeclStmtNode($2, None, $4, $7)
} | rwDEFINE IDENT opCOLONCOLON IDENT '(' var_list_decl ')' '{' statement_list '}' {
        $$ = FunctionDeclStmtNode($4, $2, $6, $9)
};

var_list_decl:
{
        $$ = StmtList()
} | var_list {
        $$ = $1
};

var_list:
VAR {
        $$ = StmtList(VarNode($1,None))
} | var_list ',' VAR{
        $$ = $1
        ($1).append(VarNode($3, None))
};

datablock_decl:
rwDATABLOCK IDENT '(' IDENT parent_block ')'  '{' slot_assign_list '}' ';' {
        $$ = ObjectDeclNode(ConstantNode($2), ConstantNode($4), None, $5, $8, None, True, False, False)
};

object_decl:
rwDECLARE class_name_expr '(' object_name parent_block object_args ')' '{' object_declare_block '}'{
        $$ = ObjectDeclNode($2, $4, $6, $5, $9.slots, $9.decls, False, False, False)
} | rwDECLARE class_name_expr '(' object_name parent_block object_args ')' {
        $$ = ObjectDeclNode($2, $4, $6, $5, None, None, False, False, False)
} | rwDECLARE class_name_expr '(' '[' object_name ']' parent_block object_args ')' '{' object_declare_block '}' {
        $$ = ObjectDeclNode($2, $5, $8, $7, $11.slots, $11.decls, False, True, False)
} | rwDECLARE class_name_expr '(' '[' object_name ']' parent_block object_args ')' {
        $$ = ObjectDeclNode($2, $5, $8, $7, None, None, False, True, False)
}   | rwDECLARESINGLETON class_name_expr '(' object_name parent_block object_args ')' '{' object_declare_block '}' {
        $$ = ObjectDeclNode($2, $4, $6, $5, $9.slots, $9.decls, False, False, True)
} | rwDECLARESINGLETON class_name_expr '(' object_name parent_block object_args ')' {
        $$ = ObjectDeclNode($2, $4, $6, $5, None, None, False, False, True)
};

parent_block:
{
        $$ = None
} | ':' IDENT{
        $$ = $2
};

object_name:
{
        $$ = StrConstNode("", False)
} | expr {
        $$ = $1
};

object_args:
{
        $$ = None
} | ',' expr_list {
        $$ = $2
};

object_declare_block:
{
        $$ = ObjectBlockDecl(None, None)
} | slot_assign_list {
        $$ = ObjectBlockDecl($1, None)
}| object_decl_list {
        $$ = ObjectBlockDecl(None, $1)
} | slot_assign_list object_decl_list {
        $$ = ObjectBlockDecl($1, $2)
};

object_decl_list:
object_decl ';' {
        $$ = StmtList($1)
} | object_decl_list object_decl ';' {
        ($1).append($2)
        $$ = $1
};

stmt_block:
'{' statement_list '}' {
        $$ = $2;
} | stmt {
        $$ = $1
};

switch_stmt: rwSWITCH '(' expr ')' '{' case_block '}' {
        $$ = $6
        ($6).propagate_switch_expr($3, False)
} | rwSWITCHSTR '(' expr ')' '{' case_block '}' {
        $$ = $6
        ($6).propagate_switch_expr($3, True)
};

case_block:
rwCASE case_expr ':' statement_list {
        $$ = IfStmtNode($1, $2, $4, None, False)
} | rwCASE case_expr ':' statement_list rwDEFAULT ':' statement_list {
        $$ = IfStmtNode($1, $2, $4, $7, False);
} | rwCASE case_expr ':' statement_list case_block {
        $$ = IfStmtNode($1, $2, $4, $5, True)
};

case_expr:
expr {
        $$ = StmtList($1)
} | case_expr rwCASEOR expr {
        ($1).append($3)
        $$=$1
};

if_stmt:
rwIF '(' expr ')' stmt_block{
        $$ = IfStmtNode($1, $3, $5, None, False)
} | rwIF '(' expr ')' stmt_block rwELSE stmt_block {
        $$ = IfStmtNode($1, $3, $5, $7, False)
};

while_stmt:
rwWHILE '(' expr ')' stmt_block {
        $$ = LoopStmtNode($1, None, $3, None, $5, False)
} | rwDO stmt_block rwWHILE '(' expr ')' {
        $$ = LoopStmtNode($3, None, $5, None, $2, True)
};

for_stmt:
rwFOR '(' expr ';' expr ';' expr ')' stmt_block {
        $$ = LoopStmtNode($1, $3, $5, $7, $9, False) 
} | rwFOR '(' expr ';' expr ';'      ')' stmt_block {
        $$ = LoopStmtNode($1, $3, $5, None, $8, False)
} | rwFOR '(' expr ';'      ';' expr ')' stmt_block {
        $$ = LoopStmtNode($1, $3, None, $6, $8, False)
} | rwFOR '(' expr ';'      ';'      ')' stmt_block {
        $$ = LoopStmtNode($1, $3, None, None, $7, False)
} | rwFOR '('      ';' expr ';' expr ')' stmt_block {
        $$ = LoopStmtNode($1, None, $4, $6, $8, False)
} | rwFOR '('      ';' expr ';'      ')' stmt_block {
        $$ = LoopStmtNode($1, None, $4, None, $7, False) 
} | rwFOR '('      ';'      ';' expr ')' stmt_block {
        $$ = LoopStmtNode($1, None, None, $5, $7, False)
} | rwFOR '('      ';'      ';'      ')' stmt_block {
        $$ = LoopStmtNode($1, None, None, None, $6, False)
};

expression_stmt:
stmt_expr {
        $$ = $1
};

expr:
stmt_expr {
        $$ = $1
} | '(' expr ')' {
        $$ = $2
} | expr '^' expr {
        $$ = IntBinaryExprNode($2, $1, $3)
} | expr '%' expr {
        $$ = IntBinaryExprNode($2, $1, $3)
} | expr '&' expr {
        $$ = IntBinaryExprNode($2, $1, $3)
} | expr '|' expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr '+' expr {
      $$ = FloatBinaryExprNode($2, $1, $3)
} | expr '-' expr {
      $$ = FloatBinaryExprNode($2, $1, $3)
} | expr '*' expr {
      $$ = FloatBinaryExprNode($2, $1, $3)
} | expr '/' expr {
      $$ = FloatBinaryExprNode($2, $1, $3)
} | '-' expr  %prec UNARY {
      $$ = FloatUnaryExprNode($1, $2)
} | '*' expr %prec UNARY {
      $$ = TTagDerefNode($2)
} | TTAG {
      $$ = TTagExprNode($1)
} | expr '?' expr ':' expr {
      $$ = ConditionalExprNode($1, $3, $5)
} | expr '<' expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr '>' expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opGE expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opLE expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opEQ expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opNE expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opOR expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opSHL expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opSHR expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opAND expr {
      $$ = IntBinaryExprNode($2, $1, $3)
} | expr opSTREQ expr {
      $$ = StreqExprNode($1, $3, True)
} | expr opSTRNE expr {
      $$ = StreqExprNode($1, $3, False)
} | expr opCAT expr {
      $$ = StrcatExprNode($1, $3, $2)
} | '!' expr {
      $$ = IntUnaryExprNode($1, $2)
} | '~' expr {
      $$ = IntUnaryExprNode($1, $2)
} | TAGATOM {
      $$ = StrConstNode($1, True)
} | FLTCONST {
      $$ = FloatNode($1)
} | INTCONST {
      $$ = IntNode($1)
} | rwBREAK {
      $$ = ConstantNode("break")
} | slot_acc {
      $$ = SlotAccessNode($1.object_expr, $1.array, $1.slot_name)
} | intslot_acc {
      $$ = InternalSlotAccessNode($1.object_expr, $1.slot_expr, $1.recurse)
} | IDENT {
      $$ = ConstantNode($1)
} | STRATOM {
      $$ = StrConstNode($1, False)
} | VAR {
      $$ = VarNode($1, None)
} | VAR '[' aidx_expr ']' {
      $$ = VarNode($1, $3)
} | illegal_token_list {
      YYERROR()
};

slot_acc:
expr '.' IDENT {
        $$ = SlotDecl($1, $3, None) 
} | expr '.' IDENT '[' aidx_expr ']' {
        $$ = SlotDecl($1, $3, $5)
};

intslot_acc:
expr opINTNAME class_name_expr {
        $$ = InternalSlotDecl($1, $3, False)
} | expr opINTNAMER class_name_expr {
        $$ = InternalSlotDecl($1, $3, True)
};

class_name_expr:
IDENT {
        $$ = ConstantNode($1)
} | '(' expr ')' {
        $$ = $2
};

assign_op_struct:
opPLUSPLUS{
        $$ = AssignDecl('+', FloatNode(1))
} | opMINUSMINUS {
        $$ = AssignDecl('-', FloatNode(1))
} | opPLASN expr {
        $$ = AssignDecl('+', $2)
} | opMIASN expr {
        $$ = AssignDecl('-', $2)
} | opMLASN expr {
        $$ = AssignDecl('*', $2)
} | opDVASN expr {
        $$ = AssignDecl('/', $2)
} | opMODASN expr {
        $$ = AssignDecl('%', $2)
} | opANDASN expr {
        $$ = AssignDecl('&', $2)
} | opXORASN expr {
        $$ = AssignDecl('^', $2)
} | opORASN expr {
        $$ = AssignDecl('|', $2)
} | opSLASN expr {
        $$ = AssignDecl(opSHL, $2)
} | opSRASN expr {
        $$ = AssignDecl(opSHR, $2)
};

stmt_expr:
funcall_expr {
        $$ = $1
} | assert_expr {
        $$ = $1
} | object_decl {
        $$ = $1
} | VAR '=' expr {
        $$ = AssignExprNode($1, None, $3)
} | VAR '[' aidx_expr ']' '=' expr {
        $$ = AssignExprNode($1, $3, $6)
} | VAR assign_op_struct {
        $$ = AssignOpExprNode($1, None, $2.expr, $2.token)
} | VAR '[' aidx_expr ']' assign_op_struct {
        $$ = AssignOpExprNode($1, $3, $5.expr, $5.token)
} | slot_acc assign_op_struct {
        $$ = SlotAssignOpNode($1.object_expr, $1.slot_name, $1.array, $2.token, $2.expr)
} | slot_acc '=' expr {
        $$ = SlotAssignNode($1.object_expr, $1.array, $1.slot_name, $3)
} | slot_acc '=' '{' expr_list '}' {
        $$ = SlotAssignNode($1.object_expr, $1.array, $1.slot_naame, $4)
};

funcall_expr:
IDENT '(' expr_list_decl ')' {
        $$ = FuncCallExprNode($1, None, $3, False)
} | IDENT opCOLONCOLON IDENT '(' expr_list_decl ')' {
        $$ = FuncCallExprNode($3, $1, $5, False)
} | expr '.' IDENT '(' expr_list_decl ')' {
        stmt_list = StmtList($1, $5)
        $$ = FuncCallExprNode($3, None, stmt_list, True);
};

assert_expr:
rwASSERT '(' expr ')' {
        $$ = AssertCallExprNode( $3, None )
} | rwASSERT '(' expr ',' STRATOM ')' {
        $$ = AssertCallExprNode( $3, $5 )
};
                  
expr_list_decl:
{
        $$ = StmtList()
} | expr_list
{
        $$ = $1
};

expr_list:
expr {
        $$ = StmtList($1)
} | expr_list ',' expr {
        ($1).append($3)
        $$ = $1
};

slot_assign_list:
slot_assign {
        $$ = StmtList($1)
} | slot_assign_list slot_assign{
        ($1).append($2)
        $$ = $1
};

slot_assign:
IDENT '=' expr ';' {
        $$ = SlotAssignNode(None, None, $1, $3)
} | TYPE IDENT '=' expr ';' {
        $$ = SlotAssignNode(None, None, $2, $4, $1)
} | rwDATABLOCK '=' expr ';' {
        $$ = SlotAssignNode(None, None, "datablock", $3)
} | IDENT '[' aidx_expr ']' '=' expr ';' {
        $$ = SlotAssignNode(None, $3, $1, $6)
} | TYPE IDENT '[' aidx_expr ']' '=' expr ';' {
        $$ = SlotAssignNode(None, $4, $2, $7, $1)
};

aidx_expr:
expr {
        $$ = $1
} | aidx_expr ',' expr {
        $$ = CommaCatExprNode($1, $3)
};

illegal_token_list:
ILLEGAL_TOKEN {
        ill_tok = ExprNode()
        ill_tok.token = $1
        $$ = StmtList(ill_tok)
} illegal_token_list ILLEGAL_TOKEN {
        ill_tok = ExprNode()
        ill_tok.token = $2
        ($1).append(ill_tok)
        $$ = $1
};

%%

