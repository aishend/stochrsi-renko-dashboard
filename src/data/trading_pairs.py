"""
Trading Pairs Manager
=====================

Gerenciador de pares de trading.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
import os

from src.api.binance_client import get_binance_client
from config.settings import DASHBOARD_CONFIG

logger = logging.getLogger(__name__)

class TradingPairsManager:
    """
    Gerenciador de pares de trading.
    """
    
    def __init__(self):
        """Inicializa o gerenciador."""
        self.client = get_binance_client()
        self.pairs_file = 'trading_pairs.json'
        self.default_pairs = DASHBOARD_CONFIG['default_pairs']
    
    def get_all_pairs(self) -> List[str]:
        """
        Obtém todos os pares disponíveis.
        
        Returns:
            Lista de pares disponíveis
        """
        # Corrigido: usando o método correto da API
        exchange_info = self.client.futures_exchange_info()
        return [symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['status'] == 'TRADING']
    
    def get_popular_pairs(self) -> List[str]:
        """
        Obtém pares populares/recomendados.
        
        Returns:
            Lista de pares populares
        """
        return self.default_pairs
    
    def filter_pairs_by_volume(self, min_volume: float = 1000000) -> List[str]:
        """
        Filtra pares por volume mínimo.
        
        Args:
            min_volume: Volume mínimo em 24h
        
        Returns:
            Lista de pares filtrados
        """
        try:
            # Obtém estatísticas de 24h
            stats = self.client.client.futures_ticker()
            
            # Filtra por volume
            high_volume_pairs = [
                stat['symbol'] for stat in stats
                if float(stat['quoteVolume']) >= min_volume
            ]
            
            logger.info(f"Encontrados {len(high_volume_pairs)} pares com volume >= {min_volume}")
            return high_volume_pairs
            
        except Exception as e:
            logger.error(f"Erro ao filtrar pares por volume: {e}")
            return self.default_pairs
    
    def filter_pairs_by_pattern(self, pattern: str) -> List[str]:
        """
        Filtra pares por padrão (ex: USDT, BTC).
        
        Args:
            pattern: Padrão a ser filtrado
        
        Returns:
            Lista de pares filtrados
        """
        all_pairs = self.get_all_pairs()
        filtered_pairs = [pair for pair in all_pairs if pattern in pair]
        
        logger.info(f"Encontrados {len(filtered_pairs)} pares com padrão '{pattern}'")
        return filtered_pairs
    
    def get_stable_pairs(self) -> List[str]:
        """
        Obtém pares com stablecoins.
        
        Returns:
            Lista de pares com stablecoins
        """
        stablecoins = ['USDT', 'BUSD', 'USDC', 'TUSD', 'USDP']
        all_pairs = self.get_all_pairs()
        
        stable_pairs = [
            pair for pair in all_pairs
            if any(stable in pair for stable in stablecoins)
        ]
        
        logger.info(f"Encontrados {len(stable_pairs)} pares com stablecoins")
        return stable_pairs
    
    def save_pairs_to_file(self, pairs: List[str], filename: str = None):
        """
        Salva pares em arquivo.
        
        Args:
            pairs: Lista de pares
            filename: Nome do arquivo (opcional)
        """
        filename = filename or self.pairs_file
        
        try:
            data = {
                'pairs': pairs,
                'updated_at': datetime.now().isoformat(),
                'total_pairs': len(pairs)
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Pares salvos em {filename}: {len(pairs)} pares")
            
        except Exception as e:
            logger.error(f"Erro ao salvar pares: {e}")
    
    def load_pairs_from_file(self, filename: str = None) -> List[str]:
        """
        Carrega pares de arquivo.
        
        Args:
            filename: Nome do arquivo (opcional)
        
        Returns:
            Lista de pares carregados
        """
        filename = filename or self.pairs_file
        
        try:
            if not os.path.exists(filename):
                logger.warning(f"Arquivo {filename} não encontrado")
                return self.default_pairs
            
            with open(filename, 'r') as f:
                data = json.load(f)
            
            pairs = data.get('pairs', [])
            logger.info(f"Pares carregados de {filename}: {len(pairs)} pares")
            return pairs
            
        except Exception as e:
            logger.error(f"Erro ao carregar pares: {e}")
            return self.default_pairs
    
    def update_pairs_file(self):
        """Atualiza arquivo de pares com dados mais recentes."""
        try:
            all_pairs = self.get_all_pairs()
            self.save_pairs_to_file(all_pairs)
            
            # Cria também arquivo Python para compatibilidade
            self._create_python_pairs_file(all_pairs)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar arquivo de pares: {e}")
    
    def _create_python_pairs_file(self, pairs: List[str]):
        """Cria arquivo Python com pares para compatibilidade."""
        try:
            with open('trading_pairs.py', 'w') as f:
                f.write('# Arquivo gerado automaticamente\n')
                f.write(f'# Atualizado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                f.write('TRADING_PAIRS = [\n')
                
                for pair in pairs:
                    f.write(f'    "{pair}",\n')
                
                f.write(']\n')
            
            logger.info("Arquivo Python trading_pairs.py criado")
            
        except Exception as e:
            logger.error(f"Erro ao criar arquivo Python: {e}")
    
    def get_pairs_info(self) -> Dict:
        """
        Obtém informações sobre os pares.
        
        Returns:
            Dictionary com informações
        """
        try:
            all_pairs = self.get_all_pairs()
            stable_pairs = self.get_stable_pairs()
            popular_pairs = self.get_popular_pairs()
            
            # Categoriza pares
            btc_pairs = [p for p in all_pairs if p.endswith('BTC')]
            eth_pairs = [p for p in all_pairs if p.endswith('ETH')]
            usdt_pairs = [p for p in all_pairs if p.endswith('USDT')]
            
            return {
                'total_pairs': len(all_pairs),
                'stable_pairs': len(stable_pairs),
                'popular_pairs': len(popular_pairs),
                'btc_pairs': len(btc_pairs),
                'eth_pairs': len(eth_pairs),
                'usdt_pairs': len(usdt_pairs),
                'categories': {
                    'BTC': btc_pairs[:10],  # Top 10 de cada categoria
                    'ETH': eth_pairs[:10],
                    'USDT': usdt_pairs[:10],
                    'Popular': popular_pairs
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações dos pares: {e}")
            return {}

# Instância global
_pairs_manager = None

def get_pairs_manager() -> TradingPairsManager:
    """
    Obtém a instância singleton do gerenciador de pares.
    
    Returns:
        Instância do TradingPairsManager
    """
    global _pairs_manager
    if _pairs_manager is None:
        _pairs_manager = TradingPairsManager()
    return _pairs_manager

# Constante para compatibilidade
TRADING_PAIRS = DASHBOARD_CONFIG['default_pairs']
