"""
ATR (Average True Range) Indicator
=================================

Implementação do indicador ATR para cálculo dinâmico do brick size do Renko.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def calculate_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Calcula o True Range para cada período.
    
    True Range = máx(high - low, |high - close_anterior|, |low - close_anterior|)
    
    Args:
        high: Série de preços máximos
        low: Série de preços mínimos
        close: Série de preços de fechamento
    
    Returns:
        Série com valores de True Range
    """
    try:
        # Garante que as séries têm o mesmo índice
        high = high.reindex(close.index)
        low = low.reindex(close.index)
        
        # Calcula o close anterior
        close_prev = close.shift(1)
        
        # Calcula os três componentes do True Range
        tr1 = high - low  # Range atual
        tr2 = np.abs(high - close_prev)  # |high - close_anterior|
        tr3 = np.abs(low - close_prev)   # |low - close_anterior|
        
        # True Range = máximo dos três componentes
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        return true_range
        
    except Exception as e:
        logger.error(f"Erro ao calcular True Range: {e}")
        return pd.Series(dtype=float)

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcula o ATR (Average True Range) usando a fórmula do TradingView.
    
    ATR = (ATR_anterior * (n-1) + True_Range_atual) / n
    
    Args:
        high: Série de preços máximos
        low: Série de preços mínimos
        close: Série de preços de fechamento
        period: Período para cálculo do ATR (padrão: 14)
    
    Returns:
        Série com valores de ATR
    """
    try:
        # Calcula True Range
        true_range = calculate_true_range(high, low, close)
        
        if true_range.empty:
            logger.warning("True Range vazio - não é possível calcular ATR")
            return pd.Series(dtype=float)
        
        # Inicializa a série ATR
        atr = pd.Series(index=true_range.index, dtype=float)
        
        # Calcula ATR usando a fórmula do TradingView
        # Primeiro valor = média simples dos primeiros 'period' valores de TR
        if len(true_range) >= period:
            atr.iloc[period-1] = true_range.iloc[:period].mean()
            
            # Valores subsequentes usando a fórmula exponencial
            for i in range(period, len(true_range)):
                prev_atr = atr.iloc[i-1]
                current_tr = true_range.iloc[i]
                
                # ATR = (ATR_anterior * (n-1) + TR_atual) / n
                atr.iloc[i] = (prev_atr * (period - 1) + current_tr) / period
        
        return atr
        
    except Exception as e:
        logger.error(f"Erro ao calcular ATR: {e}")
        return pd.Series(dtype=float)

def calculate_atr_from_dataframe(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcula ATR a partir de um DataFrame com dados OHLC.
    
    Args:
        df: DataFrame com colunas 'high', 'low', 'close' (ou variações)
        period: Período para cálculo do ATR (padrão: 14)
    
    Returns:
        Série com valores de ATR
    """
    try:
        # Normaliza nomes das colunas (case-insensitive)
        df_normalized = df.copy()
        
        # Mapeia diferentes variações de nomes de colunas
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['high', 'h', 'max']:
                column_mapping[col] = 'high'
            elif col_lower in ['low', 'l', 'min']:
                column_mapping[col] = 'low'
            elif col_lower in ['close', 'c', 'last']:
                column_mapping[col] = 'close'
        
        df_normalized = df_normalized.rename(columns=column_mapping)
        
        # Verifica se as colunas necessárias estão presentes
        required_columns = ['high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df_normalized.columns]
        
        if missing_columns:
            logger.error(f"Colunas ausentes para cálculo do ATR: {missing_columns}")
            logger.error(f"Colunas disponíveis: {list(df_normalized.columns)}")
            return pd.Series(dtype=float)
        
        # Calcula ATR
        atr = calculate_atr(
            df_normalized['high'],
            df_normalized['low'],
            df_normalized['close'],
            period
        )
        
        return atr
        
    except Exception as e:
        logger.error(f"Erro ao calcular ATR do DataFrame: {e}")
        return pd.Series(dtype=float)

def get_tick_size(symbol: str) -> float:
    """
    Retorna o tick size mínimo para um símbolo.
    
    Args:
        symbol: Símbolo do ativo (ex: 'BTCUSDT')
    
    Returns:
        Tick size mínimo
    """
    # Mapeamento de tick sizes para diferentes tipos de ativos
    tick_sizes = {
        # Criptomoedas principais
        'BTCUSDT': 0.01,
        'ETHUSDT': 0.01,
        'BNBUSDT': 0.01,
        'XRPUSDT': 0.0001,
        'ADAUSDT': 0.0001,
        'SOLUSDT': 0.01,
        'DOGEUSDT': 0.00001,
        'SHIBUSDT': 0.00000001,
        'LINKUSDT': 0.001,
        'DOTUSDT': 0.001,
        'UNIUSDT': 0.001,
        'LTCUSDT': 0.01,
        'BCHUSDT': 0.01,
        'ETCUSDT': 0.001,
        'XLMUSDT': 0.00001,
        'ATOMUSDT': 0.001,
        'FILUSDT': 0.001,
        'TRXUSDT': 0.00001,
        'AVAXUSDT': 0.001,
        'MATICUSDT': 0.0001,
    }
    
    # Retorna tick size específico ou padrão
    return tick_sizes.get(symbol, 0.01)

def calculate_dynamic_brick_size(df: pd.DataFrame, symbol: str, period: int = 14) -> float:
    """
    Calcula o brick size dinâmico baseado no ATR, seguindo o método do TradingView.
    
    Args:
        df: DataFrame com dados OHLC
        symbol: Símbolo do ativo
        period: Período para cálculo do ATR (padrão: 14)
    
    Returns:
        Brick size calculado baseado no ATR
    """
    try:
        # Calcula ATR
        atr = calculate_atr_from_dataframe(df, period)
        
        if atr.empty or atr.isna().all():
            logger.warning(f"ATR vazio para {symbol} - usando brick size padrão")
            return 100.0  # Valor padrão de fallback
        
        # Pega o último valor válido do ATR
        last_atr = atr.dropna().iloc[-1] if not atr.dropna().empty else 100.0
        
        # Obtém o tick size mínimo do ativo
        tick_size = get_tick_size(symbol)
        
        # Arredonda o ATR para o tick size mínimo
        brick_size = round(last_atr / tick_size) * tick_size
        
        # Garante um valor mínimo
        min_brick_size = tick_size * 10  # Pelo menos 10 ticks
        brick_size = max(brick_size, min_brick_size)
        
        logger.info(f"Brick size calculado para {symbol}: ATR={last_atr:.6f}, Tick={tick_size}, Brick={brick_size:.6f}")
        
        return brick_size
        
    except Exception as e:
        logger.error(f"Erro ao calcular brick size dinâmico para {symbol}: {e}")
        return 100.0  # Valor padrão de fallback

def get_atr_brick_size_with_fallback(df: pd.DataFrame, symbol: str, period: int = 14, fallback_timeframes: list = None) -> float:
    """
    Calcula brick size baseado no ATR com fallback para timeframes maiores se necessário.
    
    Args:
        df: DataFrame com dados OHLC
        symbol: Símbolo do ativo
        period: Período para cálculo do ATR
        fallback_timeframes: Lista de timeframes para fallback (não implementado ainda)
    
    Returns:
        Brick size calculado
    """
    try:
        # Verifica se há dados suficientes para calcular ATR
        if len(df) < period:
            logger.warning(f"Dados insuficientes para ATR ({len(df)} < {period}) - usando brick size padrão")
            return 100.0
        
        # Calcula brick size baseado no ATR
        brick_size = calculate_dynamic_brick_size(df, symbol, period)
        
        return brick_size
        
    except Exception as e:
        logger.error(f"Erro ao calcular brick size com fallback: {e}")
        return 100.0

# Função de conveniência para compatibilidade
def get_atr_brick_size(df: pd.DataFrame, symbol: str = "BTCUSDT", period: int = 14) -> float:
    """
    Função de conveniência para calcular brick size baseado no ATR.
    
    Args:
        df: DataFrame com dados OHLC
        symbol: Símbolo do ativo (padrão: BTCUSDT)
        period: Período para cálculo do ATR (padrão: 14)
    
    Returns:
        Brick size calculado
    """
    return get_atr_brick_size_with_fallback(df, symbol, period)
