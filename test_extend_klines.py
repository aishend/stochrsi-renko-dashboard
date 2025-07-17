#!/usr/bin/env python3
"""
Teste do sistema extend klines
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from src.data.data_manager import get_data_manager
from src.api.binance_client import extend_klines_to_current

def test_extend_klines():
    """Testa o sistema de extend klines"""
    
    print("🚀 Testando sistema extend klines")
    print("=" * 50)
    
    # Inicializa o data manager
    dm = get_data_manager()
    
    # Testa com um símbolo
    symbol = "BTCUSDT"
    interval = "1h"
    
    print(f"📊 Testando {symbol} {interval}")
    
    try:
        # Busca dados sem extend
        print("\n1. Buscando dados sem extend:")
        data_no_extend = dm.get_symbol_data(symbol, interval, extend_to_current=False)
        
        if not data_no_extend.empty:
            print(f"   ✅ Dados obtidos: {len(data_no_extend)} candles")
            print(f"   📅 Último candle: {data_no_extend.index[-1]}")
            
            # Calcula diferença para agora
            now = datetime.now()
            last_candle = data_no_extend.index[-1]
            if hasattr(last_candle, 'to_pydatetime'):
                last_candle = last_candle.to_pydatetime()
            
            diff = (now - last_candle).total_seconds() / 3600  # diferença em horas
            print(f"   ⏰ Diferença para agora: {diff:.2f} horas")
            
            # Busca dados com extend
            print("\n2. Buscando dados com extend:")
            data_with_extend = dm.get_symbol_data(symbol, interval, extend_to_current=True)
            
            if not data_with_extend.empty:
                print(f"   ✅ Dados obtidos: {len(data_with_extend)} candles")
                print(f"   📅 Último candle: {data_with_extend.index[-1]}")
                
                # Calcula diferença para agora
                last_candle_extended = data_with_extend.index[-1]
                if hasattr(last_candle_extended, 'to_pydatetime'):
                    last_candle_extended = last_candle_extended.to_pydatetime()
                
                diff_extended = (now - last_candle_extended).total_seconds() / 3600
                print(f"   ⏰ Diferença para agora: {diff_extended:.2f} horas")
                
                # Mostra diferença
                new_candles = len(data_with_extend) - len(data_no_extend)
                print(f"   🆕 Novos candles adicionados: {new_candles}")
                
                if new_candles > 0:
                    print("   ✅ Extend klines funcionando!")
                    
                    # Mostra os últimos candles
                    print("\n📈 Últimos 5 candles:")
                    print(data_with_extend.tail().to_string())
                else:
                    print("   ℹ️  Dados já estavam atualizados")
            else:
                print("   ❌ Erro ao buscar dados com extend")
        else:
            print("   ❌ Erro ao buscar dados sem extend")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extend_klines()
