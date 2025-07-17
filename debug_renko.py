"""
Debug do problema com Renko - Verificar formato dos dados
"""

import pandas as pd
import logging
import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.api.binance_client import get_futures_klines
from src.indicators.renko import gerar_renko
from config.settings import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def debug_data_format():
    """Debug do formato dos dados"""
    
    # Teste com AINUSDT 4h (que está dando erro)
    symbol = "AINUSDT"
    interval = "4h"
    
    print(f"\n=== DEBUG: {symbol} {interval} ===")
    
    # Obtém dados
    start_time = datetime.now() - timedelta(days=30)
    start_timestamp = int(start_time.timestamp() * 1000)
    
    print(f"Buscando dados históricos para {symbol} {interval}...")
    
    try:
        df = get_futures_klines(symbol, interval, start_timestamp)
        
        print(f"Dados obtidos: {len(df)} registros")
        print(f"Colunas: {list(df.columns)}")
        print(f"Tipos de dados: {df.dtypes}")
        print(f"Index: {df.index}")
        print(f"Index name: {df.index.name}")
        
        if len(df) > 0:
            print(f"\nPrimeiros 5 registros:")
            print(df.head())
            
            print(f"\nÚltimos 5 registros:")
            print(df.tail())
            
            # Teste de conversão para Renko
            print(f"\n=== TESTE RENKO ===")
            
            # Verifica se tem todas as colunas necessárias
            required_columns = ['Open', 'High', 'Low', 'Close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Colunas ausentes: {missing_columns}")
                print(f"   Colunas disponíveis: {list(df.columns)}")
            else:
                print(f"✅ Todas as colunas necessárias estão presentes")
                
                # Prepara dados para Renko
                renko_df = df.reset_index()
                
                print(f"\nDados após reset_index:")
                print(f"Colunas: {list(renko_df.columns)}")
                print(f"Primeiros 3 registros:")
                print(renko_df.head(3))
                
                # Verifica se precisa renomear colunas
                if 'Time' in renko_df.columns:
                    renko_df.rename(columns={'Time': 'date'}, inplace=True)
                    print(f"Renomeou 'Time' para 'date'")
                elif renko_df.index.name:
                    renko_df['date'] = renko_df.index
                    print(f"Adicionou coluna 'date' do index")
                
                # Normaliza nomes das colunas para minúsculas
                renko_df.columns = [col.lower() for col in renko_df.columns]
                
                print(f"\nDados após normalização:")
                print(f"Colunas: {list(renko_df.columns)}")
                print(f"Primeiros 3 registros:")
                print(renko_df.head(3))
                
                # Verifica colunas necessárias
                required_columns = ['date', 'open', 'high', 'low', 'close']
                missing_columns = [col for col in required_columns if col not in renko_df.columns]
                
                if missing_columns:
                    print(f"❌ Colunas ausentes após normalização: {missing_columns}")
                else:
                    print(f"✅ Todas as colunas necessárias estão presentes após normalização")
                    
                    # Testa gerar_renko
                    print(f"\n=== TESTANDO GERAR_RENKO ===")
                    
                    try:
                        renko_data = gerar_renko(df, 1000)
                        
                        if renko_data.empty:
                            print(f"❌ Renko retornou DataFrame vazio")
                        else:
                            print(f"✅ Renko gerou {len(renko_data)} tijolos")
                            print(f"Colunas Renko: {list(renko_data.columns)}")
                            print(f"Primeiros 3 tijolos:")
                            print(renko_data.head(3))
                            
                    except Exception as e:
                        print(f"❌ Erro ao gerar Renko: {e}")
                        import traceback
                        traceback.print_exc()
                    
        else:
            print("❌ Nenhum dado retornado")
            
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_format()
