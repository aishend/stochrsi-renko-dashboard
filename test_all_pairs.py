"""
Teste com Todos os Pares
========================

Script para testar o sistema ATR Renko com todos os pares disponíveis.
"""

import sys
import os
import time
import logging
import pandas as pd
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from trading_pairs import TRADING_PAIRS
from src.data.data_manager import get_data_manager
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from config.settings import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def test_all_pairs():
    """Testa o sistema com todos os pares disponíveis."""
    print("🚀 INICIANDO TESTE COM TODOS OS PARES")
    print("=" * 60)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total de pares: {len(TRADING_PAIRS)}")
    print(f"⏰ Timeframes: 1h, 4h, 1d")
    print("=" * 60)
    
    data_manager = get_data_manager()
    timeframes = ['1h', '4h', '1d']
    
    results = {
        'success': 0,
        'errors': 0,
        'total': 0,
        'pairs_with_data': [],
        'pairs_with_errors': []
    }
    
    # Testa cada par
    for i, symbol in enumerate(TRADING_PAIRS, 1):
        print(f"\n[{i}/{len(TRADING_PAIRS)}] Testando {symbol}...")
        
        symbol_success = False
        
        for timeframe in timeframes:
            try:
                # Coleta dados
                df = data_manager.get_symbol_data(symbol, timeframe, force_cache=False)
                
                if df.empty:
                    print(f"   ❌ {timeframe}: Sem dados")
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
                    print(f"   ❌ {timeframe}: Erro ao gerar Renko")
                    continue
                
                # Verifica se há tijolos suficientes para StochRSI
                min_bricks_needed = 34  # RSI:14 + Stoch:14 + K:3 + D:3
                if len(renko_df) < min_bricks_needed:
                    print(f"   ⚠️  {timeframe}: {len(renko_df)} tijolos (< {min_bricks_needed} necessários para StochRSI)")
                    
                    # Tenta com brick_size menor para gerar mais tijolos
                    brick_size_small = df['close'].iloc[-1] * 0.001  # 0.1% do preço
                    renko_df_small = gerar_renko(
                        df, 
                        brick_size=brick_size_small, 
                        symbol=symbol, 
                        use_atr=False
                    )
                    
                    if len(renko_df_small) >= min_bricks_needed:
                        renko_df = renko_df_small
                        print(f"   🔧 {timeframe}: Usando brick_size menor: {len(renko_df)} tijolos")
                    else:
                        print(f"   ❌ {timeframe}: Mesmo com brick_size menor: {len(renko_df_small)} tijolos")
                        continue
                
                # Debug: verifica as colunas do DataFrame Renko
                print(f"   🔍 {timeframe}: {len(renko_df)} tijolos, Colunas: {list(renko_df.columns)}")
                
                # Verifica se tem coluna 'close' (pode ser 'Close' ou outra variação)
                close_col = None
                for col in renko_df.columns:
                    if col.lower() == 'close':
                        close_col = col
                        break
                
                if close_col is None:
                    print(f"   ❌ {timeframe}: Coluna 'close' não encontrada nas colunas: {list(renko_df.columns)}")
                    continue
                
                # Calcula StochRSI
                stoch_df = stochrsi(renko_df[close_col])
                
                if not stoch_df.empty and len(stoch_df) > 0:
                    # Pega o último valor de %K
                    last_stoch = stoch_df['stochrsi_k'].iloc[-1]
                    
                    # Só processa se o valor for válido
                    if not pd.isna(last_stoch):
                        # Determina sinal
                        signal = "neutro"
                        if last_stoch > 80:
                            signal = "🔴 sobrecompra"
                        elif last_stoch < 20:
                            signal = "🟢 sobrevenda"
                        else:
                            signal = "🟡 neutro"
                        
                        print(f"   ✅ {timeframe}: {len(renko_df)} tijolos, StochRSI={last_stoch:.1f} ({signal})")
                        symbol_success = True
                    else:
                        print(f"   ❌ {timeframe}: StochRSI inválido")
                else:
                    print(f"   ❌ {timeframe}: Erro no StochRSI")
                
            except Exception as e:
                print(f"   ❌ {timeframe}: Erro - {str(e)[:50]}...")
                continue
        
        # Contabiliza resultados
        results['total'] += 1
        if symbol_success:
            results['success'] += 1
            results['pairs_with_data'].append(symbol)
        else:
            results['errors'] += 1
            results['pairs_with_errors'].append(symbol)
        
        # Delay entre pares para evitar rate limiting
        time.sleep(0.1)
    
    # Mostra resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE")
    print("=" * 60)
    print(f"✅ Pares com sucesso: {results['success']}")
    print(f"❌ Pares com erro: {results['errors']}")
    print(f"📈 Taxa de sucesso: {(results['success']/results['total']*100):.1f}%")
    
    print(f"\n🎯 Top 10 pares com dados:")
    for i, pair in enumerate(results['pairs_with_data'][:10], 1):
        print(f"   {i:2d}. {pair}")
    
    if results['pairs_with_errors']:
        print(f"\n⚠️  Pares com problemas ({len(results['pairs_with_errors'])}):")
        for i, pair in enumerate(results['pairs_with_errors'][:5], 1):
            print(f"   {i}. {pair}")
        if len(results['pairs_with_errors']) > 5:
            print(f"   ... e mais {len(results['pairs_with_errors']) - 5} pares")
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 60)
    
    return results

def main():
    """Função principal."""
    try:
        results = test_all_pairs()
        
        # Salva resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_all_pairs_results_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"Teste de Todos os Pares - {datetime.now()}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total de pares: {len(TRADING_PAIRS)}\n")
            f.write(f"Pares com sucesso: {results['success']}\n")
            f.write(f"Pares com erro: {results['errors']}\n")
            f.write(f"Taxa de sucesso: {(results['success']/results['total']*100):.1f}%\n\n")
            
            f.write("Pares com dados:\n")
            for pair in results['pairs_with_data']:
                f.write(f"  - {pair}\n")
            
            f.write(f"\nPares com problemas:\n")
            for pair in results['pairs_with_errors']:
                f.write(f"  - {pair}\n")
        
        print(f"📄 Resultados salvos em: {filename}")
        
    except KeyboardInterrupt:
        print("\n👋 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        logger.error(f"Erro no teste: {e}")

if __name__ == "__main__":
    main()
