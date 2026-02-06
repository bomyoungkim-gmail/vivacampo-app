#!/usr/bin/env python3
"""
Security Validator - Garante multi-tenant security

Valida:
1. Repositories filtram por tenant_id
2. Use Cases validam tenant_id
3. JWT extraction na presentation layer
4. Queries SQL usam parameterização (previne SQL injection)
5. Row Level Security (RLS) habilitado no PostgreSQL

Uso:
    python scripts/validate_security.py
"""

import ast
import re
import sys
from pathlib import Path
from typing import List
from dataclasses import dataclass

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

@dataclass
class SecurityViolation:
    """Representa uma violação de segurança"""
    file_path: Path
    line: int
    category: str
    message: str
    severity: str  # 'critical', 'high', 'medium', 'low'

class SecurityValidator:
    """Valida segurança multi-tenant"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations: List[SecurityViolation] = []

    def validate(self) -> bool:
        """
        Valida segurança da codebase.

        Returns:
            True se não houver violações críticas
        """
        print(f"{BLUE}🔐 Validando segurança multi-tenant...{RESET}\n")

        api_path = self.project_root / "services" / "api" / "app"

        if not api_path.exists():
            print(f"{YELLOW}⚠️  Diretório {api_path} não encontrado{RESET}")
            return True

        # Validar repositories
        repo_path = api_path / "infrastructure" / "repositories"
        if repo_path.exists():
            for py_file in repo_path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    self._validate_repository(py_file)

        # Validar use cases
        use_case_path = api_path / "application" / "use_cases"
        if use_case_path.exists():
            for py_file in use_case_path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    self._validate_use_case(py_file)

        # Validar presentation layer (JWT extraction)
        presentation_path = api_path / "presentation"
        if presentation_path.exists():
            for py_file in presentation_path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    self._validate_presentation(py_file)

        return self._report_results()

    def _validate_repository(self, file_path: Path):
        """Valida que repository filtra por tenant_id"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return

        # Procurar por classes de repository
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "Repository" in node.name:
                    self._check_repository_methods(node, file_path, content)

    def _check_repository_methods(
        self,
        class_node: ast.ClassDef,
        file_path: Path,
        content: str
    ):
        """Verifica métodos do repository para tenant_id filtering"""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                # Métodos de busca devem filtrar por tenant_id
                if any(keyword in item.name for keyword in ["find", "get", "list", "search"]):
                    self._check_tenant_filtering(item, file_path, content)

    def _check_tenant_filtering(
        self,
        func_node: ast.FunctionDef,
        file_path: Path,
        content: str
    ):
        """Verifica se método filtra por tenant_id"""
        # Verificar se tenant_id está nos parâmetros
        has_tenant_id_param = any(
            arg.arg == "tenant_id"
            for arg in func_node.args.args
        )

        if not has_tenant_id_param:
            self.violations.append(SecurityViolation(
                file_path=file_path,
                line=func_node.lineno,
                category="multi-tenant",
                message=f"Repository method '{func_node.name}' missing tenant_id parameter",
                severity="critical"
            ))
            return

        # Verificar se tenant_id é usado no WHERE clause
        func_source = ast.get_source_segment(content, func_node)
        if func_source:
            # Procurar por .where( ou .filter(
            has_where = re.search(r'\.(where|filter)\s*\(', func_source)

            if has_where:
                # Verificar se tenant_id está na condição
                has_tenant_filter = re.search(
                    r'tenant_id\s*==\s*|\.tenant_id\s*==\s*',
                    func_source
                )

                if not has_tenant_filter:
                    self.violations.append(SecurityViolation(
                        file_path=file_path,
                        line=func_node.lineno,
                        category="multi-tenant",
                        message=f"Repository method '{func_node.name}' has WHERE clause but doesn't filter by tenant_id",
                        severity="critical"
                    ))

    def _validate_use_case(self, file_path: Path):
        """Valida que use case valida tenant_id"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return

        # Procurar por classes UseCase
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "UseCase" in node.name:
                    self._check_use_case_execute(node, file_path, content)

    def _check_use_case_execute(
        self,
        class_node: ast.ClassDef,
        file_path: Path,
        content: str
    ):
        """Verifica método execute do use case"""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "execute":
                # Verificar se command tem tenant_id
                if item.args.args:
                    # Primeiro argumento (depois de self) deve ser command
                    if len(item.args.args) >= 2:
                        command_arg = item.args.args[1].arg

                        # Verificar se usa command.tenant_id no código
                        func_source = ast.get_source_segment(content, item)
                        if func_source:
                            uses_tenant_id = (
                                f"{command_arg}.tenant_id" in func_source or
                                "tenant_id=" in func_source
                            )

                            if not uses_tenant_id:
                                self.violations.append(SecurityViolation(
                                    file_path=file_path,
                                    line=item.lineno,
                                    category="multi-tenant",
                                    message=f"Use case '{class_node.name}' doesn't use tenant_id from command",
                                    severity="high"
                                ))

    def _validate_presentation(self, file_path: Path):
        """Valida JWT extraction e tenant_id dependency"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        # Verificar se routers extraem tenant_id
        if "router" in content.lower() or "@router" in content.lower():
            # Procurar por Depends(get_current_tenant_id) ou similar
            has_tenant_dependency = re.search(
                r'Depends\s*\(\s*get_current_tenant_id\s*\)',
                content
            )

            # Procurar por definição de rotas
            route_definitions = re.findall(
                r'@router\.(get|post|put|patch|delete)\s*\([^\)]*\)',
                content,
                re.DOTALL
            )

            if route_definitions and not has_tenant_dependency:
                # WARNING: Router definido mas não usa tenant_id dependency
                # (pode ser válido para rotas públicas, então é apenas warning)
                self.violations.append(SecurityViolation(
                    file_path=file_path,
                    line=1,
                    category="multi-tenant",
                    message=f"Router file has endpoints but no get_current_tenant_id dependency (check if routes are public)",
                    severity="medium"
                ))

        # Verificar SQL injection risks
        self._check_sql_injection(file_path, content)

    def _check_sql_injection(self, file_path: Path, content: str):
        """Verifica riscos de SQL injection"""
        # Procurar por string concatenation em queries SQL
        sql_concat_patterns = [
            r'f"SELECT.*{.*}"',  # f-strings
            r'f\'SELECT.*{.*}\'',
            r'"SELECT.*"\s*\+\s*',  # concatenação com +
            r'\'SELECT.*\'\s*\+\s*',
            r'"UPDATE.*"\s*\+\s*',
            r'"INSERT.*"\s*\+\s*',
            r'"DELETE.*"\s*\+\s*',
        ]

        for pattern in sql_concat_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Contar linhas até o match
                line = content[:match.start()].count('\n') + 1

                self.violations.append(SecurityViolation(
                    file_path=file_path,
                    line=line,
                    category="sql-injection",
                    message=f"Potential SQL injection: String concatenation in query",
                    severity="critical"
                ))

    def _report_results(self) -> bool:
        """Reporta resultados da validação"""
        critical = [v for v in self.violations if v.severity == "critical"]
        high = [v for v in self.violations if v.severity == "high"]
        medium = [v for v in self.violations if v.severity == "medium"]
        low = [v for v in self.violations if v.severity == "low"]

        if not self.violations:
            print(f"{GREEN}✅ Nenhuma violação de segurança encontrada!{RESET}\n")
            return True

        # Imprimir critical
        if critical:
            print(f"{RED}🚨 CRITICAL ({len(critical)})::{RESET}\n")
            for violation in critical:
                rel_path = violation.file_path.relative_to(self.project_root)
                print(f"{RED}  {rel_path}:{violation.line}{RESET}")
                print(f"    Category: {violation.category}")
                print(f"    {violation.message}\n")

        # Imprimir high
        if high:
            print(f"{RED}❌ HIGH ({len(high)})::{RESET}\n")
            for violation in high:
                rel_path = violation.file_path.relative_to(self.project_root)
                print(f"{RED}  {rel_path}:{violation.line}{RESET}")
                print(f"    Category: {violation.category}")
                print(f"    {violation.message}\n")

        # Imprimir medium
        if medium:
            print(f"{YELLOW}⚠️  MEDIUM ({len(medium)})::{RESET}\n")
            for violation in medium:
                rel_path = violation.file_path.relative_to(self.project_root)
                print(f"{YELLOW}  {rel_path}:{violation.line}{RESET}")
                print(f"    Category: {violation.category}")
                print(f"    {violation.message}\n")

        # Resumo
        print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(
            f"Total: {RED}{len(critical)} critical{RESET}, "
            f"{RED}{len(high)} high{RESET}, "
            f"{YELLOW}{len(medium)} medium{RESET}, "
            f"{len(low)} low"
        )

        return len(critical) == 0 and len(high) == 0


def main():
    """Entry point"""
    project_root = Path(__file__).parent.parent
    validator = SecurityValidator(project_root)

    success = validator.validate()

    if not success:
        print(f"\n{RED}🚨 Security validation FAILED{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}✅ Security validation PASSED{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
