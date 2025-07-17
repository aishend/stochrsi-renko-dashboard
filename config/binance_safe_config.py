"""
Configuração para uso seguro da Binance API
===========================================

Este arquivo define configurações para evitar o erro -1003 (IP banned)
e usar a API de forma eficiente.
"""

# Configurações de Rate Limiting
RATE_LIMIT_CONFIG = {
    'max_requests_per_minute': 1000,  # Margem de segurança (limite real é 1200)
    'max_requests_per_second': 18,    # Margem de segurança (limite real é 20)
    'ban_cooldown_seconds': 60,       # Tempo para aguardar após detectar rate limit
    'request_delay_seconds': 0.1,     # Delay mínimo entre requisições
}

# Configurações de WebSocket
WEBSOCKET_CONFIG = {
    'auto_restart': True,             # Reinicia automaticamente em caso de erro
    'reconnect_delay': 5,             # Segundos para aguardar antes de reconectar
    'max_reconnect_attempts': 3,      # Máximo de tentativas de reconexão
    'heartbeat_interval': 30,         # Intervalo de heartbeat em segundos
}

# Configurações de Cache/Dados
DATA_CONFIG = {
    'max_data_age_hours': 24,         # Idade máxima dos dados em cache
    'cleanup_interval_minutes': 60,   # Intervalo para limpeza automática
    'max_symbols_per_stream': 100,    # Máximo de símbolos por stream
    'buffer_size': 1000,              # Tamanho do buffer de dados
}

# Símbolos recomendados para trading
RECOMMENDED_SYMBOLS = [
    'BTCUSDT',   # Bitcoin
    'ETHUSDT',   # Ethereum
    'BNBUSDT',   # Binance Coin
    'SOLUSDT',   # Solana
    'ADAUSDT',   # Cardano
    'XRPUSDT',   # Ripple
    'DOTUSDT',   # Polkadot
    'AVAXUSDT',  # Avalanche
    'MATICUSDT', # Polygon
    'LINKUSDT',  # Chainlink
]

# Intervalos recomendados
RECOMMENDED_INTERVALS = [
    '1m',   # 1 minuto
    '5m',   # 5 minutos
    '15m',  # 15 minutos
    '1h',   # 1 hora
    '4h',   # 4 horas
    '1d',   # 1 dia
]

# Configurações de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'binance_client.log',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
}

# Configurações de segurança
SECURITY_CONFIG = {
    'use_testnet': False,             # Usar testnet para testes
    'validate_symbols': True,         # Validar símbolos antes de usar
    'max_concurrent_requests': 10,    # Máximo de requisições simultâneas
    'request_timeout': 30,            # Timeout para requisições em segundos
}

# Configurações específicas para diferentes tipos de dados
DATA_TYPES_CONFIG = {
    'historical': {
        'max_days': 30,               # Máximo de dias para dados históricos
        'preferred_method': 'rest',   # 'rest' ou 'websocket'
        'cache_enabled': True,
    },
    'realtime': {
        'preferred_method': 'websocket', # Sempre usar WebSocket para tempo real
        'buffer_updates': True,
        'max_updates_per_second': 10,
    },
    'account': {
        'update_interval': 5,         # Intervalo para atualizar dados da conta
        'cache_positions': True,
        'track_orders': True,
    }
}

# Configurações de monitoramento
MONITORING_CONFIG = {
    'health_check_interval': 60,     # Intervalo para verificar saúde das conexões
    'alert_on_disconnection': True,  # Alertar quando desconectar
    'log_performance_metrics': True, # Registrar métricas de performance
    'save_connection_stats': True,   # Salvar estatísticas de conexão
}

# Função para obter configuração específica
def get_config(section: str, key: str = None):
    """
    Obtém configuração específica.
    
    Args:
        section: Seção da configuração
        key: Chave específica (opcional)
        
    Returns:
        Valor da configuração ou seção completa
    """
    configs = {
        'rate_limit': RATE_LIMIT_CONFIG,
        'websocket': WEBSOCKET_CONFIG,
        'data': DATA_CONFIG,
        'logging': LOGGING_CONFIG,
        'security': SECURITY_CONFIG,
        'data_types': DATA_TYPES_CONFIG,
        'monitoring': MONITORING_CONFIG,
    }
    
    if section not in configs:
        return None
    
    if key is None:
        return configs[section]
    
    return configs[section].get(key)
