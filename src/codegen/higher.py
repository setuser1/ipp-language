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

#will be revised to clean out library stuff that are needed in higher.py
class front:
    def __init__(self, ast, source_path=None):
        self.ast = ast
        self.source_path = source_path  # path to source file

        self._alias_to_lib = {}  # Maps alias (e.g., "lib") -> actual lib name (e.g., "mylib")
        self.namespace_imports = set()
        self._specific_imports = {}  # item -> (lib_name, namespace)
        self._scoped_var_imports = {}  # imported name -> (owner, symbol, generated name)

        self._exposed_libs = set()  # Set of exposed library names
        self._exposed_funcs = {}  # Maps bare_name -> lib_name for exposed functions

        self.plib_track = {}

def process(self, structor=None):
        self.structor = structor

        # 1. Track all import stuff
        self.track_imports()

        # 2. Validate expose rules against the tracked imports
        self.validate_exposes()

        # 3. Seed the usage graph from the main AST
        self.scan_main_dependencies(self.ast)

        # Handoff payload for mid.py (or the linker)
        return {
            "main_ast": self.ast,
            "tracked_plibs": self.tracked_plibs,
            "alias_to_lib": self.alias_to_lib,
            "specific_imports": self.specific_imports,
            "exposed_libs": self.exposed_libs,
            "exposed_funcs": self.exposed_funcs,
            "used_in_main": self.used_in_main
        }


"""
higher.py should only track libraries, mid.py will be the one handling them.
Library tracking will be a separare class from the other stuff.
"""
