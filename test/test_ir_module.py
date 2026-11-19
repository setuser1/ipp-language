import unittest

from llvmlite import ir

import higher
import parser


class IRModuleTests(unittest.TestCase):
    def test_module_configuration_and_function_declaration(self):
        module = higher.IRModule(
            source_path="sample.ix",
            name="sample",
            target_triple="x86_64-unknown-linux-gnu",
        )
        function = module.add_function(
            "sum",
            ir.IntType(32),
            [ir.IntType(32), ir.IntType(32)],
            ["left", "right"],
        )

        self.assertEqual(module.module.name, "sample")
        self.assertEqual(module.module.triple, "x86_64-unknown-linux-gnu")
        self.assertEqual(function.args[0].name, "left")
        self.assertEqual(function.args[1].name, "right")
        llvm_ir = str(module.module)
        self.assertIn("sum", llvm_ir)
        self.assertIn("i32", llvm_ir)
        self.assertEqual(module.to_dict()["functions"][0]["name"], "sum")

    def test_duplicate_function_symbol_is_rejected(self):
        module = higher.IRModule()
        module.add_function("run", ir.VoidType(), [])

        with self.assertRaisesRegex(ValueError, "duplicate LLVM symbol: run"):
            module.add_function("run", ir.VoidType(), [])

    def test_parameter_names_must_match_parameter_types(self):
        module = higher.IRModule()

        with self.assertRaisesRegex(ValueError, "parameter_names must match"):
            module.add_function(
                "run",
                ir.VoidType(),
                [ir.IntType(32), ir.IntType(32)],
                ["value"],
            )

    def test_front_declares_parser_function_in_llvm_module(self):
        function = parser.Function(
            ret_type="int",
            name="answer",
            params=[("int", "value")],
            body=parser.Compound(stmts=[]),
        )
        prepass = higher.front(parser.Program(declarations=[function]))

        handoff = prepass.process()

        self.assertIn("answer", handoff["ir"]["llvm_ir"])
        self.assertIn("i32", handoff["ir"]["llvm_ir"])
        self.assertEqual(handoff["ir"]["functions"][0]["name"], "answer")


if __name__ == "__main__":
    unittest.main()
