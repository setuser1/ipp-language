"""
High level parse handling for C∆ Compiler.
"""

import os
import sys
import error_msgs

from parser import (
    Alloc,
    ArrayAccess,
    ArrayDesignation,
    Assignment,
    Binary,
    Comma,
    Break,
    Call,
    Cast,
    Compound,
    CompoundLiteral,
    Continue,
    Declaration,
    Define,
    DesignatedInit,
    Do,
    ExposeDecl,
    ExprStmt,
    FieldAccess,
    For,
    Free,
    Function,
    Generic,
    Goto,
    If,
    Include,
    InitList,
    Label,
    LibAccess,
    Literal,
    Return,
    SpaceDecl,
    StructDef,
    Switch,
    Typedef,
    TypeExpr,
    Unary,
    UsingDecl,
    Var,
    While,
)

#will be revised to clean out library stuff that are needed in higher.py, some old code are used, just renamed
class front:
    def __init__(self, ast, source_path=None):
        self.ast = ast
        self.source_path = source_path  # path to source file
        self.tracked_plibs = {} #tracks library name and absolute path
        self._alias_to_lib = {}  # Maps alias (e.g., "lib") -> actual lib name (e.g., "mylib")
        self.namespace_imports = set() # Track libs imported as full namespaces
        self._specific_imports = {}  # item -> (lib_name, namespace)
        self._scoped_var_imports = {}  # imported name -> (owner, symbol, generated name)
        self._exposed_libs = set()  # Set of exposed library names
        self._exposed_funcs = {}  # Maps bare_name -> lib_name for exposed functions

def process(self, structor=None):
        self.structor = structor

        #Track all imported libraries
        self.track_imports()

        #Validate expose rules against the tracked imports
        self.validate_exposes()

        #Seed the usage graph from the main AST
        self.scan_main_dependencies(self.ast)

        #Handoff payload for mid.py
        return {
            "main_ast": self.ast,
            "tracked_plibs": self.tracked_plibs,
            "alias_to_lib": self.alias_to_lib,
            "specific_imports": self.specific_imports,
            "exposed_libs": self.exposed_libs,
            "exposed_funcs": self.exposed_funcs,
            "used_in_main": self.used_in_main
        }

'''
def lib_error(self):
    #library related errors for if it is not found or is untracked
'''

'''
def tracker(self):
    #error tracking stuff
'''
