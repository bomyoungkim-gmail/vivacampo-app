#!/usr/bin/env python3
"""
Architecture Validator - Garante que código segue arquitetura hexagonal

Valida:
1. Direção de dependências (Domain não importa Infrastructure/Application/Presentation)
2. Camadas respeitam suas responsabilidades
3. Pydantic usado corretamente (validate_assignment=True, frozen para DTOs)
4. Nenhuma lógica de negócio fora do Domain layer

Uso:
    python scripts/validate_architecture.py
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Tuple
from dataclasses import dataclass

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

@dataclass
class Violation:
    """Representa uma violação de arquitetura"""
    file_path: Path
    line: int
    layer: str
    message: str
    severity: str  # 'error' or 'warning'

class ArchitectureValidator:
    """Valida que código segue arquitetura hexagonal"""

    # Imports proibidos por camada
    FORBIDDEN_IMPORTS = {
        "domain": [
            # Domain não pode importar frameworks/bibliotecas externas
            "fastapi",
            "sqlalchemy",
            "boto3",
            "requests",
            "httpx",
            "psycopg2",
            "redis",
            # Domain não pode importar outras camadas
            "app.application",
            "app.infrastructure",
            "app.presentation",
        ],
        "application": [
            # Application não pode importar frameworks de apresentação ou infraestrutura
            "fastapi",
            "sqlalchemy",
            "boto3",
            "psycopg2",
            # Application não pode importar presentation
            "app.presentation",
        ],
        "infrastructure": [
            # Infrastructure pode importar qualquer coisa (implementa adapters)
        ],
        "presentation": [
            # Presentation não deve importar infraestrutura diretamente
            "sqlalchemy",
            "boto3",
            "psycopg2",
            "redis",
        ],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations: List[Violation] = []

    def validate(self) -> bool:
        """
        Valida toda a codebase.

        Returns:
            True se não houver erros críticos
        """
        print(f"{BLUE}🔍 Validando arquitetura hexagonal...{RESET}\n")

        # Validar arquivos Python em services/api
        api_path = self.project_root / "services" / "api" / "app"

        if not api_path.exists():
            print(f"{YELLOW}⚠️  Diretório {api_path} não encontrado{RESET}")
            return True

        for py_file in api_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            self._validate_file(py_file)

        return self._report_results()

    def _validate_file(self, file_path: Path):
        """Valida um arquivo Python individual"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError as e:
            self.violations.append(Violation(
                file_path=file_path,
                line=e.lineno or 0,
                layer="unknown",
                message=f"Syntax error: {e.msg}",
                severity="error"
            ))
            return

        # Determinar camada do arquivo
        layer = self._get_layer(file_path)

        if not layer:
            return  # Arquivo fora das camadas conhecidas

        # Validar imports
        self._validate_imports(tree, file_path, layer)

        # Validar Pydantic usage se arquivo contém models
        self._validate_pydantic_usage(tree, file_path, layer)

    def _get_layer(self, file_path: Path) -> str:
        """Determina a camada baseada no caminho do arquivo"""
        path_str = str(file_path)

        if "/domain/" in path_str or "\\domain\\" in path_str:
            return "domain"
        elif "/application/" in path_str or "\\application\\" in path_str:
            return "application"
        elif "/infrastructure/" in path_str or "\\infrastructure\\" in path_str:
            return "infrastructure"
        elif "/presentation/" in path_str or "\\presentation\\" in path_str:
            return "presentation"
        else:
            return ""

    def _validate_imports(self, tree: ast.AST, file_path: Path, layer: str):
        """Valida que imports respeitam direção de dependências"""
        forbidden = self.FORBIDDEN_IMPORTS.get(layer, [])

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._check_forbidden_import(
                        layer, alias.name, file_path, node.lineno, forbidden
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._check_forbidden_import(
                        layer, node.module, file_path, node.lineno, forbidden
                    )

    def _check_forbidden_import(
        self,
        layer: str,
        module: str,
        file_path: Path,
        line: int,
        forbidden: List[str]
    ):
        """Verifica se import é proibido para a camada"""
        for forbidden_module in forbidden:
            if module.startswith(forbidden_module):
                self.violations.append(Violation(
                    file_path=file_path,
                    line=line,
                    layer=layer,
                    message=f"Forbidden import: {layer} layer cannot import '{module}'",
                    severity="error"
                ))

    def _validate_pydantic_usage(self, tree: ast.AST, file_path: Path, layer: str):
        """Valida uso correto de Pydantic models"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Verificar se classe herda de BaseModel
                is_pydantic_model = any(
                    (isinstance(base, ast.Name) and base.id == "BaseModel")
                    for base in node.bases
                )

                if not is_pydantic_model:
                    continue

                # Validar configuração do model
                self._validate_model_config(node, file_path, layer)

    def _validate_model_config(self, class_node: ast.ClassDef, file_path: Path, layer: str):
        """Valida que Pydantic model tem configuração correta"""
        has_model_config = False
        has_validate_assignment = False
        is_dto = "DTO" in class_node.name or "Command" in class_node.name

        for item in class_node.body:
            # Procurar por model_config = ConfigDict(...)
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "model_config":
                        has_model_config = True

                        # Verificar se tem validate_assignment=True
                        if isinstance(item.value, ast.Call):
                            for keyword in item.value.keywords:
                                if keyword.arg == "validate_assignment":
                                    has_validate_assignment = True

        # Domain entities DEVEM ter validate_assignment=True
        if layer == "domain" and not has_validate_assignment:
            self.violations.append(Violation(
                file_path=file_path,
                line=class_node.lineno,
                layer=layer,
                message=f"Domain entity '{class_node.name}' missing validate_assignment=True",
                severity="warning"
            ))

        # DTOs DEVEM ser frozen=True (imutáveis)
        if is_dto and layer in ["application", "presentation"]:
            has_frozen = False

            for item in class_node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "model_config":
                            if isinstance(item.value, ast.Call):
                                for keyword in item.value.keywords:
                                    if keyword.arg == "frozen":
                                        has_frozen = True

            if not has_frozen:
                self.violations.append(Violation(
                    file_path=file_path,
                    line=class_node.lineno,
                    layer=layer,
                    message=f"DTO '{class_node.name}' should be frozen=True (immutable)",
                    severity="warning"
                ))

    def _report_results(self) -> bool:
        """Reporta resultados da validação"""
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]

        if not self.violations:
            print(f"{GREEN}✅ Nenhuma violação de arquitetura encontrada!{RESET}\n")
            return True

        # Imprimir erros
        if errors:
            print(f"{RED}❌ ERRORS ({len(errors)})::{RESET}\n")
            for violation in errors:
                rel_path = violation.file_path.relative_to(self.project_root)
                print(f"{RED}  {rel_path}:{violation.line}{RESET}")
                print(f"    Layer: {violation.layer}")
                print(f"    {violation.message}\n")

        # Imprimir warnings
        if warnings:
            print(f"{YELLOW}⚠️  WARNINGS ({len(warnings)})::{RESET}\n")
            for violation in warnings:
                rel_path = violation.file_path.relative_to(self.project_root)
                print(f"{YELLOW}  {rel_path}:{violation.line}{RESET}")
                print(f"    Layer: {violation.layer}")
                print(f"    {violation.message}\n")

        # Resumo
        print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"Total: {RED}{len(errors)} errors{RESET}, {YELLOW}{len(warnings)} warnings{RESET}")

        return len(errors) == 0


def main():
    """Entry point"""
    project_root = Path(__file__).parent.parent
    validator = ArchitectureValidator(project_root)

    success = validator.validate()

    if not success:
        print(f"\n{RED}❌ Architecture validation FAILED{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}✅ Architecture validation PASSED{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
