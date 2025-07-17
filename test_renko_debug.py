"""
Teste Rápido Renko
==================

Teste simples para verificar formato das colunas do DataFrame Renko.
"""

import sys
import os
import pandas as pd

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.data.data_manager import get_data_manager
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from config.settings import setup_logging

# Configurar logging
setup_logging()

def test_renko_columns():
    """Testa as colunas do DataFrame Renko."""
    print("🔍 Testando colunas do DataFrame Renko...")
    
    data_manager = get_data_manager()
    symbol = "BTCUSDT"
    timeframe = "1h"
    
    # Coleta dados
    df = data_manager.get_symbol_data(symbol, timeframe, force_cache=False)
    
    if df.empty:
        print("❌ Sem dados para teste")
        return
    
    print(f"📊 Dados originais - Colunas: {list(df.columns)}")
    print(f"📊 Dados originais - Index: {df.index.name}")
    print(f"📊 Primeiras linhas:")
    print(df.head(2))
    
    # Gera Renko
    renko_df = gerar_renko(df, brick_size=None, symbol=symbol, use_atr=True, atr_period=14)
    
    if renko_df.empty:
        print("❌ Erro ao gerar Renko")
        return
    
    print(f"\n📊 Renko gerado - Colunas: {list(renko_df.columns)}")
    print(f"📊 Renko gerado - Index: {renko_df.index.name}")
    print(f"📊 Primeiras linhas:")
    print(renko_df.head(2))
    
    # Testa StochRSI
    if 'close' in renko_df.columns:
        print(f"\n✅ Coluna 'close' encontrada")
        stoch_df = stochrsi(renko_df['close'])
        print(f"📊 StochRSI - Colunas: {list(stoch_df.columns)}")
        print(f"📊 StochRSI - Últimos valores:")
        print(stoch_df.tail(2))
    else:
        print(f"\n❌ Coluna 'close' não encontrada")
        print(f"Colunas disponíveis: {list(renko_df.columns)}")
        
        # Tenta encontrar coluna similar
        for col in renko_df.columns:
            if 'close' in col.lower():
                print(f"✅ Coluna similar encontrada: {col}")
                stoch_df = stochrsi(renko_df[col])
                print(f"📊 StochRSI - Colunas: {list(stoch_df.columns)}")
                print(f"📊 StochRSI - Últimos valores:")
                print(stoch_df.tail(2))
                break

if __name__ == "__main__":
    test_renko_columns()
