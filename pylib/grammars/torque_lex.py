#!python


from Plex import *
from Plex.Traditional import re
from cStringIO import StringIO
from yconsts import *

#// Hack to make windows lex happy.
##ifndef isatty
#inline int isatty(int) { return 0; }
##endif

#// Wrap our getc, so that lex doesn't try to do its own buffering/file IO.
##define YY_INPUT(buf,result,max_size) \
#   { \
#      int c = '*', n; \
#      for ( n = 0; n < max_size && \
#            (c = CMDgetc()) != EOF && c != '\n'; ++n ) \
#         buf[n] = (char) c; \
#      if ( c == '\n' ) \
#         buf[n++] = (char) c; \
#      result = n; \
#   }
#
#def yy_input(buf, result, max_size)
#
#// General helper stuff.
#static int lineIndex;
#
#// File state
#void CMDSetScanBuffer(const char *sb, const char *fn);
#const char * CMDgetFileLine(int &lineNumber);
#
#// Error reporting
#void CMDerror(char * s, ...);
#
#// Reset the parser.
#void CMDrestart(FILE *in);
#
#%}
def scan_doc_block(scanner, text):
	return (DOCBLOCK, text[3:].strip())

def scan_string_atom(scanner, text):
	return (STRATOM, text[1:-1])
	
def scan_tag_atom(scanner, text):
	return (TAGATOM, text[1:-1])
	
def scan_var(scanner, text):
	return (VAR, text)

gConsoleTypeTable = {
    'TypeSFXProfilePtr' : 52,
    'TypeSFXEnvironmentPtr' : 51,
    'TypeSFXDescriptionPtr' : 50,
    'TypeBox3F' : 49,
    'TypeMatrixRotation' : 48,
    'TypeMatrixPosition' : 47,
    'TypeRectF' : 46,
    'TypeRectI' : 45,
    'TypePoint4F' : 44,
    'TypePoint3F' : 43,
    'TypePoint2F' : 42,
    'TypePoint2I' : 41,
    'TypeRectSpacingI' : 40,
    'TypeGuiProfile' : 39,
    'TypeCubemapName' : 38,
    'TypeMaterialName' : 37,
    'TypeName' : 36,
    'TypeSimObjectName' : 35,
    'TypeSimObjectPtr' : 34,
    'TypeColorI' : 33,
    'TypeColorF' : 32,
    'TypeFlag' : 31,
    'TypeModifiedEnum' : 30,
    'TypeEnum' : 29,
    'TypeBoolVector' : 28,
    'TypeBool' : 27,
    'TypeF32Vector' : 26,
    'TypeF32' : 25,
    'TypeS32Vector' : 24,
    'TypeBitMask32' : 23,
    'TypeS32' : 22,
    'TypeS8' : 21,
    'TypeImageFilename' : 20,
    'TypeStringFilename' : 19,
    'TypeFilename' : 18,
    'TypeCommand' : 17,
    'TypeRealString' : 16,
    'TypeCaseString' : 15,
    'TypeString' : 14,
    'TypeLDrawDir' : 13,
    'TypeSplashDataPtr' : 12,
    'TypePrecipitationDataPtr' : 11,
    'TypeParticleEmitterDataPtr' : 10,
    'TypeExplosionDataPtr' : 9,
    'TypeDecalDataPtr' : 8,
    'TypeTriggerPolyhedron' : 7,
    'TypeProjectileDataPtr' : 6,
    'TypeWayPointTeam' : 5,
    'TypeLightFlareDataPtr' : 4,
    'TypeLightDescriptionPtr' : 3,
    'TypeLightAnimDataPtr' : 2,
    'TypeGameBaseDataPtr' : 1,
    'TypeDebrisDataPtr' : 0,
}

def scan_ident(scanner, text):
	global gConsoleTypeTable
	if text in gConsoleTypeTable:
		return (TYPE, gConsoleTypeTable[text])
	else:
		return (IDENT, text)

syntax_error = False

def lexerror(msg):
	def show_error(scanner, text):
		from sys import stderr
		global syntax_error
		name, line, col = scanner.position()
		if name:
			stderr.write("error lexing %s on line number %s: %s\n" % (name, line, str(msg)))
		else:
			stderr.write("error lexing: %s\n" % (str(msg)))
		stderr.write("\ttext \"%s\" was unlexable\n" % (text))
		syntax_error = True
		return (ILLEGAL_TOKEN,text)
	return show_error

ts_keywords = {
	"or" : rwCASEOR,
	"break" : rwBREAK,
	"return"   : rwRETURN,
	"else"     : rwELSE,
	"assert"   : rwASSERT,
	"while"    : rwWHILE,
	"do"       : rwDO,
	"if"       : rwIF,
	"for"      : rwFOR,
	"continue" : rwCONTINUE,
	"function" : rwDEFINE,
	"new"      : rwDECLARE,
	"singleton": rwDECLARESINGLETON,
	"datablock": rwDATABLOCK,
	"case"     : rwCASE,
	"switch$"  : rwSWITCHSTR,
	"switch"   : rwSWITCH,
	"default"  : rwDEFAULT,
	"package"  : rwPACKAGE,
	"namespace": rwNAMESPACE
}

def get_keyword_token(scanner, text):
	global ts_keywords
	name, line, col = scanner.position()
	return (ts_keywords[text],line)
	
def scan_hex(scanner, text):
	return (INTCONST, int(text, 16))
	
def scan_int(scanner, text):
	return (INTCONST, int(text))
	
def scan_float(scanner, text):
	return (FLTCONST, float(text))


DIGIT    = "[0-9]"
INTEGER  = "%s+" % (DIGIT)
FLOAT    = "(%s\.%s)|(%s(\.%s)?[eE][+-]?%s)" % (INTEGER, INTEGER, INTEGER, INTEGER, INTEGER)
LETTER   = "[A-Za-z_]"
FILECHAR = "[A-Za-z_\.]"
VARMID   = "[:A-Za-z0-9_]"
IDTAIL   = "[A-Za-z0-9_]"
VARTAIL  = "%s*%s" % (VARMID, IDTAIL)
VAREX    = "[$%%]%s(%s)*" % (LETTER, VARTAIL)
ID       = "%s%s*" % (LETTER, IDTAIL)
ILID     = "[$%%]%s+%s%s*" % (DIGIT, LETTER, VARTAIL)
FILENAME = "%s+" % (FILECHAR)
SPACE    = "[ \t\v\f]"
HEXDIGIT = "[a-fA-F0-9]"
DQ = '"'
SQ = "'"

lex = Lexicon([
	(re("%s+" % (SPACE)), IGNORE),
	(re("(///[^/][^\n\r]*[\n\r]*)+"), scan_doc_block),
	(re("//[^\n\r]*"), IGNORE),
	(re("[\r\n]"), IGNORE),	# The scanner instance takes care of linenumbers for us
	#(re("\"(\\.|[^\"\n\r])*\""), scan_string_atom),
	(Str("\"") + Rep((Str("\\")+AnyChar) | AnyBut("\"\n\r")) + Str("\""), scan_string_atom),	
	#(re("'(\\.|[^'\n\r])*'"), scan_tag_atom),
	(Str("\'") + Rep((Str("\\")+AnyChar) | AnyBut("\"\n\r")) + Str("\'"), scan_string_atom),
	(Str("=="), (opEQ,opEQ)),
	(Str("!="), (opNE,opNE)),
	(Str(">="), (opGE,opGE)),
	(Str("<="), (opLE,opLE)),
	(Str("&&" ),(opAND,opAND)),
	(Str("||"), (opOR,opOR)),
	(Str("::"), (opCOLONCOLON,opCOLONCOLON)),
	(Str("--"), (opMINUSMINUS,opMINUSMINUS)),
	(Str("++"), (opPLUSPLUS,opPLUSPLUS)),
	(Str("$="), (opSTREQ,opSTREQ)),
	(Str("!$="),(opSTRNE,opSTRNE)),
	(Str("<<"), (opSHL,opSHL)),
	(Str(">>"), (opSHR,opSHR)),
	(Str("+="), (opPLASN,opPLASN)),
	(Str("-="), (opMIASN,opMIASN)),
	(Str("*="), (opMLASN,opMLASN)),
	(Str("/="), (opDVASN,opDVASN)),
	(Str("%="), (opMODASN,opMODASN)),
	(Str("&="), (opANDASN,opANDASN)),
	(Str("^="), (opXORASN,opXORASN)),
	(Str("|="), (opORASN,opORASN)),
	(Str("<<="),(opSLASN,opSLASN)),
	(Str(">>="),(opSRASN,opSRASN)),
	(Str("->"), (opINTNAME,opINTNAME)),
	(Str("-->"),(opINTNAMER,opINTNAMER)),
	(Str("NL"),(opCAT,"\n")),
	(Str("TAB"),(opCAT,"\t")),
	(Str("SPC"),(opCAT," ")),
	(Str("@"), (opCAT,"@")),
	(Str("/*"), Begin("multiline-comment")),
	State("multiline-comment", [(Eof, lexerror("unexpected end of file found in comment")),
								 (Str("*/"), Begin("")),
								 (AnyChar, IGNORE)]
		),
	(Any("?[]()+-*/<>|.!:;{},&%^~="), TEXT),
	(re("|".join("(%s)" % (word.replace("$","\$")) for word in ts_keywords.keys())), get_keyword_token),
	(Str("true"), (INTCONST, 1)),
	(Str("false"), (INTCONST, 0)),
	(re(VAREX), scan_var),
	(re(ID), scan_ident),
	(re("0[xX]%s+" % (HEXDIGIT)), scan_hex),
	(re(INTEGER), scan_int),
	(re(FLOAT), scan_float),
	(re(ILID), lexerror("illegal token")),
	(AnyChar, lexerror("illegal token"))
])


scan_buffer = None

def get_current_file():
	global scan_buffer
	if scan_buffer:
		return scan_buffer.position()[0]
	else:
		return ""


def get_current_line():
	global scan_buffer
	if scan_buffer:
		return scan_buffer.position()[1]
	else:
		return -1
	

def set_scan_buffer(data, is_filename=True):
	global lex, scan_buffer
	import sys,os
	if is_filename:
		#handle = open(data, 'r')
		#file_contents = handle.read()
		#handle.close()
		scan_buffer = Scanner(lex, open(data, 'r'), data)
	else:
		clean_data = data.encode("ascii",'xmlcharrefreplace')
		if clean_data != data:
			sys.stderr.write("Warning, file-less scan buffer contains converted unicode characters. This probably shouldn't have happened \n")
		scan_buffer = Scanner(lex, StringIO(clean_data))
	scan_buffer.trace = int( os.environ.get('YYDEBUG','0') )

def reset_scan():
	global scan_buffer
	scan_buffer = None

def yylex():
	global scan_buffer
	retval, text = scan_buffer.read()
	#print "Token: %s; Text: %s" % (repr(retval), text)
	if isinstance(retval, str):
		# it's a string, must be an operator character
		retval = (retval, retval)
	elif retval == None:
		# EOF
		retval = (chr(0),"end-of-file")
	return retval

if __name__ == '__main__':
	import ytab, torque_lex
	import sys,os
	os.environ["YYDEBUG"]="1"
	sys.stdout = open("log.txt","w")
	sys.stderr = sys.stdout
	handle = open("/Users/thomas/Torque/T3D_101/FreeBuild/game/main.cs")
	data = handle.read()
	handle.close()
	torque_lex.set_scan_buffer(data,is_filename = False)
	ytab.yyparse()
	print "              \n\n\n\n\n  ---------------------------------------------\n\n\n\n            "
	ytab.yy_clear_stacks()
	torque_lex.set_scan_buffer("/Users/thomas/Torque/T3D_101/FreeBuild/game/main.cs")
	ytab.yyparse()