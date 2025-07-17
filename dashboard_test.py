"""
Dashboard de Teste - 5 Pares
============================

Dashboard simplificado para testar apenas 5 pares de moedas.
"""

import streamlit as st
import pandas as pd
import logging
import time
from datetime import datetime
import sys
import os

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.data_manager import get_data_manager
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from test_pairs_config import get_test_pairs, get_test_timeframes, get_test_config
from config.settings import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

class TestDashboard:
    """Dashboard de teste para 5 pares."""
    
    def __init__(self):
        self.data_manager = get_data_manager()
        self.test_pairs = get_test_pairs()
        self.test_timeframes = get_test_timeframes()
        self.test_config = get_test_config()
        
        # Configurar página
        st.set_page_config(
            page_title="Dashboard Teste - 5 Pares",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_sidebar(self):
        """Renderiza a sidebar com configurações."""
        st.sidebar.header("🧪 Configurações de Teste")
        
        # Mostra os pares que serão testados
        st.sidebar.subheader("🪙 Pares de Teste")
        for pair in self.test_pairs:
            st.sidebar.text(f"• {pair}")
        
        # Configurações de timeframes
        st.sidebar.subheader("⏰ Timeframes")
        selected_timeframes = st.sidebar.multiselect(
            "Selecione os timeframes:",
            self.test_timeframes,
            default=self.test_timeframes
        )
        
        # Configurações do ATR
        st.sidebar.subheader("🧱 Configuração ATR")
        use_atr = st.sidebar.checkbox(
            "Usar ATR dinâmico",
            value=True,
            help="Calcula brick size baseado na volatilidade"
        )
        
        atr_period = st.sidebar.slider(
            "Período do ATR:",
            min_value=7,
            max_value=30,
            value=14,
            help="Períodos para cálculo do ATR"
        )
        
        # Configurações de coleta
        st.sidebar.subheader("📊 Coleta de Dados")
        data_limit = st.sidebar.slider(
            "Limite de dados:",
            min_value=50,
            max_value=500,
            value=200,
            help="Número de candles por timeframe"
        )
        
        delay = st.sidebar.slider(
            "Delay entre requisições (s):",
            min_value=0.1,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="Pausa entre requisições à API"
        )
        
        return selected_timeframes, use_atr, atr_period, data_limit, delay
    
    def collect_data(self, timeframes, data_limit, delay):
        """Coleta dados para os pares de teste."""
        all_data = {}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_requests = len(self.test_pairs) * len(timeframes)
        current_request = 0
        
        for symbol in self.test_pairs:
            all_data[symbol] = {}
            
            for timeframe in timeframes:
                try:
                    status_text.text(f"Coletando {symbol} {timeframe}...")
                    
                    # Coleta dados
                    df = self.data_manager.get_symbol_data(
                        symbol, 
                        timeframe, 
                        force_cache=False
                    )
                    
                    all_data[symbol][timeframe] = df
                    
                    current_request += 1
                    progress_bar.progress(current_request / total_requests)
                    
                    # Delay entre requisições
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Erro ao coletar {symbol} {timeframe}: {e}")
                    all_data[symbol][timeframe] = pd.DataFrame()
        
        status_text.text("✅ Coleta concluída!")
        return all_data
    
    def process_data(self, all_data, timeframes, use_atr, atr_period):
        """Processa os dados coletados."""
        results = {}
        
        for symbol in self.test_pairs:
            results[symbol] = {}
            
            for timeframe in timeframes:
                try:
                    df = all_data[symbol][timeframe]
                    
                    if df.empty:
                        continue
                    
                    # Gera dados Renko
                    if use_atr:
                        renko_df = gerar_renko(
                            df, 
                            brick_size=None, 
                            symbol=symbol, 
                            use_atr=True, 
                            atr_period=atr_period
                        )
                    else:
                        renko_df = gerar_renko(
                            df, 
                            brick_size=200, 
                            symbol=symbol, 
                            use_atr=False
                        )
                    
                    if renko_df.empty:
                        continue
                    
                    # Calcula StochRSI
                    stoch = stochrsi(renko_df['close'])
                    stoch = stoch.dropna()
                    
                    if not stoch.empty:
                        # Acessa corretamente os valores do StochRSI
                        last_k = stoch['stochrsi_k'].iloc[-1]
                        last_d = stoch['stochrsi_d'].iloc[-1]
                        
                        # Classifica o sinal baseado no K
                        if last_k >= 80:
                            signal = "SOBRECOMPRA"
                        elif last_k <= 20:
                            signal = "SOBREVENDA"
                        else:
                            signal = "NEUTRO"
                        
                        results[symbol][timeframe] = {
                            'renko_count': len(renko_df),
                            'stoch_k': last_k,
                            'stoch_d': last_d,
                            'signal': signal,
                            'data_count': len(df),
                            'last_close': df['close'].iloc[-1] if len(df) > 0 else None
                        }
                
                except Exception as e:
                    logger.error(f"Erro ao processar {symbol} {timeframe}: {e}")
        
        return results
    
    def display_results(self, results, timeframes, use_atr, atr_period):
        """Exibe os resultados."""
        st.header("📊 Resultados dos Testes")
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🪙 Pares Testados", len(self.test_pairs))
        
        with col2:
            st.metric("⏰ Timeframes", len(timeframes))
        
        with col3:
            st.metric("🧱 Método", "ATR Dinâmico" if use_atr else "Fixo")
        
        with col4:
            st.metric("📈 Período ATR", atr_period if use_atr else "N/A")
        
        # Tabela de resultados
        st.subheader("🔍 Detalhes por Par")
        
        for symbol in self.test_pairs:
            if symbol in results:
                st.write(f"**{symbol}**")
                
                # Cria DataFrame para este símbolo
                symbol_data = []
                for timeframe in timeframes:
                    if timeframe in results[symbol]:
                        data = results[symbol][timeframe]
                        symbol_data.append({
                            'Timeframe': timeframe,
                            'Dados OHLC': data['data_count'],
                            'Tijolos Renko': data['renko_count'],
                            'StochRSI K': f"{data['stoch_k']:.2f}" if data['stoch_k'] is not None else "N/A",
                            'StochRSI D': f"{data['stoch_d']:.2f}" if data['stoch_d'] is not None else "N/A",
                            'Sinal': data['signal'] if 'signal' in data else "N/A",
                            'Último Close': f"{data['last_close']:.4f}" if data['last_close'] is not None else "N/A"
                        })
                
                if symbol_data:
                    df_display = pd.DataFrame(symbol_data)
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.warning(f"Nenhum dado processado para {symbol}")
    
    def run(self):
        """Executa o dashboard."""
        st.title("🧪 Dashboard de Teste - 5 Pares")
        st.markdown("*Teste rápido do sistema ATR Renko com pares limitados*")
        
        # Renderiza sidebar
        timeframes, use_atr, atr_period, data_limit, delay = self.render_sidebar()
        
        if not timeframes:
            st.warning("⚠️ Selecione pelo menos um timeframe")
            return
        
        # Botão para executar teste
        if st.button("🚀 Executar Teste", type="primary"):
            with st.spinner("Executando teste..."):
                # Coleta dados
                all_data = self.collect_data(timeframes, data_limit, delay)
                
                # Processa dados
                results = self.process_data(all_data, timeframes, use_atr, atr_period)
                
                # Exibe resultados
                self.display_results(results, timeframes, use_atr, atr_period)
                
                st.success("✅ Teste concluído!")
        
        # Informações adicionais
        with st.expander("ℹ️ Informações do Teste"):
            st.write("**Pares testados:**")
            for i, pair in enumerate(self.test_pairs, 1):
                st.write(f"{i}. {pair}")
            
            st.write("**Configurações:**")
            st.write(f"- Limite de dados: {data_limit} candles")
            st.write(f"- Delay entre requisições: {delay}s")
            st.write(f"- Método: {'ATR Dinâmico' if use_atr else 'Brick Size Fixo'}")
            if use_atr:
                st.write(f"- Período ATR: {atr_period}")

def main():
    """Função principal."""
    try:
        dashboard = TestDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"❌ Erro no dashboard: {e}")
        logger.error(f"Erro no dashboard: {e}")

if __name__ == "__main__":
    main()
