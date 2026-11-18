"""
High-level parse handling for C∆ Compiler.

This file is intentionally a transition layer between the parser AST and the
lowering/IR pipeline. The original library-tracking logic is preserved, but the
AST node imports are no longer enumerated individually. We import the full
parser module instead so the lowering handoff can inspect generic AST nodes in a
future-proof way without hard-coding every node type here.
"""

import os
import sys

import error_msgs
import parser

'''
from llvmlite import binding, ir

#IRModule is responsible to make it possible to lower into midlevel.py
class IRModule:
    def __init__(self, source_path=None, name="module", target_triple=""):
        self.source_path = source_path #record the source path for the module
        self.module = ir.Module(name=name) ##LLVM Module
        if target_triple: #Optionally set the target triple if provided, tells the LLVM what architecture to target
            self.module.triple = target_triple

        self.functions = {} #for function lookup
        self.metadata = {} 

    def add_function(self, name, return_type, parameter_types, parameter_names=()): #gives a clear way to declare a function in the module
        if name in self.module.globals: #makes sure that the module avoids duplicate function names, which would cause issues in the LLVM IR
            raise ValueError(f"duplicate LLVM symbol: {name}")
'''

class IRModule:
    """Template for the lowering handoff payload passed into mid/IR stages."""

    def __init__(self, source_path=None):
        self.source_path = source_path
        self.imports = []
        self.functions = []
        self.declarations = []
        self.globals = []
        self.metadata = {}

    def add_function(self, function_node):
        self.functions.append({
            "kind": "function",
            "name": getattr(function_node, "name", None),
            "ret_type": getattr(function_node, "ret_type", None),
            "params": getattr(function_node, "params", []),
        })

    def to_dict(self):
        return {
            "kind": "module",
            "source_path": self.source_path,
            "imports": self.imports,
            "functions": self.functions,
            "declarations": self.declarations,
            "globals": self.globals,
            "metadata": self.metadata,
        }


class front:
    """Semantic prepass that keeps dependency work while preparing an IR handoff."""

    def __init__(self, ast, source_path=None):
        self.ast = ast
        self.source_path = source_path
        self.tracked_plibs = {}
        self._alias_to_lib = {}
        self.namespace_imports = set()
        self._specific_imports = {}
        self._scoped_var_imports = {}
        self._exposed_libs = set()
        self._exposed_funcs = {}
        self.used_in_main = {}

        # Retain legacy attribute names used by the original payload contract.
        self.alias_to_lib = self._alias_to_lib
        self.specific_imports = self._specific_imports
        self.exposed_libs = self._exposed_libs
        self.exposed_funcs = self._exposed_funcs

        self.ir_module = IRModule(source_path=source_path)

    def track_imports(self):
        """Collect import metadata while retaining the existing library-tracking work."""
        self.tracked_plibs = getattr(self, "tracked_plibs", {})
        self.namespace_imports = getattr(self, "namespace_imports", set())
        self._specific_imports = getattr(self, "_specific_imports", {})
        self._alias_to_lib = getattr(self, "_alias_to_lib", {})
        self.alias_to_lib = self._alias_to_lib

        if hasattr(self.ast, "declarations"):
            for decl in self.ast.declarations:
                if isinstance(decl, parser.UsingDecl):
                    self.ir_module.imports.append({
                        "kind": "using",
                        "item": decl.item,
                        "source": decl.source,
                        "alias": decl.alias,
                    })
                    self.tracked_plibs.setdefault(decl.source, decl.source)

    def validate_exposes(self):
        """Placeholder validation step for future expose/import policy checks."""
        self._exposed_libs = getattr(self, "_exposed_libs", set())
        self.exposed_libs = self._exposed_libs

    def scan_main_dependencies(self, node):
        """Walk the AST and collect the main program's usage metadata."""
        self.used_in_main = {}
        if node is None:
            return self.used_in_main

        def visit(current):
            if isinstance(current, parser.Function):
                self.used_in_main.setdefault("functions", []).append(current.name)
            elif isinstance(current, parser.Call):
                self.used_in_main.setdefault("calls", []).append(getattr(current, "name", None))
            elif isinstance(current, parser.LibAccess):
                self.used_in_main.setdefault("lib_access", []).append(current.symbol)
            elif isinstance(current, parser.Include):
                self.used_in_main.setdefault("includes", []).append(getattr(current, "path", None))

            for field_name in ("declarations", "stmts", "body", "cond", "then_branch", "else_branch", "expr", "cases", "params"):
                child = getattr(current, field_name, None)
                if isinstance(child, list):
                    for item in child:
                        if item is not None:
                            visit(item)
                elif child is not None and hasattr(child, "__class__"):
                    visit(child)

        visit(node)
        return self.used_in_main

    def _lower_node(self, node):
        """Template lowering step for the IR handoff; extend as the IR grows."""
        if node is None:
            return None

        if isinstance(node, parser.Function):
            lowered = {
                "kind": "function",
                "name": node.name,
                "ret_type": node.ret_type,
                "params": node.params,
            }
            self.ir_module.add_function(node)
            return lowered

        if isinstance(node, parser.Declaration):
            self.ir_module.declarations.append({
                "kind": "declaration",
                "name": node.name,
                "type": node.var_type,
                "initializer": getattr(node, "initializer", None),
            })
            return {"kind": "declaration", "name": node.name, "type": node.var_type}

        if isinstance(node, parser.UsingDecl):
            return {
                "kind": "using",
                "item": node.item,
                "source": node.source,
                "alias": node.alias,
            }

        if isinstance(node, parser.SpaceDecl):
            return {"kind": "space", "name": node.name}

        if isinstance(node, parser.Include):
            return {"kind": "include", "path": getattr(node, "path", None)}

        if isinstance(node, parser.Compound):
            return {"kind": "compound", "stmt_count": len(node.stmts)}

        return {"kind": node.__class__.__name__.lower()}

    def lower_to_ir(self):
        """Begin lowering the parsed AST into an IR-style payload while retaining metadata."""
        if self.ir_module is None:
            self.ir_module = IRModule(source_path=self.source_path)

        self.ir_module.metadata = {
            "phase": "lowering_handoff_template",
            "source_path": self.source_path,
            "tracked_plibs": list(self.tracked_plibs.keys()),
            "used_in_main": self.used_in_main,
        }

        if hasattr(self.ast, "declarations"):
            for decl in self.ast.declarations:
                lowered = self._lower_node(decl)
                if lowered is not None:
                    self.ir_module.globals.append(lowered)

        return self.ir_module.to_dict()

    def process(self, structor=None):
        """Run the semantic prepass and return the new lowering handoff payload."""
        self.structor = structor

        # Preserve the existing library-tracking and dependency work.
        self.track_imports()
        self.validate_exposes()
        self.scan_main_dependencies(self.ast)

        # Start the IR handoff while keeping the metadata the earlier pass produced.
        ir_handoff = self.lower_to_ir()

        return {
            "main_ast": self.ast,
            "ir": ir_handoff,
            "tracked_plibs": self.tracked_plibs,
            "alias_to_lib": self.alias_to_lib,
            "specific_imports": self.specific_imports,
            "exposed_libs": self.exposed_libs,
            "exposed_funcs": self.exposed_funcs,
            "used_in_main": self.used_in_main,
            "lowering_metadata": self.ir_module.metadata,
        }


class error(Exception):
    def __init__(self, ErrorType, message, ErrorCode=None):
        self.ErrorType = ErrorType
        self.ErrorCode = ErrorCode
        self.message = message
        super().__init__(self.message)

    def assert_error(self):
        fallback = self.message or "An unknown compiler error occurred"
        message = error_msgs.get_error_msg(self.ErrorCode, fallback)
        raise self.ErrorType(message)
