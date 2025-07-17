import logging
import os
import sys
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta

# Adiciona o diretório atual ao Python path
sys.path.append('.')

# Importa os módulos da nova estrutura
from src.api.binance_client import get_binance_client, get_futures_klines
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from config.settings import setup_logging

# Configuração do logging
setup_logging()
logger = logging.getLogger(__name__)

# Coleta e prepara dados
client = get_binance_client()
symbol = "BTCUSDT"
interval = "4h"
days = 7

logger.info(f"Coletando dados para {symbol} {interval}")
# Corrigido: usando a função wrapper que utiliza o método correto
ohlc = get_futures_klines(symbol, interval, (datetime.now() - timedelta(days=days)).timestamp() * 1000)

# Parâmetro Renko
brick_size = 1000

# Gera Renko
logger.info("Gerando dados Renko")
renko_df = gerar_renko(ohlc, brick_size)

if renko_df.empty:
    logger.error("Dados Renko vazios!")
    exit(1)

# Plota gráfico Renko tradicional
logger.info("Gerando gráfico Renko")
mpf.plot(
    ohlc,
    type='renko',
    renko_params=dict(brick_size=brick_size),
    style='charles',
    title=f'{symbol} Renko Chart ({interval} Interval)',
    volume=True,
    show_nontrading=True
)
plt.show()

# Calcula StochRSI dos fechamentos Renko
logger.info("Calculando StochRSI")
stochrsi_vals = stochrsi(renko_df['close'])

# Junta a data/hora correspondente
stochrsi_vals_with_date = stochrsi_vals.copy()
stochrsi_vals_with_date['date'] = pd.to_datetime(renko_df['date']).dt.strftime('%Y-%m-%d %H:%M')
stochrsi_vals_with_date = stochrsi_vals_with_date[['date', 'stochrsi_k', 'stochrsi_d']]

# Exibe os últimos 10 valores de %K, %D e data/hora
print("\n📊 Últimos 10 valores StochRSI:")
print("=" * 50)
print(stochrsi_vals_with_date.tail(10))

# Análise dos sinais
ultimo_valor = stochrsi_vals_with_date.tail(1)
k_val = ultimo_valor['stochrsi_k'].iloc[0]
d_val = ultimo_valor['stochrsi_d'].iloc[0]

print(f"\n🔍 Análise do último valor:")
print(f"K: {k_val:.2f}")
print(f"D: {d_val:.2f}")

if k_val < 20 and d_val < 20:
    print("🟢 SINAL: Oversold - Possível compra")
elif k_val > 80 and d_val > 80:
    print("🔴 SINAL: Overbought - Possível venda")
elif k_val > d_val:
    print("⬆️ SINAL: Bullish")
else:
    print("⬇️ SINAL: Bearish")

logger.info("Análise concluída com sucesso")
