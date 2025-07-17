"""
Renko Indicator
===============

Implementação do indicador Renko para análise técnica com cálculo dinâmico do brick size baseado no ATR.
"""

import pandas as pd
import logging
from typing import Optional
from stocktrends import Renko

from config.settings import INDICATOR_CONFIG
from .atr import get_atr_brick_size, calculate_dynamic_brick_size

logger = logging.getLogger(__name__)

class RenkoIndicator:
    """
    Classe para gerar gráficos Renko.
    """
    
    def __init__(self, brick_size: Optional[int] = None, symbol: str = "BTCUSDT", use_atr: bool = True, atr_period: int = 14):
        """
        Inicializa o indicador Renko.
        
        Args:
            brick_size: Tamanho do tijolo (opcional, usa ATR se não especificado)
            symbol: Símbolo do ativo para cálculo do ATR
            use_atr: Se deve usar ATR para calcular brick size dinamicamente
            atr_period: Período para cálculo do ATR (padrão: 14)
        """
        self.symbol = symbol
        self.use_atr = use_atr
        self.atr_period = atr_period
        self.brick_size = brick_size
        
        # Se não especificou brick_size, será calculado dinamicamente via ATR
        if brick_size is None:
            self.brick_size = None  # Será calculado no generate_renko_data
        else:
            # Valida brick_size especificado
            min_size = INDICATOR_CONFIG['renko']['min_brick_size']
            max_size = INDICATOR_CONFIG['renko']['max_brick_size']
            
            if not min_size <= brick_size <= max_size:
                logger.warning(f"Brick size {brick_size} fora do range [{min_size}, {max_size}]")
                self.brick_size = max(min_size, min(max_size, brick_size))
    
    def generate_renko_data(self, ohlc_data: pd.DataFrame) -> pd.DataFrame:
        """
        Gera dados Renko a partir de dados OHLC com brick size dinâmico baseado no ATR.
        
        Args:
            ohlc_data: DataFrame com dados OHLC
        
        Returns:
            DataFrame com dados Renko
        """
        try:
            if ohlc_data.empty:
                logger.warning("DataFrame OHLC vazio fornecido")
                return pd.DataFrame()
            
            # Calcula brick size dinamicamente se necessário
            if self.brick_size is None or self.use_atr:
                calculated_brick_size = calculate_dynamic_brick_size(ohlc_data, self.symbol, self.atr_period)
                
                if self.brick_size is None:
                    self.brick_size = calculated_brick_size
                    logger.info(f"Brick size calculado via ATR para {self.symbol}: {self.brick_size}")
                else:
                    # Atualiza brick size se usar ATR
                    self.brick_size = calculated_brick_size
                    logger.info(f"Brick size atualizado via ATR para {self.symbol}: {self.brick_size}")
            
            # Prepara dados para stocktrends
            renko_df = ohlc_data.copy()
            renko_df = renko_df.reset_index()
            
            # Log detalhado para debug
            logger.debug(f"Dados originais - Colunas: {list(ohlc_data.columns)}, Index: {ohlc_data.index.name}")
            logger.debug(f"Após reset_index - Colunas: {list(renko_df.columns)}")
            
            # Primeiro, garante que temos uma coluna de data
            if 'date' not in renko_df.columns:
                # Verifica possíveis nomes de colunas de data
                date_columns = ['Time', 'timestamp', 'open_time', 'datetime']
                date_found = False
                
                for date_col in date_columns:
                    if date_col in renko_df.columns:
                        renko_df.rename(columns={date_col: 'date'}, inplace=True)
                        date_found = True
                        logger.debug(f"Coluna de data encontrada: {date_col} -> date")
                        break
                
                # Se não encontrou coluna de data, usa o index
                if not date_found:
                    if renko_df.index.name:
                        renko_df['date'] = renko_df.index
                        logger.debug(f"Usando index como data: {renko_df.index.name}")
                    elif hasattr(renko_df.index, 'dtype') and 'datetime' in str(renko_df.index.dtype):
                        renko_df['date'] = renko_df.index
                        logger.debug("Usando datetime index como data")
                    else:
                        # Se chegou aqui, tenta usar a primeira coluna do reset_index
                        first_col = renko_df.columns[0]
                        if 'datetime' in str(renko_df[first_col].dtype).lower() or pd.api.types.is_datetime64_any_dtype(renko_df[first_col]):
                            renko_df.rename(columns={first_col: 'date'}, inplace=True)
                            logger.debug(f"Usando primeira coluna como data: {first_col} -> date")
                        else:
                            logger.error("Não foi possível determinar a coluna de data")
                            return pd.DataFrame()
            
            # Segundo, normaliza os nomes das colunas OHLC
            # Mapeia diferentes variações para os nomes padrão
            column_mappings = {
                # Diferentes variações de Open
                'Open': 'open',
                'OPEN': 'open',
                'o': 'open',
                
                # Diferentes variações de High
                'High': 'high',
                'HIGH': 'high',
                'h': 'high',
                
                # Diferentes variações de Low
                'Low': 'low',
                'LOW': 'low',
                'l': 'low',
                
                # Diferentes variações de Close
                'Close': 'close',
                'CLOSE': 'close',
                'c': 'close',
                
                # Diferentes variações de Volume
                'Volume': 'volume',
                'VOLUME': 'volume',
                'v': 'volume',
                'vol': 'volume'
            }
            
            # Aplica os mapeamentos
            for old_name, new_name in column_mappings.items():
                if old_name in renko_df.columns:
                    renko_df.rename(columns={old_name: new_name}, inplace=True)
                    logger.debug(f"Coluna renomeada: {old_name} -> {new_name}")
            
            # Verifica se todas as colunas necessárias estão presentes
            required_columns = ['date', 'open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in renko_df.columns]
            
            if missing_columns:
                logger.error(f"Colunas ausentes: {missing_columns}")
                logger.error(f"Colunas disponíveis: {list(renko_df.columns)}")
                logger.error(f"Primeiras linhas do DataFrame:")
                logger.error(f"{renko_df.head()}")
                return pd.DataFrame()
            
            # Garante que as colunas estão no tipo correto
            try:
                renko_df['open'] = pd.to_numeric(renko_df['open'], errors='coerce')
                renko_df['high'] = pd.to_numeric(renko_df['high'], errors='coerce')
                renko_df['low'] = pd.to_numeric(renko_df['low'], errors='coerce')
                renko_df['close'] = pd.to_numeric(renko_df['close'], errors='coerce')
                
                # Converte coluna de data para datetime se necessário
                if not pd.api.types.is_datetime64_any_dtype(renko_df['date']):
                    renko_df['date'] = pd.to_datetime(renko_df['date'], errors='coerce')
                    
            except Exception as e:
                logger.error(f"Erro ao converter tipos de dados: {e}")
                return pd.DataFrame()
            
            # Remove linhas com valores NaN
            initial_length = len(renko_df)
            renko_df = renko_df.dropna(subset=['open', 'high', 'low', 'close', 'date'])
            final_length = len(renko_df)
            
            if final_length < initial_length:
                logger.warning(f"Removidas {initial_length - final_length} linhas com valores NaN")
            
            if renko_df.empty:
                logger.error("DataFrame vazio após remoção de valores NaN")
                return pd.DataFrame()
            
            # Ordena por data
            renko_df = renko_df.sort_values('date')
            
            # Cria objeto Renko
            renko = Renko(renko_df)
            renko.brick_size = self.brick_size
            
            # Gera dados Renko
            renko_data = renko.get_ohlc_data()
            
            logger.info(f"Dados Renko gerados: {len(renko_data)} tijolos com tamanho {self.brick_size} (ATR: {self.use_atr})")
            return renko_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados Renko: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def get_calculated_brick_size(self, ohlc_data: pd.DataFrame) -> float:
        """
        Retorna o brick size calculado baseado no ATR sem gerar dados Renko.
        
        Args:
            ohlc_data: DataFrame com dados OHLC
        
        Returns:
            Brick size calculado
        """
        try:
            if self.use_atr:
                return calculate_dynamic_brick_size(ohlc_data, self.symbol, self.atr_period)
            else:
                return self.brick_size or INDICATOR_CONFIG['renko']['default_brick_size']
        except Exception as e:
            logger.error(f"Erro ao calcular brick size: {e}")
            return INDICATOR_CONFIG['renko']['default_brick_size']
    
    def update_brick_size(self, new_brick_size: int):
        """
        Atualiza o tamanho do tijolo.
        
        Args:
            new_brick_size: Novo tamanho do tijolo
        """
        min_size = INDICATOR_CONFIG['renko']['min_brick_size']
        max_size = INDICATOR_CONFIG['renko']['max_brick_size']
        
        if min_size <= new_brick_size <= max_size:
            self.brick_size = new_brick_size
            self.use_atr = False  # Desabilita ATR quando definido manualmente
            logger.info(f"Brick size atualizado para {new_brick_size}")
        else:
            logger.warning(f"Brick size {new_brick_size} fora do range [{min_size}, {max_size}]")
    
    def enable_atr(self, enable: bool = True, period: int = 14):
        """
        Habilita ou desabilita o cálculo dinâmico via ATR.
        
        Args:
            enable: Se deve habilitar ATR
            period: Período para cálculo do ATR
        """
        self.use_atr = enable
        self.atr_period = period
        if enable:
            logger.info(f"ATR habilitado com período {period}")
        else:
            logger.info("ATR desabilitado - usando brick size fixo")

# Função de conveniência para compatibilidade
def gerar_renko(ohlc: pd.DataFrame, brick_size: int = None, symbol: str = "BTCUSDT", use_atr: bool = True, atr_period: int = 14) -> pd.DataFrame:
    """
    Função de conveniência para gerar dados Renko com ATR dinâmico.
    
    Args:
        ohlc: DataFrame com dados OHLC
        brick_size: Tamanho do tijolo (opcional, usa ATR se None)
        symbol: Símbolo do ativo para cálculo ATR
        use_atr: Se deve usar ATR para cálculo dinâmico
        atr_period: Período para cálculo do ATR (padrão: 14)
    
    Returns:
        DataFrame com dados Renko
    """
    renko_indicator = RenkoIndicator(brick_size, symbol, use_atr, atr_period)
    return renko_indicator.generate_renko_data(ohlc)

# Função para calcular apenas o brick size sem gerar Renko
def calcular_brick_size_atr(ohlc: pd.DataFrame, symbol: str = "BTCUSDT", period: int = 14) -> float:
    """
    Calcula apenas o brick size baseado no ATR.
    
    Args:
        ohlc: DataFrame com dados OHLC
        symbol: Símbolo do ativo
        period: Período para cálculo do ATR
    
    Returns:
        Brick size calculado
    """
    return calculate_dynamic_brick_size(ohlc, symbol, period)
