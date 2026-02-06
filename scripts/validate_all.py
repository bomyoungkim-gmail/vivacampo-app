#!/usr/bin/env python3
"""
Master Validator - Executa todos os validadores de arquitetura e segurança

Executa:
1. Architecture Validator - Valida camadas e dependências
2. Security Validator - Valida multi-tenant e SQL injection
3. (Futuro) Contract Validator - Valida Pydantic schemas
4. (Futuro) Test Coverage - Valida cobertura de testes

Uso:
    python scripts/validate_all.py

    # Com verbose output
    python scripts/validate_all.py --verbose

    # Falhar em warnings
    python scripts/validate_all.py --strict

CI/CD:
    Adicionar ao .github/workflows/validate.yml
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

class MasterValidator:
    """Executa todos os validadores"""

    def __init__(self, verbose: bool = False, strict: bool = False):
        self.verbose = verbose
        self.strict = strict
        self.project_root = Path(__file__).parent.parent

    def run(self) -> bool:
        """
        Executa todos os validadores.

        Returns:
            True se todos passaram
        """
        print(f"{BOLD}{BLUE}{'=' * 60}{RESET}")
        print(f"{BOLD}{BLUE}VivaCampo - Master Validator{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

        validators = [
            ("Architecture", "scripts/validate_architecture.py"),
            ("Security", "scripts/validate_security.py"),
        ]

        results: List[Tuple[str, bool, float]] = []
        failed_validators: List[str] = []

        for name, script_path in validators:
            success, duration = self._run_validator(name, script_path)
            results.append((name, success, duration))

            if not success:
                failed_validators.append(name)

        # Relatório final
        self._print_summary(results, failed_validators)

        return len(failed_validators) == 0

    def _run_validator(self, name: str, script_path: str) -> Tuple[bool, float]:
        """
        Executa um validador individual.

        Returns:
            (success, duration_seconds)
        """
        print(f"{BOLD}{'─' * 60}{RESET}")
        print(f"{BOLD}{BLUE}Running {name} Validator...{RESET}\n")

        script_full_path = self.project_root / script_path

        if not script_full_path.exists():
            print(f"{RED}❌ Validator script not found: {script_path}{RESET}\n")
            return False, 0.0

        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, str(script_full_path)],
                capture_output=not self.verbose,
                text=True,
                cwd=self.project_root
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                print(f"{GREEN}✅ {name} Validator PASSED{RESET} ({duration:.2f}s)\n")
                return True, duration
            else:
                print(f"{RED}❌ {name} Validator FAILED{RESET} ({duration:.2f}s)\n")

                if not self.verbose and result.stdout:
                    print(result.stdout)

                return False, duration

        except Exception as e:
            duration = time.time() - start_time
            print(f"{RED}❌ {name} Validator ERROR: {e}{RESET} ({duration:.2f}s)\n")
            return False, duration

    def _print_summary(
        self,
        results: List[Tuple[str, bool, float]],
        failed_validators: List[str]
    ):
        """Imprime resumo final"""
        print(f"{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}SUMMARY{RESET}")
        print(f"{BOLD}{'=' * 60}{RESET}\n")

        # Tabela de resultados
        for name, success, duration in results:
            status = f"{GREEN}✅ PASSED{RESET}" if success else f"{RED}❌ FAILED{RESET}"
            print(f"  {name:20} {status:20} ({duration:.2f}s)")

        print()

        # Total
        total = len(results)
        passed = sum(1 for _, success, _ in results if success)
        failed = total - passed

        total_duration = sum(duration for _, _, duration in results)

        print(f"{BOLD}Total:{RESET} {total} validators")
        print(f"{GREEN}Passed:{RESET} {passed}")
        print(f"{RED}Failed:{RESET} {failed}")
        print(f"Duration: {total_duration:.2f}s\n")

        # Resultado final
        if failed == 0:
            print(f"{BOLD}{GREEN}{'=' * 60}{RESET}")
            print(f"{BOLD}{GREEN}✅ ALL VALIDATIONS PASSED!{RESET}")
            print(f"{BOLD}{GREEN}{'=' * 60}{RESET}\n")
        else:
            print(f"{BOLD}{RED}{'=' * 60}{RESET}")
            print(f"{BOLD}{RED}❌ VALIDATION FAILED{RESET}")
            print(f"{BOLD}{RED}{'=' * 60}{RESET}\n")
            print(f"{RED}Failed validators:{RESET}")
            for validator in failed_validators:
                print(f"  - {validator}")
            print()


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run all architecture and security validators"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output from validators"
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Fail on warnings (not just errors)"
    )

    args = parser.parse_args()

    validator = MasterValidator(verbose=args.verbose, strict=args.strict)
    success = validator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
