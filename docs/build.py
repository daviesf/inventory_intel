#!/usr/bin/env python3
"""
build.py - Script de build para documentação IntelliStock

Executa latexmk ou pdflatex para gerar o PDF da documentação.
Uso: python build.py

Requer uma distribuição LaTeX instalada (TeX Live, MiKTeX, etc.)
"""

import subprocess
import sys
import shutil
from pathlib import Path


def find_latex_tool():
    """Encontra a ferramenta LaTeX disponível no sistema."""
    # Ordem de preferência
    tools = ["latexmk", "pdflatex", "xelatex", "lualatex"]
    
    for tool in tools:
        if shutil.which(tool):
            return tool
    
    return None


def build_with_latexmk(docs_dir, main_tex):
    """Build usando latexmk (compilação automática)."""
    cmd = [
        "latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory=" + str(docs_dir),
        str(main_tex)
    ]
    return subprocess.run(cmd, cwd=docs_dir, check=False)


def build_with_pdflatex(docs_dir, main_tex):
    """Build usando pdflatex (precisa executar múltiplas vezes)."""
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory=" + str(docs_dir),
        str(main_tex)
    ]
    
    # Executar 3 vezes para resolver referências e TOC
    for i in range(3):
        print(f"\n[pdflatex pass {i+1}/3]")
        result = subprocess.run(cmd, cwd=docs_dir, check=False)
        if result.returncode != 0:
            return result
    
    return result


def main():
    """Executa o build da documentação LaTeX."""
    # Diretório do script
    docs_dir = Path(__file__).parent.resolve()
    main_tex = docs_dir / "main.tex"
    
    # Verificar se o arquivo principal existe
    if not main_tex.exists():
        print(f"ERRO: Arquivo {main_tex} não encontrado.")
        sys.exit(1)
    
    print("=" * 50)
    print("IntelliStock - Build de Documentação")
    print("=" * 50)
    print(f"\nDiretório: {docs_dir}")
    print(f"Arquivo: main.tex")
    
    # Encontrar ferramenta LaTeX
    tool = find_latex_tool()
    
    if tool is None:
        print("\n" + "=" * 50)
        print("✗ NENHUMA DISTRIBUIÇÃO LATEX ENCONTRADA")
        print("=" * 50)
        print("\nPara gerar o PDF, instale uma distribuição LaTeX:")
        print("")
        print("  Windows:")
        print("    - MiKTeX: https://miktex.org/download")
        print("    - TeX Live: https://www.tug.org/texlive/")
        print("")
        print("  Linux:")
        print("    sudo apt install texlive-full")
        print("")
        print("  macOS:")
        print("    brew install --cask mactex")
        print("")
        print("Após instalar, reinicie o terminal e execute:")
        print("    python build.py")
        print("")
        print("=" * 50)
        print("Arquivos .tex criados com sucesso.")
        print("O PDF será gerado após instalação do LaTeX.")
        print("=" * 50)
        sys.exit(0)  # Não falhar, apenas avisar
    
    print(f"\nFerramenta: {tool}")
    print("-" * 50)
    
    try:
        if tool == "latexmk":
            result = build_with_latexmk(docs_dir, main_tex)
        else:
            result = build_with_pdflatex(docs_dir, main_tex)
        
        print("-" * 50)
        
        if result.returncode == 0:
            pdf_path = docs_dir / "main.pdf"
            if pdf_path.exists():
                print(f"\n✓ BUILD CONCLUÍDO COM SUCESSO")
                print(f"  PDF gerado: {pdf_path}")
                print(f"  Tamanho: {pdf_path.stat().st_size / 1024:.1f} KB")
            else:
                print(f"\n⚠ Build retornou sucesso mas PDF não encontrado")
                sys.exit(1)
        else:
            print(f"\n✗ BUILD FALHOU (código: {result.returncode})")
            print("  Verifique os logs acima para detalhes do erro.")
            
            # Verificar log
            log_path = docs_dir / "main.log"
            if log_path.exists():
                print(f"\n  Log disponível em: {log_path}")
            
            sys.exit(result.returncode)
            
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
