"""
Início Rápido do Dashboard
==========================

Script para iniciar o dashboard rapidamente.
"""

import os
import sys
import subprocess

def main():
    """Inicia o dashboard."""
    print("🚀 Iniciando Dashboard de Trading Renko...")
    
    # Verifica se está no diretório correto
    if not os.path.exists("dashboard/dashboard.py"):
        print("❌ Erro: Execute este script a partir do diretório raiz do projeto")
        return
    
    # Adiciona informações sobre as novas funcionalidades
    print("📊 Características do dashboard atualizado:")
    print("- ✅ Matriz com pares nas linhas e timeframes nas colunas")
    print("- ✅ Cálculo automático de dias de histórico por timeframe")
    print("- ✅ Renko usado para todos os timeframes")
    print("- ✅ Multithreading para busca rápida de dados")
    print("- ✅ Cache inteligente por timeframe")
    print("- ✅ Filtros avançados 'Todos TF > Limite'")
    print("- ✅ Sinais coloridos (Oversold, Overbought, Bullish, Bearish)")
    print("- ✅ Estatísticas resumidas por timeframe")
    print("- ✅ Limpeza automática de cache")
    
    print("\n🌐 Abrindo dashboard no navegador...")
    
    try:
        # Inicia o Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard/dashboard.py",
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar dashboard: {e}")
        print("\n💡 Tente executar manualmente:")
        print("   streamlit run dashboard/dashboard.py")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
