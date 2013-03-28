#!python
# Komodo TorqueScript language service.

"""Language package for TorqueScript"""

import os
import re
import logging

import process
import koprocessutils

from koLanguageServiceBase import *
from koUDLLanguageBase import KoUDLLanguage
from xpcom import components, ServerException
import xpcom.server

sci_constants = components.interfaces.ISciMoz


log = logging.getLogger("koTorqueScriptLanguage")
log.setLevel(logging.DEBUG)


def registerLanguage(registry):
    log.debug("Registering language TorqueScript")
    registry.registerLanguage(KoTorqueScriptLanguage())


class KoTorqueScriptLanguage(KoUDLLanguage, KoLanguageBaseDedentMixin):
    name = "TorqueScript"
    _reg_desc_ = "%s Language" % name
    _reg_contractid_ = "@activestate.com/koLanguage?language=%s;1" % name
    _reg_clsid_ = "c144db8f-e44e-497d-9bd3-ba56d13a96c8"
    _reg_categories_ = [("komodo-language", name)]
    _com_interfaces_ = [components.interfaces.koILanguage,
                        components.interfaces.nsIObserver]

    lexresLangName = "TorqueScript"
    lang_from_udl_family = { 'SSL' : 'TorqueScript', 'M' : 'TorqueML'}
    namedBlockRE = r'^(.*?function\s+[&]*?\s*[\w_]*)|(^.*?(package)\s+[\w_]*)|(^.*?(datablock|singleton)\s+\(\s+[\w_]*\))'
    namedBlockDescription = 'PHP functions and classes'
     
    defaultExtension = ".cs"
    variableIndicators = '$%'
    downloadURL = 'http://www.garagegames.com'
    commentDelimiterInfo = {
        "line": [ "//" ],
        "block": [ ("/*", "*/") ]
    }
    _dedenting_statements = [u'return', u'break', u'continue']
    _indenting_statements = [u'case']
    supportsSmartIndent = "brace"
    _indent_chars = "{}"
    _indent_open_chars = "{"
    _indent_close_chars = "}"
    _lineup_chars = u"{}()[]"
    _lineup_open_chars = "([{" # Perl tells the difference between the indent and lineup {}'s
    _lineup_close_chars = ")]}"
    sample = """package Sample{
    function foo(%bar) {
        echo("baz" SPC $global_awesome);
        commandToServer('do_more_stuff');
        return 5;
    }
};
activatePackage(Sample);"""

    def __init__(self):
        KoUDLLanguage.__init__(self)
        KoLanguageBaseDedentMixin.__init__(self)
        
        self.matchingSoftChars = {"(": (")", None),
                                  "{": ("}", None),
                                  "[": ("]", None),
                                  '"': ('"', self.softchar_accept_matching_double_quote),
                                  "'": ("'", self.softchar_accept_matching_single_quote),
                                  }            
        
        self._setupIndentCheckSoftChar()


