"""
Teste Rápido - Principais Pares
===============================

Script para testar rapidamente os principais pares de criptomoedas.
"""

import sys
import os
import time
import logging
import pandas as pd
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.data.data_manager import get_data_manager
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from config.settings import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def test_main_pairs():
    """Testa os principais pares de criptomoedas."""
    
    # Principais pares com maior volume
    MAIN_PAIRS = [
        'BTCUSDT',
        'ETHUSDT', 
        'BNBUSDT',
        'SOLUSDT',
        'XRPUSDT',
        'ADAUSDT',
        'DOGEUSDT',
        'AVAXUSDT',
        'LINKUSDT',
        'DOTUSDT'
    ]
    
    print("🚀 TESTE RÁPIDO - PRINCIPAIS PARES")
    print("=" * 50)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Pares selecionados: {len(MAIN_PAIRS)}")
    print(f"⏰ Timeframes: 1h, 4h, 1d")
    print("=" * 50)
    
    data_manager = get_data_manager()
    timeframes = ['1h', '4h', '1d']
    
    results = {
        'success': 0,
        'errors': 0,
        'total': 0,
        'pairs_data': {}
    }
    
    for i, symbol in enumerate(MAIN_PAIRS, 1):
        print(f"\n[{i}/{len(MAIN_PAIRS)}] 📊 Testando {symbol}...")
        
        symbol_results = {}
        symbol_success = False
        
        for timeframe in timeframes:
            try:
                # Coleta dados
                df = data_manager.get_symbol_data(symbol, timeframe, force_cache=False)
                
                if df.empty:
                    print(f"   ❌ {timeframe}: Sem dados")
                    continue
                
                # Calcula brick_size apropriado baseado na volatilidade
                price = df['close'].iloc[-1]
                volatility = df['close'].pct_change().std()
                
                # Brick size adaptativo: 0.5% para alta volatilidade, 1% para baixa
                if volatility > 0.05:  # Alta volatilidade
                    brick_size = price * 0.005
                elif volatility > 0.02:  # Média volatilidade
                    brick_size = price * 0.01
                else:  # Baixa volatilidade
                    brick_size = price * 0.02
                
                # Gera Renko com brick_size fixo
                renko_df = gerar_renko(
                    df, 
                    brick_size=brick_size, 
                    symbol=symbol, 
                    use_atr=False
                )
                
                if renko_df.empty:
                    print(f"   ❌ {timeframe}: Erro ao gerar Renko")
                    continue
                
                # Verifica se há tijolos suficientes
                min_bricks_needed = 34
                if len(renko_df) < min_bricks_needed:
                    # Tenta com brick_size menor
                    brick_size_small = price * 0.001  # 0.1% do preço
                    renko_df = gerar_renko(
                        df, 
                        brick_size=brick_size_small, 
                        symbol=symbol, 
                        use_atr=False
                    )
                    
                    if len(renko_df) < min_bricks_needed:
                        print(f"   ⚠️  {timeframe}: {len(renko_df)} tijolos (< {min_bricks_needed} necessários)")
                        continue
                
                # Calcula StochRSI
                stoch_df = stochrsi(renko_df['close'])
                
                if not stoch_df.empty and len(stoch_df) > 0:
                    # Pega o último valor de %K
                    last_stoch = stoch_df['stochrsi_k'].iloc[-1]
                    
                    if not pd.isna(last_stoch):
                        # Determina sinal
                        if last_stoch > 80:
                            signal = "🔴 sobrecompra"
                            signal_emoji = "🔴"
                        elif last_stoch < 20:
                            signal = "🟢 sobrevenda"
                            signal_emoji = "🟢"
                        else:
                            signal = "🟡 neutro"
                            signal_emoji = "🟡"
                        
                        print(f"   ✅ {timeframe}: {len(renko_df)} tijolos, StochRSI={last_stoch:.1f} {signal_emoji}")
                        
                        symbol_results[timeframe] = {
                            'bricks': len(renko_df),
                            'stoch_rsi': last_stoch,
                            'signal': signal,
                            'brick_size': brick_size,
                            'price': price
                        }
                        
                        symbol_success = True
                    else:
                        print(f"   ❌ {timeframe}: StochRSI inválido")
                else:
                    print(f"   ❌ {timeframe}: Erro no StochRSI")
                
            except Exception as e:
                print(f"   ❌ {timeframe}: Erro - {str(e)[:30]}...")
                continue
        
        # Contabiliza resultados
        results['total'] += 1
        if symbol_success:
            results['success'] += 1
            results['pairs_data'][symbol] = symbol_results
        else:
            results['errors'] += 1
        
        # Delay entre pares
        time.sleep(0.2)
    
    # Mostra resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DO TESTE")
    print("=" * 50)
    print(f"✅ Pares com sucesso: {results['success']}")
    print(f"❌ Pares com erro: {results['errors']}")
    print(f"📈 Taxa de sucesso: {(results['success']/results['total']*100):.1f}%")
    
    # Mostra sinais interessantes
    print("\n🎯 SINAIS IDENTIFICADOS:")
    for symbol, data in results['pairs_data'].items():
        print(f"\n📊 {symbol}:")
        for timeframe, info in data.items():
            stoch_val = info['stoch_rsi']
            signal = info['signal']
            print(f"   {timeframe}: StochRSI={stoch_val:.1f} {signal}")
    
    print("\n" + "=" * 50)
    print("✅ TESTE RÁPIDO CONCLUÍDO!")
    print("=" * 50)
    
    return results

def main():
    """Função principal."""
    try:
        results = test_main_pairs()
        
        # Salva resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_main_pairs_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Teste Principais Pares - {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("RESUMO:\n")
            f.write(f"Total de pares: {results['total']}\n")
            f.write(f"Pares com sucesso: {results['success']}\n")
            f.write(f"Pares com erro: {results['errors']}\n")
            f.write(f"Taxa de sucesso: {(results['success']/results['total']*100):.1f}%\n\n")
            
            f.write("SINAIS IDENTIFICADOS:\n")
            for symbol, data in results['pairs_data'].items():
                f.write(f"\n{symbol}:\n")
                for timeframe, info in data.items():
                    stoch_val = info['stoch_rsi']
                    signal = info['signal']
                    bricks = info['bricks']
                    f.write(f"  {timeframe}: StochRSI={stoch_val:.1f} {signal} ({bricks} tijolos)\n")
        
        print(f"📄 Resultados salvos em: {filename}")
        
    except KeyboardInterrupt:
        print("\n👋 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        logger.error(f"Erro no teste: {e}")

if __name__ == "__main__":
    main()
