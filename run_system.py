"""
Sistema de Trading Renko - Entrada Principal
===========================================

Execute este arquivo para iniciar o sistema completo.

Opções de uso:
- python run_system.py                    # Dashboard padrão
- python run_system.py --all-pairs       # Dashboard com todos os pares
- python run_system.py --test            # Modo teste (5 pares)
- python run_system.py --analysis        # Análise de todos os pares
- python run_system.py --help            # Ajuda
"""

import sys
import os
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Adiciona o diretório atual ao Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config.settings import setup_logging, validate_api_config

def run_dashboard(all_pairs=False, test_mode=False):
    """Executa o dashboard com diferentes modos."""
    dashboard_path = os.path.join(current_dir, "dashboard", "dashboard.py")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        dashboard_path,
        "--server.headless", "false",
        "--server.runOnSave", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    # Adiciona argumentos específicos para o dashboard
    if all_pairs:
        cmd.extend(["--", "--all-pairs"])
    elif test_mode:
        cmd.extend(["--", "--test-mode"])
    
    subprocess.run(cmd)

def run_analysis():
    """Executa análise de todos os pares."""
    print("🔍 Iniciando análise de todos os pares...")
    
    try:
        from trading_pairs import TRADING_PAIRS
        from src.data.data_manager import get_data_manager
        from src.indicators.renko import gerar_renko
        from src.indicators.stoch_rsi import stochrsi
        import pandas as pd
        from datetime import datetime
        
        data_manager = get_data_manager()
        timeframes = ['1h', '4h', '1d']
        
        print(f"📊 Analisando {len(TRADING_PAIRS)} pares...")
        print(f"⏰ Timeframes: {', '.join(timeframes)}")
        
        results = {}
        
        for i, symbol in enumerate(TRADING_PAIRS, 1):
            print(f"\n[{i}/{len(TRADING_PAIRS)}] Analisando {symbol}...")
            
            symbol_results = {}
            
            for timeframe in timeframes:
                try:
                    # Coleta dados
                    df = data_manager.get_symbol_data(symbol, timeframe)
                    
                    if df.empty:
                        continue
                    
                    # Gera Renko com ATR
                    renko_df = gerar_renko(
                        df, 
                        brick_size=None, 
                        symbol=symbol, 
                        use_atr=True, 
                        atr_period=14
                    )
                    
                    if renko_df.empty:
                        continue
                    
                    # Calcula StochRSI - verifica qual coluna usar
                    close_col = 'Close' if 'Close' in renko_df.columns else 'close'
                    price_col = 'Close' if 'Close' in df.columns else 'close'
                    
                    if close_col not in renko_df.columns:
                        continue
                    
                    stoch = stochrsi(renko_df[close_col])
                    
                    # Verifica sinais
                    if len(stoch) > 0:
                        # stochrsi retorna um DataFrame com colunas 'stochrsi_k' e 'stochrsi_d'
                        # Vamos usar a coluna 'stochrsi_k' para o sinal
                        if 'stochrsi_k' in stoch.columns:
                            last_stoch = stoch['stochrsi_k'].iloc[-1]
                        else:
                            # Fallback para o caso de retorno diferente
                            last_stoch = stoch.iloc[-1, 0] if len(stoch.columns) > 0 else 0
                        
                        signal = "neutro"
                        if pd.notna(last_stoch) and last_stoch > 80:
                            signal = "sobrecompra"
                        elif pd.notna(last_stoch) and last_stoch < 20:
                            signal = "sobrevenda"
                        
                        symbol_results[timeframe] = {
                            'renko_bricks': len(renko_df),
                            'stoch_rsi': last_stoch,
                            'signal': signal,
                            'last_price': df[price_col].iloc[-1] if price_col in df.columns else 0
                        }
                    
                except Exception as e:
                    print(f"   ❌ Erro em {timeframe}: {e}")
                    continue
            
            results[symbol] = symbol_results
        
        # Salva resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_results_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Análise concluída!")
        print(f"📄 Resultados salvos em: {filename}")
        
        # Mostra resumo
        total_analyzed = len([s for s in results.values() if s])
        print(f"📊 Resumo: {total_analyzed}/{len(TRADING_PAIRS)} pares analisados")
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

def show_help():
    """Mostra ajuda sobre o uso."""
    print("""
🚀 Sistema de Trading Renko - Opções de Uso
===========================================

Uso: python run_system.py [opções]

Opções disponíveis:
  --all-pairs       Inicia dashboard com TODOS os pares disponíveis
  --test            Inicia dashboard no modo teste (5 pares)
  --analysis        Executa análise de todos os pares (sem interface)
  --help            Mostra esta ajuda

Exemplos:
  python run_system.py                    # Dashboard padrão
  python run_system.py --all-pairs       # Dashboard com todos os pares
  python run_system.py --test            # Modo teste
  python run_system.py --analysis        # Análise completa

💡 Dicas:
  - Use --all-pairs para análise completa de mercado
  - Use --test para desenvolvimento/debugging
  - Use --analysis para relatórios automatizados
  - O dashboard padrão usa pares configurados em config/settings.py
""")

def main():
    """Função principal do sistema."""
    parser = argparse.ArgumentParser(
        description="Sistema de Trading Renko",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--all-pairs", 
        action="store_true",
        help="Usar todos os pares disponíveis"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Modo teste (5 pares)"
    )
    
    parser.add_argument(
        "--analysis", 
        action="store_true",
        help="Executar análise de todos os pares"
    )
    
    parser.add_argument(
        "--help-extended", 
        action="store_true",
        help="Mostrar ajuda detalhada"
    )
    
    args = parser.parse_args()
    
    # Mostra ajuda extendida
    if args.help_extended:
        show_help()
        return
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Cabeçalho
    print("🚀 Sistema de Trading Renko")
    print("=" * 50)
    
    if args.all_pairs:
        print("🌐 Modo: TODOS OS PARES")
        try:
            from trading_pairs import TRADING_PAIRS
            print(f"📊 {len(TRADING_PAIRS)} pares serão carregados")
        except ImportError:
            print("❌ Arquivo trading_pairs.py não encontrado")
            return
    elif args.test:
        print("🧪 Modo: TESTE (5 pares)")
    elif args.analysis:
        print("🔍 Modo: ANÁLISE COMPLETA")
    else:
        print("📈 Modo: DASHBOARD PADRÃO")
    
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    logger.info("Sistema de trading iniciado")
    
    # Validar configurações
    if not validate_api_config():
        print("❌ Configurações da API não encontradas!")
        print("Configure as variáveis BINANCE_KEY e BINANCE_SECRET ou edite config/settings.py")
        print("\n💡 Execute: python setup.py")
        logger.error("Configurações da API inválidas")
        return
    
    print("✅ Configurações validadas")
    logger.info("Configurações validadas com sucesso")
    
    try:
        if args.analysis:
            # Modo análise
            run_analysis()
        else:
            # Modo dashboard
            if args.all_pairs:
                print("🖥️ Iniciando dashboard com TODOS os pares...")
                print("⚠️  Isso pode demorar mais para carregar...")
            elif args.test:
                print("🖥️ Iniciando dashboard no modo teste...")
            else:
                print("🖥️ Iniciando dashboard...")
            
            print("🌐 O dashboard será aberto no navegador automaticamente...")
            logger.info("Iniciando dashboard")
            
            run_dashboard(all_pairs=args.all_pairs, test_mode=args.test)
        
    except KeyboardInterrupt:
        print("\n👋 Sistema interrompido pelo usuário")
        logger.info("Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        logger.error(f"Erro inesperado: {e}")
        print("\n💡 Alternativamente, execute diretamente:")
        print("   streamlit run dashboard/dashboard.py")

if __name__ == "__main__":
    main()
