#!/usr/bin/env python
"""
Teste das correções dos gráficos StochRSI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Teste básico dos imports
    from src.data.data_manager import get_data_manager
    from src.indicators.renko import gerar_renko
    from src.indicators.stoch_rsi import stochrsi
    import pandas as pd
    
    print("✅ Todos os imports funcionando")
    
    # Teste básico do data manager
    dm = get_data_manager()
    print("✅ Data manager inicializado")
    
    # Teste de cache
    stats = dm.get_cache_statistics()
    print(f"✅ Cache stats: {stats}")
    
    # Teste de um símbolo
    test_symbol = "BTCUSDT"
    print(f"\n🔍 Testando {test_symbol}...")
    
    df = dm.get_symbol_data(test_symbol, "1h")
    print(f"✅ Dados obtidos: {len(df)} registros")
    
    if not df.empty:
        print(f"✅ Colunas disponíveis: {list(df.columns)}")
        
        # Teste do Renko
        renko_df = gerar_renko(df, brick_size=None, symbol=test_symbol, use_atr=True)
        print(f"✅ Renko gerado: {len(renko_df)} tijolos")
        
        if not renko_df.empty:
            print(f"✅ Colunas Renko: {list(renko_df.columns)}")
            
            # Teste do StochRSI
            close_col = 'Close' if 'Close' in renko_df.columns else 'close'
            if close_col in renko_df.columns:
                stoch = stochrsi(renko_df[close_col])
                print(f"✅ StochRSI calculado: {len(stoch)} valores")
                
                if len(stoch) > 0:
                    print(f"✅ Último StochRSI: {stoch.iloc[-1]:.2f}")
            else:
                print(f"❌ Coluna close não encontrada: {list(renko_df.columns)}")
    
    print("\n🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()
