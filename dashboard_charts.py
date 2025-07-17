"""
Teste Dashboard com Gráficos
=============================

Script para testar o dashboard com gráficos no modo teste.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.data.data_manager import get_data_manager
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from config.settings import setup_logging

# Configurar logging
setup_logging()

# Configurar página
st.set_page_config(
    page_title="Dashboard Teste - Gráficos",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📊 Dashboard Teste - Gráficos Renko + StochRSI")
    st.markdown("*Visualização detalhada dos indicadores*")
    
    # Pares de teste
    test_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
    
    # Sidebar
    st.sidebar.header("⚙️ Configurações")
    
    # Seleção de par
    selected_pair = st.sidebar.selectbox(
        "📊 Selecione o par:",
        test_pairs,
        index=0
    )
    
    # Seleção de timeframe
    timeframe = st.sidebar.selectbox(
        "⏰ Selecione o timeframe:",
        ['1h', '4h', '1d'],
        index=1
    )
    
    # Configurações ATR
    use_atr = st.sidebar.checkbox("Usar ATR dinâmico", value=True)
    atr_period = st.sidebar.slider("Período ATR", 7, 30, 14)
    
    if not use_atr:
        brick_size = st.sidebar.slider("Brick Size", 50, 1000, 200)
    else:
        brick_size = None
    
    # Botão para atualizar
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
    
    # Coleta dados
    with st.spinner(f"📡 Coletando dados para {selected_pair} {timeframe}..."):
        data_manager = get_data_manager()
        df = data_manager.get_symbol_data(selected_pair, timeframe, force_cache=False)
        
        if df.empty:
            st.error(f"❌ Sem dados para {selected_pair} {timeframe}")
            return
    
    # Gera Renko
    with st.spinner("🧱 Gerando dados Renko..."):
        renko_df = gerar_renko(
            df, 
            brick_size=brick_size,
            symbol=selected_pair,
            use_atr=use_atr,
            atr_period=atr_period
        )
        
        if renko_df.empty:
            st.error(f"❌ Erro ao gerar Renko para {selected_pair}")
            return
    
    # Calcula StochRSI
    with st.spinner("🎯 Calculando StochRSI..."):
        stoch_df = stochrsi(renko_df['close'])
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Dados Originais", f"{len(df)} candles")
    
    with col2:
        st.metric("🧱 Tijolos Renko", f"{len(renko_df)} tijolos")
    
    with col3:
        if use_atr:
            # Pega o brick size calculado
            from src.indicators.renko import RenkoIndicator
            indicator = RenkoIndicator(symbol=selected_pair, use_atr=True, atr_period=atr_period)
            calculated_size = indicator.get_calculated_brick_size(df)
            st.metric("🧱 Brick Size (ATR)", f"{calculated_size:.2f}")
        else:
            st.metric("🧱 Brick Size", f"{brick_size}")
    
    with col4:
        if not stoch_df.empty and len(stoch_df) > 0:
            last_k = stoch_df['stochrsi_k'].iloc[-1]
            st.metric("🎯 StochRSI %K", f"{last_k:.1f}")
        else:
            st.metric("🎯 StochRSI %K", "N/A")
    
    # Layout em duas colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Gráfico de Preços")
        
        # Gráfico de candlestick
        fig_candle = go.Figure()
        
        # Limita a 200 últimas barras
        df_plot = df.tail(200)
        
        fig_candle.add_trace(go.Candlestick(
            x=df_plot.index,
            open=df_plot['open'],
            high=df_plot['high'],
            low=df_plot['low'],
            close=df_plot['close'],
            name=f"{selected_pair} Candlestick"
        ))
        
        fig_candle.update_layout(
            title=f"{selected_pair} {timeframe} - Candlestick",
            xaxis_title="Data",
            yaxis_title="Preço",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_candle, use_container_width=True)
    
    with col2:
        st.subheader("🧱 Gráfico Renko")
        
        # Gráfico Renko
        fig_renko = go.Figure()
        
        # Limita a 100 últimos tijolos
        renko_plot = renko_df.tail(100)
        
        fig_renko.add_trace(go.Candlestick(
            x=renko_plot.index,
            open=renko_plot['open'],
            high=renko_plot['high'],
            low=renko_plot['low'],
            close=renko_plot['close'],
            name=f"{selected_pair} Renko"
        ))
        
        fig_renko.update_layout(
            title=f"{selected_pair} {timeframe} - Renko",
            xaxis_title="Índice",
            yaxis_title="Preço",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_renko, use_container_width=True)
    
    # Gráfico do StochRSI (full width)
    if not stoch_df.empty and len(stoch_df) > 0:
        st.subheader("🎯 Análise StochRSI")
        
        fig_stoch = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Preço Renko', 'StochRSI'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Subplot 1: Preço Renko
        renko_plot = renko_df.tail(100)
        fig_stoch.add_trace(
            go.Scatter(
                x=renko_plot.index,
                y=renko_plot['close'],
                mode='lines',
                name='Preço Renko',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # Subplot 2: StochRSI
        stoch_plot = stoch_df.tail(100)
        fig_stoch.add_trace(
            go.Scatter(
                x=stoch_plot.index,
                y=stoch_plot['stochrsi_k'],
                mode='lines',
                name='%K',
                line=dict(color='orange', width=2)
            ),
            row=2, col=1
        )
        
        fig_stoch.add_trace(
            go.Scatter(
                x=stoch_plot.index,
                y=stoch_plot['stochrsi_d'],
                mode='lines',
                name='%D',
                line=dict(color='red', width=2)
            ),
            row=2, col=1
        )
        
        # Linhas de referência no StochRSI
        fig_stoch.add_hline(y=80, line_dash="dash", line_color="red", row=2, col=1)
        fig_stoch.add_hline(y=20, line_dash="dash", line_color="green", row=2, col=1)
        fig_stoch.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
        
        fig_stoch.update_layout(
            title=f"{selected_pair} {timeframe} - Análise Completa",
            height=600,
            showlegend=True
        )
        
        fig_stoch.update_yaxes(title_text="Preço", row=1, col=1)
        fig_stoch.update_yaxes(title_text="StochRSI", row=2, col=1, range=[0, 100])
        fig_stoch.update_xaxes(title_text="Índice", row=2, col=1)
        
        st.plotly_chart(fig_stoch, use_container_width=True)
        
        # Análise do sinal atual
        last_k = stoch_df['stochrsi_k'].iloc[-1]
        last_d = stoch_df['stochrsi_d'].iloc[-1]
        
        st.subheader("🚨 Análise do Sinal")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 StochRSI %K", f"{last_k:.1f}")
        
        with col2:
            st.metric("📊 StochRSI %D", f"{last_d:.1f}")
        
        with col3:
            if last_k > 80:
                st.error("🔴 SOBRECOMPRA - Considere venda")
            elif last_k < 20:
                st.success("🟢 SOBREVENDA - Considere compra")
            else:
                st.info("🟡 NEUTRO - Aguarde sinal")
        
        # Tabela com dados recentes
        st.subheader("📋 Dados Recentes")
        
        # Combina dados Renko e StochRSI
        combined_df = pd.concat([
            renko_df[['close']].tail(10),
            stoch_df[['stochrsi_k', 'stochrsi_d']].tail(10)
        ], axis=1)
        
        st.dataframe(combined_df, use_container_width=True)
    
    else:
        st.warning("⚠️ Dados insuficientes para calcular StochRSI")
        st.info("💡 Tente usar um brick size menor ou aumentar o período de dados")

if __name__ == "__main__":
    main()
