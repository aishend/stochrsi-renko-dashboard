"""
StochRSI Indicator
==================

Implementação do indicador StochRSI para análise técnica.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Tuple

from config.settings import INDICATOR_CONFIG

logger = logging.getLogger(__name__)

class StochRSIIndicator:
    """
    Classe para calcular o indicador StochRSI.
    """
    
    def __init__(self, 
                 rsi_period: int = None,
                 stoch_period: int = None,
                 k_period: int = None,
                 d_period: int = None):
        """
        Inicializa o indicador StochRSI.
        
        Args:
            rsi_period: Período do RSI (padrão: 14)
            stoch_period: Período do Stochastic (padrão: 14)
            k_period: Período de suavização do %K (padrão: 3)
            d_period: Período de suavização do %D (padrão: 3)
        """
        config = INDICATOR_CONFIG['stoch_rsi']
        
        self.rsi_period = rsi_period or config['period']
        self.stoch_period = stoch_period or config['stoch_period']
        self.k_period = k_period or config['k_period']
        self.d_period = d_period or config['d_period']
        
        logger.info(f"StochRSI configurado: RSI({self.rsi_period}), "
                   f"Stoch({self.stoch_period}), K({self.k_period}), D({self.d_period})")
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """
        Calcula o RSI (Relative Strength Index).
        
        Args:
            prices: Série de preços
        
        Returns:
            Série com valores RSI
        """
        try:
            if len(prices) < self.rsi_period:
                logger.warning(f"Dados insuficientes para RSI: {len(prices)} < {self.rsi_period}")
                return pd.Series(index=prices.index, dtype=float)
            
            # Calcula as diferenças
            delta = prices.diff()
            
            # Separa ganhos e perdas
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calcula médias móveis
            avg_gains = gains.rolling(window=self.rsi_period).mean()
            avg_losses = losses.rolling(window=self.rsi_period).mean()
            
            # Calcula RS e RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_stochrsi(self, prices: pd.Series) -> pd.DataFrame:
        """
        Calcula o StochRSI.
        
        Args:
            prices: Série de preços
        
        Returns:
            DataFrame com %K e %D do StochRSI
        """
        try:
            # Calcula dados mínimos necessários
            min_data_required = self.rsi_period + self.stoch_period + self.k_period + self.d_period
            
            if len(prices) < min_data_required:
                logger.warning(f"Dados insuficientes para StochRSI: {len(prices)} < {min_data_required} "
                              f"(RSI:{self.rsi_period} + Stoch:{self.stoch_period} + K:{self.k_period} + D:{self.d_period})")
                logger.warning(f"Considere aumentar o período de coleta de dados ou usar brick_size menor no Renko")
                return pd.DataFrame(index=prices.index, columns=['stochrsi_k', 'stochrsi_d'])
            
            # Calcula RSI
            rsi_values = self.calculate_rsi(prices)
            
            # Calcula Stochastic do RSI
            min_rsi = rsi_values.rolling(window=self.stoch_period).min()
            max_rsi = rsi_values.rolling(window=self.stoch_period).max()
            
            # Evita divisão por zero
            range_rsi = max_rsi - min_rsi
            stoch_rsi = np.where(range_rsi != 0, 
                               (rsi_values - min_rsi) / range_rsi, 
                               0)
            
            # Suaviza %K e %D
            k_values = pd.Series(stoch_rsi, index=prices.index).rolling(window=self.k_period).mean() * 100
            d_values = k_values.rolling(window=self.d_period).mean()
            
            result = pd.DataFrame({
                'stochrsi_k': k_values,
                'stochrsi_d': d_values
            })
            
            logger.info(f"StochRSI calculado para {len(result)} períodos")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao calcular StochRSI: {e}")
            return pd.DataFrame(index=prices.index, columns=['stochrsi_k', 'stochrsi_d'])
    
    def get_signals(self, stochrsi_data: pd.DataFrame) -> pd.DataFrame:
        """
        Gera sinais de compra/venda baseados no StochRSI.
        
        Args:
            stochrsi_data: DataFrame com dados StochRSI
        
        Returns:
            DataFrame com sinais
        """
        try:
            signals = pd.DataFrame(index=stochrsi_data.index)
            
            k_values = stochrsi_data['stochrsi_k']
            d_values = stochrsi_data['stochrsi_d']
            
            # Sinais básicos
            signals['oversold'] = k_values < 20
            signals['overbought'] = k_values > 80
            
            # Cruzamentos
            signals['k_cross_d_up'] = (k_values > d_values) & (k_values.shift(1) <= d_values.shift(1))
            signals['k_cross_d_down'] = (k_values < d_values) & (k_values.shift(1) >= d_values.shift(1))
            
            # Sinais de compra/venda
            signals['buy_signal'] = signals['oversold'] & signals['k_cross_d_up']
            signals['sell_signal'] = signals['overbought'] & signals['k_cross_d_down']
            
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais: {e}")
            return pd.DataFrame(index=stochrsi_data.index)
    
    def update_parameters(self, rsi_period: int = None, stoch_period: int = None,
                         k_period: int = None, d_period: int = None):
        """
        Atualiza os parâmetros do indicador.
        
        Args:
            rsi_period: Novo período do RSI
            stoch_period: Novo período do Stochastic
            k_period: Novo período de suavização do %K
            d_period: Novo período de suavização do %D
        """
        if rsi_period is not None:
            self.rsi_period = rsi_period
        if stoch_period is not None:
            self.stoch_period = stoch_period
        if k_period is not None:
            self.k_period = k_period
        if d_period is not None:
            self.d_period = d_period
        
        logger.info(f"Parâmetros atualizados: RSI({self.rsi_period}), "
                   f"Stoch({self.stoch_period}), K({self.k_period}), D({self.d_period})")

# Funções de conveniência para compatibilidade
def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """
    Função de conveniência para calcular RSI.
    
    Args:
        series: Série de preços
        window: Período do RSI
    
    Returns:
        Série com valores RSI
    """
    indicator = StochRSIIndicator(rsi_period=window)
    return indicator.calculate_rsi(series)

def stochrsi(series: pd.Series, rsi_window: int = 14, stoch_window: int = 14,
             smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
    """
    Função de conveniência para calcular StochRSI.
    
    Args:
        series: Série de preços
        rsi_window: Período do RSI
        stoch_window: Período do Stochastic
        smooth_k: Suavização do %K
        smooth_d: Suavização do %D
    
    Returns:
        DataFrame com %K e %D do StochRSI
    """
    indicator = StochRSIIndicator(
        rsi_period=rsi_window,
        stoch_period=stoch_window,
        k_period=smooth_k,
        d_period=smooth_d
    )
    return indicator.calculate_stochrsi(series)
