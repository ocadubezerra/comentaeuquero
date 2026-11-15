"""Migração explícita; requer banco existente e backup com restauração testada."""
import argparse

from . import db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-testado", action="store_true", required=True,
                        help="Confirma backup e restauração testada antes da migração")
    parser.parse_args()
    if not db.DB_PATH.is_file():
        parser.error("Banco não encontrado em DATA_DIR; nenhuma alteração feita")
    contas, segredos = db.migrar_credenciais()
    print(f"Migração concluída: {contas} contas e {segredos} ajustes cifrados.")
    print("Backups antigos e páginas livres/WAL podem conservar valores anteriores; proteja-os.")


if __name__ == "__main__":
    main()
