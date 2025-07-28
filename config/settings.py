"""
Configurações do Sistema
========================

Arquivo central de configurações do sistema de trading.
"""

import os
import logging
from typing import Dict, List

# Configurações da API Binance
BINANCE_CONFIG = {
    'KEY': os.environ.get('BINANCE_KEY', 'IiPTCvu1AAziLvdusHHkCus5NCpwU0mQ0vMcZnRLwZeFNCA3ODdEIgHYLrDsPYij'),
    'SECRET': os.environ.get('BINANCE_SECRET', 'sUdrgJMQ15FceuPSLjc5NkKY951iWTUvBJmOGUgmhPln05f3jHHEBfnKPuRLnEbe'),
    'BASE_URL': 'https://fapi.binance.com',
    'TESTNET': False
}

# Configurações de logging
LOGGING_CONFIG = {
    'level': logging.INFO,
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'trading_system.log'
}

# Configurações padrão para indicadores
INDICATOR_CONFIG = {
    'stoch_rsi': {
        'period': 14,
        'stoch_period': 14,
        'k_period': 3,
        'd_period': 3
    },
    'renko': {
        'default_brick_size': 1000,
        'min_brick_size': 100,
        'max_brick_size': 10000
    }
}

# Configurações do dashboard
DASHBOARD_CONFIG = {
    'title': '📊 Dashboard Crypto Filtering - Renko + StochRSI',
    'layout': 'wide',
    'default_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT'],
    'default_intervals': ['15m', '1h', '4h', '1d'],
    'available_intervals': ['15m', '1h', '4h', '1d'],
    'default_days': None,  # Calculado automaticamente
    'max_pairs': 100,
    'max_workers': 10,
    # Configurações de auto-refresh
    'auto_refresh_enabled': True,
    'auto_refresh_interval': 7200,  # 2 horas em segundos (2 * 60 * 60)
    'auto_refresh_options': {
        '30 minutos': 1800,
        '1 hora': 3600,
        '2 horas': 7200,
        '4 horas': 14400,
        '6 horas': 21600,
        '12 horas': 43200,
        '24 horas': 86400
    }
}

# Configurações de dados
DATA_CONFIG = {
    'cache_enabled': True,
    'cache_duration': 300,  # 5 minutos (padrão)
    'max_retries': 3,
    'retry_delay': 1,
    'cleanup_interval': 3600,  # 1 hora para limpeza automática
    'max_cache_size': 1000000000  # 1GB máximo de cache
}

def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=LOGGING_CONFIG['level'],
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG['filename']),
            logging.StreamHandler()
        ]
    )

def validate_api_config() -> bool:
    """Valida se as configurações da API estão corretas."""
    return (
        BINANCE_CONFIG['KEY'] != 'COLOQUE_SUA_BINANCE_API_KEY_AQUI' and
        BINANCE_CONFIG['SECRET'] != 'COLOQUE_SUA_BINANCE_API_SECRET_AQUI'
    )
