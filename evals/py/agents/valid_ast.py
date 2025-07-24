import ast

def validate_agent_code(code: str) -> tuple[int, dict]:
    try:
        tree = ast.parse(code)
        report = {}

        # 1. Classe LLMAgent
        report["has_llm_agent"] = any(
            isinstance(node, ast.ClassDef) and node.name == "Agent"
            for node in tree.body
        )

        # 2. Função main
        report["has_main_func"] = any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in tree.body
        )

        # 3. Bloco __main__ com asyncio.run(main())
        report["has_main_block"] = any(
            isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and
            any(
                isinstance(e, ast.Constant) and e.value == "__main__"
                for e in ast.walk(node.test)
            ) and
            any(
                isinstance(e, ast.Call) and getattr(e.func, 'attr', '') == "run"
                for e in ast.walk(node)
            )
            for node in tree.body
        )

        # 4. Classe MCPTool com método abstrato execute
        report["has_mcp_tool_class"] = False
        report["has_execute_in_mcp_tool"] = False
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "MCPTool":
                report["has_mcp_tool_class"] = True
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "execute":
                        report["has_execute_in_mcp_tool"] = True

        # 5. Classe concreta que herda MCPTool e implementa execute
        report["has_tool_impl"] = False
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                base_names = [base.id for base in node.bases if isinstance(base, ast.Name)]
                if "MCPTool" in base_names:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == "execute":
                            report["has_tool_impl"] = True

        # Pontuação: 1 ponto por item encontrado
        score = sum(report.values())
        return score, report

    except Exception as e:
        print(f"Erro na validação do código: {e}")
        return 0, {"error": str(e)}


if __name__ == "__main__":
    try:
        with open("agent_generated.py", "r", encoding="utf-8") as f:
            code = f.read()

        score, report = validate_agent_code(code)
        print(f"\n✅ Pontuação: {score}/6")
        for key, value in report.items():
            status = "✅ OK" if value else "❌ Faltando"
            print(f"- {key}: {status}")
    except FileNotFoundError:
        print("❌ Arquivo 'agent_generated.py' não encontrado.")
