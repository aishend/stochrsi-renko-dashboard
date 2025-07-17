"""
Executar Testes - Script Principal
=================================

Script para executar diferentes tipos de testes do sistema ATR Renko.
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

def run_all_pairs_test():
    """Executa teste com todos os pares."""
    print("🚀 Executando teste com TODOS os pares...")
    try:
        subprocess.run([sys.executable, "test_all_pairs.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar teste: {e}")
    except FileNotFoundError:
        print("❌ Arquivo test_all_pairs.py não encontrado")

def run_5_pairs_test():
    """Executa o teste com 5 pares."""
    print("🚀 Executando teste com 5 pares...")
    try:
        subprocess.run([sys.executable, "test_5_pairs.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar teste: {e}")
    except FileNotFoundError:
        print("❌ Arquivo test_5_pairs.py não encontrado")

def run_test_dashboard():
    """Executa o dashboard de teste."""
    print("🚀 Executando dashboard de teste...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard_test.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar dashboard: {e}")
    except FileNotFoundError:
        print("❌ Streamlit não encontrado ou dashboard_test.py não encontrado")

def run_main_dashboard():
    """Executa o dashboard principal."""
    print("🚀 Executando dashboard principal...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar dashboard: {e}")
    except FileNotFoundError:
        print("❌ Dashboard principal não encontrado")

def run_atr_test():
    """Executa teste específico do ATR."""
    print("🚀 Executando teste ATR...")
    try:
        subprocess.run([sys.executable, "test_atr_renko.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar teste ATR: {e}")
    except FileNotFoundError:
        print("❌ Arquivo test_atr_renko.py não encontrado")

def show_menu():
    """Mostra o menu de opções."""
    print("\n" + "=" * 60)
    print("🧪 SISTEMA DE TESTES ATR RENKO")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nOpções disponíveis:")
    print("1. 🔬 Teste rápido (5 pares)")
    print("2. 🌐 Teste completo (TODOS os pares)")
    print("3. 📊 Dashboard de teste")
    print("4. 🌐 Dashboard principal")
    print("5. 📈 Teste específico ATR")
    print("6. ❌ Sair")
    print("\n" + "=" * 60)

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Executar testes do sistema ATR Renko")
    parser.add_argument("--test", choices=["5pairs", "allpairs", "dashboard", "main", "atr"], 
                       help="Tipo de teste a executar")
    parser.add_argument("--interactive", action="store_true", 
                       help="Modo interativo")
    
    args = parser.parse_args()
    
    if args.test:
        # Modo não interativo
        if args.test == "5pairs":
            run_5_pairs_test()
        elif args.test == "allpairs":
            run_all_pairs_test()
        elif args.test == "dashboard":
            run_test_dashboard()
        elif args.test == "main":
            run_main_dashboard()
        elif args.test == "atr":
            run_atr_test()
    else:
        # Modo interativo
        while True:
            show_menu()
            
            try:
                choice = input("Escolha uma opção (1-6): ").strip()
                
                if choice == "1":
                    run_5_pairs_test()
                elif choice == "2":
                    run_all_pairs_test()
                elif choice == "3":
                    run_test_dashboard()
                elif choice == "4":
                    run_main_dashboard()
                elif choice == "5":
                    run_atr_test()
                elif choice == "6":
                    print("👋 Saindo...")
                    break
                else:
                    print("❌ Opção inválida. Tente novamente.")
                
                input("\nPressione Enter para continuar...")
                
            except KeyboardInterrupt:
                print("\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
                input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()
