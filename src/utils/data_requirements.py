"""
Calculadora de dados necessários para Renko + StochRSI
"""

def calculate_required_data_for_renko_stochrsi(interval: str, brick_size: int = 1000) -> int:
    """
    Calcula a quantidade de dados necessários para Renko + StochRSI.
    
    O Renko pode reduzir drasticamente a quantidade de dados, então precisamos
    de muito mais candles originais para garantir dados suficientes após o Renko.
    
    Args:
        interval: Intervalo dos dados (1m, 5m, 15m, 1h, 4h, 1d)
        brick_size: Tamanho do tijolo Renko (None para ATR dinâmico)
        
    Returns:
        Número de dias necessários para garantir dados suficientes
    """
    
    # Se brick_size é None (ATR dinâmico), usa valor padrão conservador
    if brick_size is None:
        brick_size = 1000  # Valor padrão para ATR dinâmico
    
    # Parâmetros padrão do StochRSI
    RSI_PERIOD = 14
    STOCH_PERIOD = 14
    K_PERIOD = 3
    D_PERIOD = 3
    
    # Mínimo de dados necessários para StochRSI
    min_stochrsi_data = RSI_PERIOD + STOCH_PERIOD + K_PERIOD + D_PERIOD + 10  # ~44 pontos
    
    # Fator de redução do Renko baseado no timeframe e brick_size
    # Timeframes menores com brick_size grande = maior redução
    # Timeframes maiores com brick_size pequeno = menor redução
    
    reduction_factors = {
        '1m': 0.05,    # Renko reduz muito em 1 minuto
        '3m': 0.08,    # 
        '5m': 0.10,    # 
        '15m': 0.15,   # 
        '30m': 0.20,   # 
        '1h': 0.25,    # 
        '2h': 0.30,    # 
        '4h': 0.35,    # 
        '6h': 0.40,    # 
        '8h': 0.45,    # 
        '12h': 0.50,   # 
        '1d': 0.60,    # Renko reduz menos em 1 dia
        '3d': 0.70,    # 
        '1w': 0.80     # 
    }
    
    base_reduction = reduction_factors.get(interval, 0.30)
    
    # Ajuste baseado no brick_size
    # Brick_size maior = mais redução
    if brick_size >= 5000:
        brick_multiplier = 0.5
    elif brick_size >= 2000:
        brick_multiplier = 0.7
    elif brick_size >= 1000:
        brick_multiplier = 0.8
    elif brick_size >= 500:
        brick_multiplier = 0.9
    else:
        brick_multiplier = 1.0
    
    final_reduction = base_reduction * brick_multiplier
    
    # Calcula dados necessários
    # Se o Renko reduz para X% dos dados originais, precisamos de 100/X% dos dados
    required_candles = int(min_stochrsi_data / final_reduction)
    
    # Converte para dias baseado no timeframe
    candles_per_day = {
        '1m': 1440,     # 1440 candles por dia
        '3m': 480,      # 480 candles por dia
        '5m': 288,      # 288 candles por dia
        '15m': 96,      # 96 candles por dia
        '30m': 48,      # 48 candles por dia
        '1h': 24,       # 24 candles por dia
        '2h': 12,       # 12 candles por dia
        '4h': 6,        # 6 candles por dia
        '6h': 4,        # 4 candles por dia
        '8h': 3,        # 3 candles por dia
        '12h': 2,       # 2 candles por dia
        '1d': 1,        # 1 candle por dia
        '3d': 0.33,     # 1 candle a cada 3 dias
        '1w': 0.14      # 1 candle por semana
    }
    
    candles_per_day_value = candles_per_day.get(interval, 24)
    required_days = int(required_candles / candles_per_day_value)
    
    # Mínimo de segurança
    min_days = {
        '1m': 7,        # Mínimo 7 dias para 1 minuto
        '3m': 10,       # Mínimo 10 dias para 3 minutos
        '5m': 14,       # Mínimo 14 dias para 5 minutos
        '15m': 21,      # Mínimo 21 dias para 15 minutos
        '30m': 30,      # Mínimo 30 dias para 30 minutos
        '1h': 45,       # Mínimo 45 dias para 1 hora
        '2h': 60,       # Mínimo 60 dias para 2 horas
        '4h': 90,       # Mínimo 90 dias para 4 horas
        '6h': 120,      # Mínimo 120 dias para 6 horas
        '8h': 150,      # Mínimo 150 dias para 8 horas
        '12h': 180,     # Mínimo 180 dias para 12 horas
        '1d': 365,      # Mínimo 365 dias para 1 dia
        '3d': 500,      # Mínimo 500 dias para 3 dias
        '1w': 700       # Mínimo 700 dias para 1 semana
    }
    
    min_days_value = min_days.get(interval, 90)
    
    # Retorna o maior entre o calculado e o mínimo
    final_days = max(required_days, min_days_value)
    
    return final_days

# Tabela de referência para diferentes configurações
RENKO_STOCHRSI_DATA_REQUIREMENTS = {
    # interval: (brick_size_1000, brick_size_500, brick_size_2000)
    '1m': (7, 5, 10),
    '3m': (10, 8, 15),
    '5m': (14, 12, 20),
    '15m': (21, 18, 30),
    '30m': (30, 25, 45),
    '1h': (45, 40, 60),
    '2h': (60, 50, 90),
    '4h': (90, 75, 120),
    '6h': (120, 100, 150),
    '8h': (150, 125, 180),
    '12h': (180, 150, 240),
    '1d': (365, 300, 450),
    '3d': (500, 400, 600),
    '1w': (700, 600, 800)
}

def get_optimized_days_for_renko_stochrsi(interval: str, brick_size: int = 1000) -> int:
    """
    Retorna número otimizado de dias para Renko + StochRSI.
    
    Args:
        interval: Intervalo dos dados
        brick_size: Tamanho do tijolo Renko (None para ATR dinâmico)
        
    Returns:
        Número de dias otimizado
    """
    # Se brick_size é None (ATR dinâmico), usa valor padrão conservador
    if brick_size is None:
        brick_size = 1000  # Valor padrão para ATR dinâmico
    
    if interval in RENKO_STOCHRSI_DATA_REQUIREMENTS:
        base_days = RENKO_STOCHRSI_DATA_REQUIREMENTS[interval][0]  # Para brick_size 1000
        
        # Ajusta baseado no brick_size
        if brick_size <= 500:
            return int(base_days * 0.8)
        elif brick_size <= 1000:
            return base_days
        elif brick_size <= 2000:
            return int(base_days * 1.3)
        elif brick_size <= 5000:
            return int(base_days * 1.8)
        else:
            return int(base_days * 2.5)
    else:
        # Fallback para intervalos não mapeados
        return calculate_required_data_for_renko_stochrsi(interval, brick_size)

if __name__ == "__main__":
    # Testes
    print("Tabela de Requisitos de Dados para Renko + StochRSI")
    print("=" * 60)
    
    intervals = ['1m', '5m', '15m', '1h', '4h', '1d']
    brick_sizes = [500, 1000, 2000, 5000]
    
    for interval in intervals:
        print(f"\n{interval}:")
        for brick_size in brick_sizes:
            days = get_optimized_days_for_renko_stochrsi(interval, brick_size)
            print(f"  Brick {brick_size}: {days} dias")
