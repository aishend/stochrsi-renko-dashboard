"""
Timeframe Utilities
==================

Utilitários para trabalhar com timeframes e fallback automático.
"""

import pandas as pd
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Mapeamento de timeframes para minutos
TIMEFRAME_MINUTES = {
    '1m': 1,
    '3m': 3,
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '2h': 120,
    '4h': 240,
    '6h': 360,
    '8h': 480,
    '12h': 720,
    '1d': 1440,
    '3d': 4320,
    '1w': 10080,
    '1M': 43200,  # Aproximadamente 30 dias
}

# Sequência de fallback para timeframes maiores
FALLBACK_SEQUENCE = [
    '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
]

def get_timeframe_minutes(timeframe: str) -> int:
    """
    Retorna o número de minutos para um timeframe.
    
    Args:
        timeframe: String do timeframe (ex: '1h', '15m', '1d')
    
    Returns:
        Número de minutos
    """
    return TIMEFRAME_MINUTES.get(timeframe, 60)  # Default para 1h

def get_next_timeframe(current_timeframe: str) -> Optional[str]:
    """
    Retorna o próximo timeframe maior na sequência de fallback.
    
    Args:
        current_timeframe: Timeframe atual
    
    Returns:
        Próximo timeframe maior ou None se não existir
    """
    try:
        current_index = FALLBACK_SEQUENCE.index(current_timeframe)
        if current_index < len(FALLBACK_SEQUENCE) - 1:
            return FALLBACK_SEQUENCE[current_index + 1]
        return None
    except ValueError:
        logger.warning(f"Timeframe desconhecido: {current_timeframe}")
        return None

def get_fallback_timeframes(original_timeframe: str, max_fallbacks: int = 3) -> List[str]:
    """
    Retorna uma lista de timeframes de fallback.
    
    Args:
        original_timeframe: Timeframe original
        max_fallbacks: Número máximo de fallbacks
    
    Returns:
        Lista de timeframes de fallback
    """
    fallbacks = []
    current = original_timeframe
    
    for _ in range(max_fallbacks):
        next_tf = get_next_timeframe(current)
        if next_tf:
            fallbacks.append(next_tf)
            current = next_tf
        else:
            break
    
    return fallbacks

def resample_ohlc_data(df: pd.DataFrame, target_timeframe: str, original_timeframe: str) -> pd.DataFrame:
    """
    Resample dados OHLC para um timeframe maior.
    
    Args:
        df: DataFrame com dados OHLC
        target_timeframe: Timeframe alvo
        original_timeframe: Timeframe original
    
    Returns:
        DataFrame com dados resampled
    """
    try:
        if df.empty:
            return pd.DataFrame()
        
        # Garante que o index é datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                logger.error("Não foi possível encontrar coluna de data para resample")
                return pd.DataFrame()
        
        # Mapeia timeframes para pandas resample
        timeframe_map = {
            '1m': '1min',
            '3m': '3min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1H',
            '2h': '2H',
            '4h': '4H',
            '6h': '6H',
            '8h': '8H',
            '12h': '12H',
            '1d': '1D',
            '3d': '3D',
            '1w': '1W',
            '1M': '1M'
        }
        
        target_rule = timeframe_map.get(target_timeframe, '1H')
        
        # Resample OHLC
        resampled = df.resample(target_rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum' if 'volume' in df.columns else 'last'
        }).dropna()
        
        logger.info(f"Resample {original_timeframe} -> {target_timeframe}: {len(df)} -> {len(resampled)} períodos")
        
        return resampled
        
    except Exception as e:
        logger.error(f"Erro ao fazer resample de {original_timeframe} para {target_timeframe}: {e}")
        return pd.DataFrame()

def extend_data_with_fallback(df: pd.DataFrame, symbol: str, original_timeframe: str, 
                             min_periods: int = 50, max_fallbacks: int = 3) -> pd.DataFrame:
    """
    Estende dados usando fallback para timeframes maiores se necessário.
    
    Args:
        df: DataFrame original
        symbol: Símbolo do ativo
        original_timeframe: Timeframe original
        min_periods: Número mínimo de períodos necessários
        max_fallbacks: Número máximo de fallbacks a tentar
    
    Returns:
        DataFrame estendido
    """
    try:
        if len(df) >= min_periods:
            logger.debug(f"Dados suficientes para {symbol} {original_timeframe}: {len(df)} períodos")
            return df
        
        logger.warning(f"Dados insuficientes para {symbol} {original_timeframe}: {len(df)} < {min_periods}")
        
        # Tenta fallback para timeframes maiores
        fallback_timeframes = get_fallback_timeframes(original_timeframe, max_fallbacks)
        
        for fallback_tf in fallback_timeframes:
            logger.info(f"Tentando fallback para {fallback_tf}")
            
            # Simula dados estendidos usando resample
            # Na implementação real, isso deveria buscar dados do timeframe maior
            extended_df = resample_ohlc_data(df, fallback_tf, original_timeframe)
            
            if len(extended_df) >= min_periods:
                logger.info(f"Fallback bem-sucedido para {fallback_tf}: {len(extended_df)} períodos")
                return extended_df
            
            logger.warning(f"Fallback para {fallback_tf} ainda insuficiente: {len(extended_df)} períodos")
        
        # Se nenhum fallback funcionou, retorna os dados originais
        logger.warning(f"Nenhum fallback foi suficiente para {symbol}, usando dados disponíveis")
        return df
        
    except Exception as e:
        logger.error(f"Erro no fallback para {symbol} {original_timeframe}: {e}")
        return df

def calculate_projection_brick_size(df: pd.DataFrame, symbol: str, atr_period: int = 14) -> float:
    """
    Calcula brick size projetado para uso em tempo real.
    
    Args:
        df: DataFrame com dados OHLC
        symbol: Símbolo do ativo
        atr_period: Período do ATR
    
    Returns:
        Brick size projetado
    """
    try:
        from ..indicators.atr import calculate_dynamic_brick_size
        
        # Para projeção em tempo real, usa apenas dados confirmados
        # Remove a última barra se ela ainda não foi confirmada
        if len(df) > 1:
            confirmed_df = df.iloc[:-1]  # Remove última barra não confirmada
        else:
            confirmed_df = df
        
        # Calcula brick size baseado nos dados confirmados
        projected_size = calculate_dynamic_brick_size(confirmed_df, symbol, atr_period)
        
        logger.debug(f"Brick size projetado para {symbol}: {projected_size}")
        return projected_size
        
    except Exception as e:
        logger.error(f"Erro ao calcular brick size projetado para {symbol}: {e}")
        return 100.0  # Fallback
