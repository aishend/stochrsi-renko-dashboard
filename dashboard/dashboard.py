"""
Trading Dashboard
=================

Interface web para visualização e análise de dados de trading.
"""

import streamlit as st
import pandas as pd
import logging
import time
from datetime import datetime
import sys
import os
import time

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.data_manager import get_data_manager
from src.indicators.renko import gerar_renko
from src.indicators.stoch_rsi import stochrsi
from src.data.trading_pairs import get_pairs_manager
from config.settings import DASHBOARD_CONFIG, setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def get_dashboard_mode():
    """Detecta o modo do dashboard baseado nos argumentos."""
    # Verifica argumentos da linha de comando
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--all-pairs":
                return "all_pairs"
            elif arg == "--test-mode":
                return "test_mode"
    
    # Verifica query parameters do Streamlit
    query_params = st.query_params
    if "all_pairs" in query_params:
        return "all_pairs"
    elif "test_mode" in query_params:
        return "test_mode"
    
    return "default"

def get_trading_pairs_for_mode(mode):
    """Retorna os pares de trading baseado no modo."""
    if mode == "all_pairs":
        try:
            from trading_pairs import TRADING_PAIRS
            return TRADING_PAIRS
        except ImportError:
            st.error("❌ Arquivo trading_pairs.py não encontrado!")
            return []
    
    elif mode == "test_mode":
        return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
    
    else:  # default
        try:
            from trading_pairs import TRADING_PAIRS
            # Usa os primeiros 20 pares para o modo padrão
            return TRADING_PAIRS[:20]
        except ImportError:
            return [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'TRXUSDT', 'LINKUSDT',
                'DOTUSDT', 'MATICUSDT', 'LTCUSDT', 'SHIBUSDT', 'UNIUSDT',
                'ATOMUSDT', 'ETCUSDT', 'XLMUSDT', 'BCHUSDT', 'FILUSDT'
            ]

class TradingDashboard:
    """
    Dashboard principal para trading.
    """
    
    def __init__(self):
        """Inicializa o dashboard."""
        self.data_manager = get_data_manager()
        self.pairs_manager = get_pairs_manager()
        self.config = DASHBOARD_CONFIG
        
        # Detecta o modo do dashboard
        self.mode = get_dashboard_mode()
        
        # Inicializa session state para cache de dados
        if 'cached_data' not in st.session_state:
            st.session_state.cached_data = {}
        if 'cached_matriz_stoch' not in st.session_state:
            st.session_state.cached_matriz_stoch = {}
        if 'data_timestamp' not in st.session_state:
            st.session_state.data_timestamp = None
        if 'last_config' not in st.session_state:
            st.session_state.last_config = {}
        if 'updating_data' not in st.session_state:
            st.session_state.updating_data = False
        
        # Configurar página
        page_title = self.config['title']
        if self.mode == "all_pairs":
            page_title += " - Todos os Pares"
        elif self.mode == "test_mode":
            page_title += " - Modo Teste"
        
        st.set_page_config(
            page_title=page_title,
            layout=self.config['layout'],
            initial_sidebar_state="expanded"
        )
        
        # Mostra o modo atual
        self.show_mode_info()
    
    def needs_data_refresh(self, trading_pairs, intervals, brick_size, use_atr, atr_period, force_refresh):
        """Verifica se é necessário atualizar os dados."""
        current_config = {
            'trading_pairs': trading_pairs,
            'intervals': intervals,
            'brick_size': brick_size,
            'use_atr': use_atr,
            'atr_period': atr_period,
            'mode': self.mode
        }
        
        # Se força refresh, sempre atualizar
        if force_refresh:
            return True
        
        # Se não há dados em cache, sempre atualizar
        if not st.session_state.cached_data or not st.session_state.cached_matriz_stoch:
            return True
        
        # Se configuração mudou, atualizar
        if st.session_state.last_config != current_config:
            return True
        
        # Se passou mais de 10 minutos, atualizar
        if st.session_state.data_timestamp:
            time_diff = (datetime.now() - st.session_state.data_timestamp).total_seconds()
            if time_diff > 600:  # 10 minutes
                return True
        
        return False
    
    def show_mode_info(self):
        """Mostra informações sobre o modo atual."""
        if self.mode == "all_pairs":
            st.info("🌐 **Modo: TODOS OS PARES** - Carregando todos os pares disponíveis")
        elif self.mode == "test_mode":
            st.info("🧪 **Modo: TESTE** - Usando apenas 5 pares para desenvolvimento")
        else:
            st.info("📈 **Modo: PADRÃO** - Usando pares selecionados")
        
        # Mostra informações do cache
        if st.session_state.updating_data:
            st.warning("🔄 **Atualizando dados** - Interface permanece funcional com dados anteriores")
        elif st.session_state.data_timestamp:
            cache_age = (datetime.now() - st.session_state.data_timestamp).total_seconds() / 60
            if cache_age < 1:
                st.success(f"💾 **Cache:** Dados atualizados há {cache_age:.0f} segundos")
            else:
                st.info(f"💾 **Cache:** Dados atualizados há {cache_age:.1f} minutos")
        else:
            st.warning("💾 **Cache:** Nenhum dado em cache")
    
    def needs_data_refresh(self, trading_pairs, intervals, brick_size, use_atr, atr_period, force_refresh):
        """Verifica se é necessário atualizar os dados."""
        current_config = {
            'trading_pairs': trading_pairs,
            'intervals': intervals,
            'brick_size': brick_size,
            'use_atr': use_atr,
            'atr_period': atr_period,
            'mode': self.mode
        }
        
        # Se força refresh, sempre atualizar
        if force_refresh:
            return True
        
        # Se não há dados em cache, sempre atualizar
        if not st.session_state.cached_data or not st.session_state.cached_matriz_stoch:
            return True
        
        # Se configuração mudou, atualizar
        if st.session_state.last_config != current_config:
            return True
        
        # Se passou mais de 10 minutos, atualizar
        if st.session_state.data_timestamp:
            time_diff = (datetime.now() - st.session_state.data_timestamp).total_seconds()
            if time_diff > 600:  # 10 minutes
                return True
        
        return False
    
    def cache_data(self, trading_pairs, intervals, brick_size, use_atr, atr_period, all_data, matriz_stoch):
        """Armazena dados no cache da sessão."""
        st.session_state.cached_data = all_data
        st.session_state.cached_matriz_stoch = matriz_stoch
        st.session_state.data_timestamp = datetime.now()
        st.session_state.last_config = {
            'trading_pairs': trading_pairs,
            'intervals': intervals,
            'brick_size': brick_size,
            'use_atr': use_atr,
            'atr_period': atr_period,
            'mode': self.mode
        }
    
    def get_cached_data(self):
        """Recupera dados do cache da sessão."""
        return st.session_state.cached_data, st.session_state.cached_matriz_stoch
    
    def render_sidebar(self):
        """Renderiza a barra lateral com controles."""
        st.sidebar.header("⚙️ Configurações")
        
        # Pares de trading baseado no modo
        st.sidebar.subheader("📊 Pares de Trading")
        
        trading_pairs = get_trading_pairs_for_mode(self.mode)
        
        if not trading_pairs:
            st.sidebar.error("❌ Nenhum par carregado!")
            return None, None, None, None, None, None, None, None, None, None, None
        
        mode_info = {
            "all_pairs": f"🌐 TODOS OS PARES ({len(trading_pairs)})",
            "test_mode": f"🧪 TESTE - 5 pares",
            "default": f"📈 PADRÃO - {len(trading_pairs)} pares"
        }
        
        st.sidebar.info(mode_info[self.mode])
        st.sidebar.write(f"📊 {len(trading_pairs)} pares carregados")
        
        # Opção para alterar modo (somente no dashboard)
        if st.sidebar.button("🔄 Alterar Modo"):
            st.sidebar.markdown("""
            **Para alterar o modo, use:**
            - `python run_system.py` - Modo padrão
            - `python run_system.py --all-pairs` - Todos os pares
            - `python run_system.py --test` - Modo teste
            """)
        
        # Botão para forçar refresh dos dados
        st.sidebar.subheader("🔄 Atualização de Dados")
        
        # Informação sobre última atualização
        current_time = datetime.now().strftime("%H:%M:%S")
        st.sidebar.info(f"🕐 Última verificação: {current_time}")
        
        # Botão para forçar refresh
        force_refresh = st.sidebar.button("🔄 Forçar Atualização dos Dados", 
                                        help="Força busca de novos dados da API, ignorando cache válido")
        
        # Seção de Auto-Refresh
        st.sidebar.subheader("⏰ Auto-Refresh")
        
        # Toggle para ativar/desativar auto-refresh
        auto_refresh_enabled = st.sidebar.checkbox(
            "🔄 Ativar Atualização Automática",
            value=self.config.get('auto_refresh_enabled', True),
            help="Atualiza os dados automaticamente a cada 2 horas"
        )
        
        # Intervalo fixo de 2 horas
        refresh_interval = 7200  # 2 horas em segundos
        
        # Sistema de auto-refresh
        if auto_refresh_enabled:
            # Inicializa o timestamp se não existir
            if 'last_refresh_time' not in st.session_state:
                st.session_state.last_refresh_time = time.time()
            
            # Calcula tempo restante
            current_time_seconds = time.time()
            time_since_refresh = current_time_seconds - st.session_state.last_refresh_time
            time_remaining = refresh_interval - time_since_refresh
            
            # Mostra contador regressivo
            if time_remaining > 0:
                hours = int(time_remaining // 3600)
                minutes = int((time_remaining % 3600) // 60)
                seconds = int(time_remaining % 60)
                
                if hours > 0:
                    countdown_text = f"🕐 Próxima atualização em: {hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    countdown_text = f"🕐 Próxima atualização em: {minutes:02d}:{seconds:02d}"
                
                st.sidebar.info(countdown_text)
                
                # Para evitar travamento, atualiza apenas nos últimos segundos
                if time_remaining <= 3:
                    time.sleep(1)
                    st.rerun()
            else:
                # Hora de atualizar
                st.session_state.last_refresh_time = current_time_seconds
                force_refresh = True
                st.sidebar.success("🔄 Atualizando dados automaticamente...")
                st.rerun()
        
        # Informação sobre funcionamento
        if auto_refresh_enabled:
            st.sidebar.success("✅ Auto-refresh ativo: a cada 2 horas")
        else:
            st.sidebar.info("⏸️ Auto-refresh desativado")
        
        # Informação sobre auto-refresh
        st.sidebar.info("� Os filtros são aplicados instantaneamente usando cache")
        st.sidebar.info("🔄 Use 'Forçar Atualização' para buscar dados mais recentes")
        
        # Seção de timeframes
        st.sidebar.subheader("⏰ Timeframes")
        intervals = st.sidebar.multiselect(
            "Intervalos de tempo:",
            self.config['available_intervals'],
            default=self.config['default_intervals']
        )
        
        # Seção de filtros StochRSI
        st.sidebar.subheader("🎯 Filtros StochRSI %K")
        
        # Timeframes para aplicar filtros
        st.sidebar.subheader("📊 Timeframes para Filtro")
        filter_timeframes = st.sidebar.multiselect(
            "Selecione os timeframes para aplicar os filtros:",
            intervals,
            default=["1h", "4h"] if all(tf in intervals for tf in ["1h", "4h"]) else intervals[:2],
            help="Timeframes que serão usados nos filtros abaixo"
        )
        
        # Filtro: Todos Acima
        st.sidebar.subheader("📈 Filtro Geral - Todos Acima")
        enable_above = st.sidebar.checkbox("Ativar filtro 'Todos acima'", key="enable_above")
        if enable_above:
            value_above = st.sidebar.slider("Valor mínimo para os selecionados", 0, 100, 70, key="all_above")
        else:
            value_above = None
        
        # Filtro: Todos Abaixo
        st.sidebar.subheader("📉 Filtro Geral - Todos Abaixo")
        enable_below = st.sidebar.checkbox("Ativar filtro 'Todos abaixo'", key="enable_below")
        if enable_below:
            value_below = st.sidebar.slider("Valor máximo para os selecionados", 0, 100, 30, key="all_below")
        else:
            value_below = None
        
        # Filtro: Extremos
        st.sidebar.subheader("🎯 Filtro Extremos (abaixo/acima)")
        enable_extremos = st.sidebar.checkbox("Ativar filtro de extremos", key="enable_extremos")
        if enable_extremos:
            extremos_min, extremos_max = st.sidebar.slider(
                "Defina os valores dos extremos (mínimo e máximo)",
                0, 100, (30, 70), key="extremos_range"
            )
        else:
            extremos_min = extremos_max = None
        
        # Filtro: Intervalo Personalizado
        st.sidebar.subheader("🟩 Filtro Intervalo Personalizado (meio)")
        enable_intervalo = st.sidebar.checkbox("Ativar filtro de intervalo personalizado", key="enable_intervalo")
        if enable_intervalo:
            intervalo_min, intervalo_max = st.sidebar.slider(
                "Defina o intervalo central (mínimo e máximo)",
                0, 100, (30, 70), key="intervalo_range"
            )
        else:
            intervalo_min = intervalo_max = None
        
        # Configurar filtros
        stoch_filter = {
            'filter_timeframes': filter_timeframes,
            'enable_above': enable_above,
            'value_above': value_above,
            'enable_below': enable_below,
            'value_below': value_below,
            'enable_extremos': enable_extremos,
            'extremos_min': extremos_min,
            'extremos_max': extremos_max,
            'enable_intervalo': enable_intervalo,
            'intervalo_min': intervalo_min,
            'intervalo_max': intervalo_max
        }
        
        # Mostrar apenas sinais
        show_signals_only = st.sidebar.checkbox("Mostrar apenas sinais importantes", value=False)
        
        # Seção de parâmetros
        st.sidebar.subheader("🔧 Parâmetros")
        
        # Informação sobre cálculo automático de dias
        st.sidebar.info("📅 Dias de histórico calculados automaticamente para cada timeframe")
        
        # Controle de rate limiting
        st.sidebar.subheader("⚠️ Rate Limiting")
        delay_between_requests = st.sidebar.slider(
            "Delay entre requisições (ms):",
            min_value=50,  # Reduzido para aproveitar connection pool maior
            max_value=2000,
            value=300,  # Reduzido para ser mais eficiente
            step=50,
            help="Aumentar para evitar rate limiting da API (otimizado para connection pool de 50)"
        )
        
        batch_size = st.sidebar.slider(
            "Tamanho do lote:",
            min_value=5,
            max_value=50,
            value=30,  # Aumentado para aproveitar connection pool maior
            step=5,
            help="Número de pares processados por vez (otimizado para connection pool de 50)"
        )
        
        # Dicas de otimização
        requests_per_minute = (60000 / delay_between_requests) * batch_size if delay_between_requests > 0 else 0
        
        if batch_size > 40 and delay_between_requests < 200:
            st.sidebar.warning("⚠️ Configuração de alto risco! Pode resultar em ban da API.")
        elif batch_size <= 25 and delay_between_requests >= 250:
            st.sidebar.success("✅ Configuração segura para evitar rate limiting.")
        else:
            st.sidebar.info("ℹ️ Configuração moderada. Monitore os avisos de rate limiting.")
        
        st.sidebar.metric("📊 Taxa estimada", f"{requests_per_minute:.0f} req/min")
        st.sidebar.info("🔧 Connection pool: 50 conexões ativas")
        
        # Seção de configuração do Renko
        st.sidebar.subheader("🧱 Configuração Renko")
        
        # Opção para usar ATR dinâmico
        use_atr = st.sidebar.checkbox(
            "Usar ATR dinâmico para brick size",
            value=True,
            help="Calcula o brick size automaticamente baseado no ATR (Average True Range)"
        )
        
        if use_atr:
            atr_period = st.sidebar.slider(
                "Período do ATR:",
                min_value=7,
                max_value=30,
                value=14,
                step=1,
                help="Período para cálculo do ATR (padrão: 14 períodos)"
            )
            
            st.sidebar.info("📊 Brick size será calculado automaticamente baseado na volatilidade")
            brick_size = None  # Será calculado dinamicamente
        else:
            brick_size = st.sidebar.slider(
                "Tamanho do tijolo Renko:",
                min_value=50,
                max_value=2000,
                value=200,
                step=50,
                help="Tamanho do tijolo em pontos para cálculo do Renko"
            )
            atr_period = 14  # Valor padrão não usado
        
        # Opção para usar sempre Renko
        use_renko_always = st.sidebar.checkbox(
            "Usar sempre Renko para todos os timeframes",
            value=True,
            help="Quando ativado, usa Renko para todos os timeframes (recomendado)"
        )
        
        # Cache controls
        st.sidebar.subheader("💾 Cache de Sessão")
        
        # Informações do cache
        if st.session_state.updating_data:
            st.sidebar.warning("🔄 Atualizando dados...")
            st.sidebar.info("⚡ Interface continua funcional")
        elif st.session_state.data_timestamp:
            cache_age = (datetime.now() - st.session_state.data_timestamp).total_seconds() / 60
            cached_pairs = len(st.session_state.cached_data) if st.session_state.cached_data else 0
            st.sidebar.success(f"✅ Cache ativo: {cached_pairs} pares")
            
            if cache_age < 5:
                st.sidebar.success(f"⚡ Dados atuais: {cache_age:.1f} min")
            elif cache_age < 30:
                st.sidebar.info(f"⏰ Idade: {cache_age:.1f} min")
            else:
                st.sidebar.warning(f"⚠️ Dados antigos: {cache_age:.1f} min")
            
            # Botão para limpar cache da sessão
            if st.sidebar.button("🗑️ Limpar Cache Sessão", help="Remove dados da sessão atual"):
                st.session_state.cached_data = {}
                st.session_state.cached_matriz_stoch = {}
                st.session_state.data_timestamp = None
                st.session_state.last_config = {}
                st.session_state.updating_data = False
                st.success("🗑️ Cache da sessão limpo!")
                st.rerun()
        else:
            st.sidebar.warning("⚠️ Nenhum cache ativo")
            st.sidebar.info("💡 Dados serão carregados na primeira execução")
        
        st.sidebar.subheader("💾 Cache Arquivos")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("Limpar Cache"):
                self.data_manager.clear_cache()
                st.success("Cache limpo!")
        
        with col2:
            if st.button("Limpeza Auto"):
                self.data_manager.cleanup_cache()
                st.success("Limpeza automática!")
        
        # Informações do cache de arquivos
        cache_info = self.data_manager.get_cache_info()
        if cache_info.get('cache_enabled'):
            st.sidebar.info(f"📁 Cache arquivos: {cache_info.get('valid_files', 0)}/{cache_info.get('total_files', 0)} válidos")
        
        # Opção para usar cache em caso de erro
        use_cache_fallback = st.sidebar.checkbox(
            "Usar cache como fallback",
            value=True,
            help="Usa dados em cache (mesmo expirados) se API falhar"
        )
        
        return trading_pairs, intervals, brick_size, stoch_filter, show_signals_only, use_renko_always, delay_between_requests, batch_size, use_cache_fallback, use_atr, atr_period, force_refresh
    
    def render_main_content(self, trading_pairs, intervals, brick_size, stoch_filter, show_signals_only, use_renko_always, delay_between_requests, batch_size, use_cache_fallback, use_atr=True, atr_period=14, force_refresh=False):
        """Renderiza o conteúdo principal."""
        st.title("📊 Dashboard Crypto Filtering - Renko + StochRSI")
        st.markdown("Dev by aishend - Stochastic Renko Version ☕️")
        
        # Exibe informação sobre dados atuais
        current_time = datetime.now()
        st.info(f"🕐 **Dados atualizados até:** {current_time.strftime('%Y-%m-%d %H:%M:%S')} (momento atual)")
        
        if not trading_pairs:
            st.warning("⚠️ Nenhum par de trading carregado.")
            return
        
        if not intervals:
            st.warning("⚠️ Selecione pelo menos um intervalo de tempo na barra lateral.")
            return
        
        # Informações gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total de Pares", len(trading_pairs))
        
        with col2:
            st.metric("⏰ Timeframes", len(intervals))
        
        with col3:
            st.metric("🧱 Tamanho Tijolo", f"{brick_size}")
        
        with col4:
            st.metric("⚡ Delay (ms)", delay_between_requests)
        
        # Coleta dados com cache inteligente
        need_refresh = self.needs_data_refresh(trading_pairs, intervals, brick_size, use_atr, atr_period, force_refresh)
        
        # Primeiro mostra dados em cache se existirem (para o usuário não ficar sem ver nada)
        has_cached_data = st.session_state.cached_data and st.session_state.cached_matriz_stoch
        
        if has_cached_data and need_refresh:
            # Mostra dados anteriores enquanto carrega novos
            all_data, matriz_stoch = self.get_cached_data()
            
            # Aplica os filtros nos dados atuais primeiro para o usuário ver
            self.show_active_filters(stoch_filter)
            matriz_original = matriz_stoch.copy()
            matriz_stoch_filtered = self.apply_stoch_filter(matriz_stoch, stoch_filter, show_signals_only)
            
            # Mostra dados atuais enquanto atualiza
            if stoch_filter.get('filter_timeframes'):
                original_count = len(matriz_original)
                filtered_count = len(matriz_stoch_filtered)
                removed_count = original_count - filtered_count
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total de pares", original_count)
                with col2:
                    st.metric("✅ Pares filtrados", filtered_count)
                with col3:
                    st.metric("❌ Pares removidos", removed_count)
            
            # Exibe tabela atual primeiro
            st.subheader("📊 StochRSI %K - Todos os Pares (dados em cache)")
            self.display_simple_table_content(matriz_stoch_filtered, intervals)
            
            # Adiciona um botão para atualizar manualmente
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Atualizar Dados Agora", type="primary"):
                    # Marca que vai atualizar
                    st.session_state.updating_data = True
                    st.rerun()
            with col2:
                st.info("💡 Use o botão 'Forçar Atualização' na sidebar para atualizar automaticamente")
            
            # Se foi marcado para atualizar, faz a atualização
            if st.session_state.updating_data:
                with st.spinner("📡 Atualizando dados da API..."):
                    try:
                        # Monitora logs para detectar rate limiting
                        import logging
                        rate_limit_warnings = []
                        
                        # Captura logs de rate limiting
                        class RateLimitHandler(logging.Handler):
                            def emit(self, record):
                                if "Rate limit" in record.getMessage():
                                    rate_limit_warnings.append(record.getMessage())
                        
                        handler = RateLimitHandler()
                        binance_logger = logging.getLogger('src.api.binance_client')
                        binance_logger.addHandler(handler)
                        
                        all_data_new = self.get_data_with_brick_size(
                            trading_pairs, intervals, brick_size, batch_size, 
                            delay_between_requests / 1000, use_cache_fallback, force_refresh
                        )
                        
                        # Remove handler
                        binance_logger.removeHandler(handler)
                        
                        # Processa dados e calcula indicadores
                        matriz_stoch_new = self.process_data_matrix(all_data_new, intervals, brick_size, use_renko_always, use_atr, atr_period)
                        
                        # Armazena no cache
                        self.cache_data(trading_pairs, intervals, brick_size, use_atr, atr_period, all_data_new, matriz_stoch_new)
                        
                        # Marca que terminou de atualizar
                        st.session_state.updating_data = False
                        
                        # Mostra resultado da atualização
                        if rate_limit_warnings:
                            st.warning(f"⚠️ {len(rate_limit_warnings)} avisos de rate limiting durante atualização.")
                        else:
                            st.success(f"✅ Dados atualizados com sucesso: {len(all_data_new)} pares processados!")
                        
                        # Recarrega para mostrar novos dados
                        st.rerun()
                        
                    except Exception as e:
                        st.session_state.updating_data = False
                        st.error(f"❌ Erro durante atualização: {e}")
                        logger.error(f"Erro na atualização: {e}")
            
            # Para aqui para não processar novamente abaixo
            return
                
        elif need_refresh:
            with st.spinner("📡 Coletando novos dados da API..."):
                try:
                    # Monitora logs para detectar rate limiting
                    import logging
                    rate_limit_warnings = []
                    
                    # Captura logs de rate limiting
                    class RateLimitHandler(logging.Handler):
                        def emit(self, record):
                            if "Rate limit" in record.getMessage():
                                rate_limit_warnings.append(record.getMessage())
                    
                    handler = RateLimitHandler()
                    binance_logger = logging.getLogger('src.api.binance_client')
                    binance_logger.addHandler(handler)
                    
                    all_data = self.get_data_with_brick_size(
                        trading_pairs, intervals, brick_size, batch_size, delay_between_requests / 1000, use_cache_fallback, force_refresh
                    )
                    
                    # Remove handler
                    binance_logger.removeHandler(handler)
                    
                    # Processa dados e calcula indicadores
                    with st.spinner("🔍 Calculando indicadores StochRSI..."):
                        matriz_stoch = self.process_data_matrix(all_data, intervals, brick_size, use_renko_always, use_atr, atr_period)
                    
                    # Armazena no cache
                    self.cache_data(trading_pairs, intervals, brick_size, use_atr, atr_period, all_data, matriz_stoch)
                    
                    # Mostra resultado
                    if rate_limit_warnings:
                        st.warning(f"⚠️ {len(rate_limit_warnings)} avisos de rate limiting detectados. Considere aumentar o delay entre requisições.")
                        with st.expander("Ver avisos de rate limiting"):
                            for warning in rate_limit_warnings:
                                st.text(warning)
                    else:
                        st.success(f"✅ Dados coletados e armazenados no cache: {len(all_data)} pares processados!")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao coletar dados: {e}")
                    
                    # Sugestões para resolver problemas
                    st.markdown("""
                    **💡 Sugestões para resolver problemas:**
                    - Aumente o delay entre requisições (slider na sidebar)
                    - Reduza o tamanho do lote (slider na sidebar)
                    - Verifique sua conexão com a internet
                    - Aguarde alguns minutos antes de tentar novamente
                    """)
                    
                    logger.error(f"Erro ao coletar dados: {e}")
                    return
        else:
            # Usa dados do cache
            st.info("� **Usando dados do cache** - Alterações nos filtros são aplicadas instantaneamente!")
            all_data, matriz_stoch = self.get_cached_data()
        
        # Mostra filtros ativos
        self.show_active_filters(stoch_filter)
        
        # Aplica filtros
        matriz_original = matriz_stoch.copy()
        matriz_stoch = self.apply_stoch_filter(matriz_stoch, stoch_filter, show_signals_only)
        
        # Mostra estatísticas de filtragem
        if stoch_filter.get('filter_timeframes'):
            original_count = len(matriz_original)
            filtered_count = len(matriz_stoch)
            removed_count = original_count - filtered_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total de pares", original_count)
            with col2:
                st.metric("✅ Pares filtrados", filtered_count)
            with col3:
                st.metric("❌ Pares removidos", removed_count)
        
        # Exibe resultados em formato tabela simples
        self.display_simple_table(matriz_stoch, intervals)
        
        # Se estiver no modo teste, adiciona gráficos
        if self.mode == "test_mode":
            st.markdown("---")
            st.subheader("📈 Gráficos de Análise - Modo Teste")
            self.display_test_charts(all_data, intervals, brick_size, use_atr, atr_period)
        
        # Estatísticas resumidas
        self.display_summary_stats(matriz_stoch, intervals)
    
    def display_simple_table_content(self, matriz_stoch, intervals):
        """Exibe apenas o conteúdo da tabela simples (sem cabeçalho)."""
        if not matriz_stoch:
            st.warning("⚠️ Nenhum resultado para exibir após aplicar filtros.")
            return
        
        # Cria dados para a tabela
        table_data = []
        
        for symbol in sorted(matriz_stoch.keys()):
            row = [symbol]  # Primeira coluna é o par
            
            # Adiciona valores para cada timeframe
            for interval in intervals:
                data = matriz_stoch[symbol].get(interval)
                
                if data is None:
                    row.append("N/A")
                else:
                    k_value = data['StochRSI_%K']
                    
                    # Determina cor baseada no valor
                    if k_value < 20:
                        row.append(f"🟢 {k_value:.1f}")  # Oversold
                    elif k_value > 80:
                        row.append(f"🔴 {k_value:.1f}")  # Overbought
                    else:
                        row.append(f"{k_value:.1f}")  # Normal
            
            table_data.append(row)
        
        # Cria DataFrame
        columns = ["Par"] + intervals
        df = pd.DataFrame(table_data, columns=columns)
        
        # Função para colorir células
        def color_cells(val):
            if isinstance(val, str):
                if "🟢" in val:
                    return "background-color: #90EE90; color: black; font-weight: bold;"
                elif "🔴" in val:
                    return "background-color: #FFB6C1; color: black; font-weight: bold;"
                elif val == "N/A":
                    return "background-color: #f0f0f0; color: #666;"
            return ""
        
        # Aplica estilo
        styled_df = df.style.map(color_cells)
        
        # Exibe tabela
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Legenda
        st.markdown("""
        **Legenda:**
        - 🟢 **Oversold** (< 20) - Possível sinal de compra
        - 🔴 **Overbought** (> 80) - Possível sinal de venda
        - **Valores normais** (20-80) - Sem sinal específico
        """)
        
        return df

    def display_simple_table(self, matriz_stoch, intervals):
        """Exibe tabela simples com pares na primeira coluna e timeframes nas colunas seguintes."""
        if not matriz_stoch:
            st.warning("⚠️ Nenhum resultado para exibir após aplicar filtros.")
            return
        
        st.subheader("📊 StochRSI %K - Todos os Pares")
        return self.display_simple_table_content(matriz_stoch, intervals)
    
    def show_active_filters(self, stoch_filter):
        """Mostra filtros ativos na interface."""
        active_filters = []
        
        if stoch_filter.get('enable_above') and stoch_filter.get('value_above') is not None:
            active_filters.append(f"Todos os selecionados ≥ {stoch_filter['value_above']}")
        
        if stoch_filter.get('enable_below') and stoch_filter.get('value_below') is not None:
            active_filters.append(f"Todos os selecionados ≤ {stoch_filter['value_below']}")
        
        if stoch_filter.get('enable_extremos'):
            extremos_min = stoch_filter['extremos_min']
            extremos_max = stoch_filter['extremos_max']
            active_filters.append(f"Todos os selecionados ≤ {extremos_min} ou ≥ {extremos_max} (extremos)")
        
        if stoch_filter.get('enable_intervalo'):
            intervalo_min = stoch_filter['intervalo_min']
            intervalo_max = stoch_filter['intervalo_max']
            active_filters.append(f"Todos os selecionados entre {intervalo_min} e {intervalo_max} (intervalo personalizado)")
        
        if active_filters:
            st.success("🎯 **Filtros ativos:**")
            for filter_desc in active_filters:
                st.write(f"• {filter_desc}")
            
            if stoch_filter.get('filter_timeframes'):
                st.info(f"📊 **Timeframes para filtro:** {', '.join(stoch_filter['filter_timeframes'])}")
        else:
            st.info("ℹ️ Nenhum filtro ativo - mostrando todos os pares")
    
    def process_data_matrix(self, all_data, intervals, brick_size, use_renko_always=True, use_atr=True, atr_period=14):
        """Processa dados em formato de matriz com Renko para todos os timeframes."""
        matriz_stoch = {}
        
        for symbol in all_data:
            matriz_stoch[symbol] = {}
            
            for tf in intervals:
                try:
                    df = all_data[symbol][tf]
                    
                    if df.empty:
                        logger.warning(f"Dados vazios para {symbol} {tf}")
                        continue
                    
                    # Usar sempre Renko se especificado
                    if use_renko_always:
                        # Usar ATR dinâmico ou brick size fixo
                        if use_atr:
                            renko_df = gerar_renko(df, brick_size=None, symbol=symbol, use_atr=True, atr_period=atr_period)
                        else:
                            renko_df = gerar_renko(df, brick_size=brick_size, symbol=symbol, use_atr=False, atr_period=atr_period)
                        
                        if renko_df.empty:
                            logger.warning(f"Dados Renko vazios para {symbol} {tf}")
                            continue
                        closes = renko_df['close']
                        dates = pd.to_datetime(renko_df['date'])
                    else:
                        # Fallback para dados originais apenas para timeframes muito baixos
                        if tf == "1m":
                            closes = df['close']
                            dates = df.index
                        else:
                            renko_df = gerar_renko(df, brick_size)
                            if renko_df.empty:
                                logger.warning(f"Dados Renko vazios para {symbol} {tf}")
                                continue
                            closes = renko_df['close']
                            dates = pd.to_datetime(renko_df['date'])
                    
                    # Calcula StochRSI
                    stoch = stochrsi(closes)
                    stoch = stoch.dropna()
                    
                    if stoch.empty:
                        logger.warning(f"StochRSI vazio para {symbol} {tf}")
                        continue
                    
                    ultimo = stoch.iloc[-1]
                    ultima_data = dates.iloc[-1] if len(dates) > 0 else None
                    
                    matriz_stoch[symbol][tf] = {
                        "StochRSI_%K": round(ultimo['stochrsi_k'], 2),
                        "StochRSI_%D": round(ultimo['stochrsi_d'], 2),
                        "Signal": self.get_signal(ultimo['stochrsi_k'], ultimo['stochrsi_d']),
                        "Datetime": ultima_data.strftime('%Y-%m-%d %H:%M') if ultima_data else "N/A",
                        "Data_Points": len(closes)
                    }
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {symbol} {tf}: {e}")
                    continue
        
        return matriz_stoch
    
    def get_signal(self, k_value, d_value):
        """Determina sinal baseado nos valores K e D."""
        if k_value < 20 and d_value < 20:
            return "🟢 Oversold"
        elif k_value > 80 and d_value > 80:
            return "🔴 Overbought"
        elif k_value > d_value:
            return "⬆️ Bullish"
        else:
            return "⬇️ Bearish"
    
    def display_results(self, resultados):
        """Exibe resultados em tabela."""
        if not resultados:
            st.warning("⚠️ Nenhum resultado para exibir.")
            return
        
        st.subheader("📈 Análise StochRSI")
        
        # Converte para DataFrame
        df_resultados = pd.DataFrame(resultados)
        
        # Estiliza a tabela
        def style_signal(val):
            if "Oversold" in val:
                return "background-color: #90EE90"
            elif "Overbought" in val:
                return "background-color: #FFB6C1"
            elif "Bullish" in val:
                return "background-color: #87CEEB"
            elif "Bearish" in val:
                return "background-color: #F0E68C"
            return ""
        
        styled_df = df_resultados.style.map(style_signal, subset=['Signal'])        
        st.dataframe(styled_df, use_container_width=True)
        
        # Estatísticas resumidas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            oversold_count = sum(1 for r in resultados if "Oversold" in r['Signal'])
            st.metric("🟢 Oversold", oversold_count)
        
        with col2:
            overbought_count = sum(1 for r in resultados if "Overbought" in r['Signal'])
            st.metric("🔴 Overbought", overbought_count)
        
        with col3:
            bullish_count = sum(1 for r in resultados if "Bullish" in r['Signal'])
            st.metric("⬆️ Bullish", bullish_count)
    
    def render_detailed_analysis(self, all_data, intervals, brick_size, use_renko_always=True):
        """Renderiza análise detalhada."""
        st.subheader("🔍 Análise Detalhada")
        
        # Seletor de par para análise detalhada
        symbols = list(all_data.keys())
        if not symbols:
            return
        
        selected_symbol = st.selectbox("Selecione um par para análise:", symbols)
        
        if selected_symbol:
            symbol_data = all_data[selected_symbol]
            
            # Tabs para diferentes timeframes
            tabs = st.tabs(intervals)
            
            for i, interval in enumerate(intervals):
                with tabs[i]:
                    df = symbol_data[interval]
                    
                    if df.empty:
                        st.warning(f"Sem dados para {selected_symbol} {interval}")
                        continue
                    
                    # Mostra últimos dados
                    st.write(f"**Últimos dados - {selected_symbol} {interval}:**")
                    st.dataframe(df.tail(10))
                    
                    # Mostra dados Renko se usar_renko_always ou não for 1m
                    if use_renko_always or interval != "1m":
                        renko_df = gerar_renko(df, brick_size)
                        if not renko_df.empty:
                            st.write(f"**Dados Renko (últimos 10 tijolos):**")
                            st.dataframe(renko_df.tail(10))
    
    def get_data_with_brick_size(self, trading_pairs, intervals, brick_size, batch_size, delay_between_requests, use_cache_fallback, force_refresh=False):
        """
        Obtém dados considerando brick_size para cálculo otimizado.
        
        Args:
            trading_pairs: Lista de pares de trading
            intervals: Lista de intervalos
            brick_size: Tamanho do tijolo Renko
            batch_size: Tamanho do lote
            delay_between_requests: Delay entre requisições
            use_cache_fallback: Usar cache como fallback
            force_refresh: Forçar busca nova da API
            
        Returns:
            Dict com dados coletados
        """
        all_data = {}
        
        # Coleta dados para cada par individualmente para poder passar brick_size
        for symbol in trading_pairs:
            all_data[symbol] = {}
            for interval in intervals:
                try:
                    # Usa o método atualizado que considera brick_size e busca dados atuais
                    # Se force_refresh é True, força busca nova mesmo com cache válido
                    data = self.data_manager.get_symbol_data(
                        symbol, 
                        interval, 
                        brick_size=brick_size,
                        extend_to_current=True,  # Sempre busca dados até o momento atual
                        force_cache=False if force_refresh else None  # Se force_refresh, não usa cache
                    )
                    all_data[symbol][interval] = data
                    
                    if not data.empty:
                        # Mostra informação sobre o último candle
                        last_time = data.index[-1]
                        current_time = datetime.now()
                        
                        # Calcula diferença em minutos
                        if hasattr(last_time, 'to_pydatetime'):
                            last_time = last_time.to_pydatetime()
                        
                        diff_minutes = (current_time - last_time).total_seconds() / 60
                        
                        logger.info(f"Dados obtidos para {symbol} {interval}: {len(data)} registros")
                        logger.info(f"Último candle: {last_time} (há {diff_minutes:.1f} minutos)")
                        
                        # Aviso se dados estão muito antigos
                        if diff_minutes > 60:  # Mais de 1 hora
                            logger.warning(f"Dados podem estar desatualizados para {symbol} {interval}")
                    else:
                        logger.warning(f"Nenhum dado obtido para {symbol} {interval}")
                        
                except Exception as e:
                    logger.error(f"Erro ao obter dados para {symbol} {interval}: {e}")
                    all_data[symbol][interval] = pd.DataFrame()
                    
                # Delay entre requisições
                if delay_between_requests > 0:
                    time.sleep(delay_between_requests)
        
        return all_data

    # ...existing code...
    
    def apply_stoch_filter(self, matriz_stoch, stoch_filter, show_signals_only):
        """Aplica filtros baseados no StochRSI %K seguindo o exemplo fornecido."""
        if not stoch_filter.get('filter_timeframes'):
            return matriz_stoch
        
        filtered_matriz = {}
        filter_timeframes = stoch_filter['filter_timeframes']
        
        for symbol, intervals_data in matriz_stoch.items():
            include_symbol = True
            
            # Coleta valores StochRSI para os timeframes selecionados
            stoch_values = []
            for tf in filter_timeframes:
                if tf in intervals_data and intervals_data[tf] is not None:
                    stoch_values.append(intervals_data[tf]['StochRSI_%K'])
                else:
                    include_symbol = False
                    break
            
            # Aplica filtros se há dados suficientes
            if include_symbol and stoch_values:
                # Filtro: Todos Acima
                if stoch_filter['enable_above'] and stoch_filter['value_above'] is not None:
                    if not all(v >= stoch_filter['value_above'] for v in stoch_values):
                        include_symbol = False
                
                # Filtro: Todos Abaixo
                if stoch_filter['enable_below'] and stoch_filter['value_below'] is not None:
                    if not all(v <= stoch_filter['value_below'] for v in stoch_values):
                        include_symbol = False
                
                # Filtro: Extremos (todos devem estar abaixo do min OU acima do max)
                if stoch_filter['enable_extremos'] and stoch_filter['extremos_min'] is not None:
                    extremos_min = stoch_filter['extremos_min']
                    extremos_max = stoch_filter['extremos_max']
                    if not all((v <= extremos_min or v >= extremos_max) for v in stoch_values):
                        include_symbol = False
                
                # Filtro: Intervalo Personalizado (todos devem estar dentro do intervalo)
                if stoch_filter['enable_intervalo'] and stoch_filter['intervalo_min'] is not None:
                    intervalo_min = stoch_filter['intervalo_min']
                    intervalo_max = stoch_filter['intervalo_max']
                    if not all((intervalo_min <= v <= intervalo_max) for v in stoch_values):
                        include_symbol = False
            
            # Filtro adicional para mostrar apenas sinais importantes
            if show_signals_only and include_symbol:
                has_important_signal = False
                for tf_data in intervals_data.values():
                    if tf_data is not None:
                        signal = tf_data['Signal']
                        if "Oversold" in signal or "Overbought" in signal:
                            has_important_signal = True
                            break
                if not has_important_signal:
                    include_symbol = False
            
            # Inclui o símbolo se passou em todos os filtros
            if include_symbol:
                filtered_matriz[symbol] = intervals_data
        
        return filtered_matriz
    
    def display_matrix_results(self, matriz_stoch, intervals):
        """Exibe resultados em formato de matriz."""
        if not matriz_stoch:
            st.warning("⚠️ Nenhum resultado para exibir após aplicar filtros.")
            return
        
        st.subheader("📊 Matriz StochRSI %K por Par/Timeframe")
        
        # Cria DataFrame para exibição
        display_data = []
        
        for symbol in sorted(matriz_stoch.keys()):
            row = {"Par": symbol}
            
            for interval in intervals:
                data = matriz_stoch[symbol].get(interval)
                
                if data is None:
                    row[interval] = "N/A"
                else:
                    k_value = data['StochRSI_%K']
                    signal = data['Signal']
                    
                    # Formata valor com emoji baseado no sinal
                    if "Oversold" in signal:
                        row[interval] = f"🟢 {k_value:.1f}"
                    elif "Overbought" in signal:
                        row[interval] = f"🔴 {k_value:.1f}"
                    elif "Bullish" in signal:
                        row[interval] = f"⬆️ {k_value:.1f}"
                    else:
                        row[interval] = f"⬇️ {k_value:.1f}"
            
            display_data.append(row)
        
        # Converte para DataFrame
        df_matrix = pd.DataFrame(display_data)
        
        # Função para colorir as células
        def color_cells(val):
            if isinstance(val, str):
                if "🟢" in val:
                    return "background-color: #90EE90; color: black;"
                elif "🔴" in val:
                    return "background-color: #FFB6C1; color: black;"
                elif "⬆️" in val:
                    return "background-color: #87CEEB; color: black;"
                elif "⬇️" in val:
                    return "background-color: #F0E68C; color: black;"
            return ""
        
        # Aplica estilo
        styled_df = df_matrix.style.map(color_cells)
        
        # Exibe tabela
        st.dataframe(styled_df, use_container_width=True)
        
        # Adiciona legenda
        st.markdown("""
        **Legenda:**
        - 🟢 Oversold (< 20) - Possível compra
        - 🔴 Overbought (> 80) - Possível venda  
        - ⬆️ Bullish - Tendência de alta
        - ⬇️ Bearish - Tendência de baixa
        """)
        
        return df_matrix
    
    def display_summary_stats(self, matriz_stoch, intervals):
        """Exibe estatísticas resumidas."""
        if not matriz_stoch:
            return
        
        st.subheader("📊 Estatísticas Resumidas")
        
        # Conta sinais por tipo
        oversold_count = 0
        overbought_count = 0
        normal_count = 0
        na_count = 0
        total_signals = 0
        
        for symbol, intervals_data in matriz_stoch.items():
            for interval, data in intervals_data.items():
                total_signals += 1
                
                if data is None:
                    na_count += 1
                else:
                    k_value = data['StochRSI_%K']
                    
                    if k_value < 20:
                        oversold_count += 1
                    elif k_value > 80:
                        overbought_count += 1
                    else:
                        normal_count += 1
        
        # Exibe métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Total", total_signals)
        
        with col2:
            st.metric("🟢 Oversold", oversold_count)
        
        with col3:
            st.metric("🔴 Overbought", overbought_count)
        
        with col4:
            st.metric("⚪ Normal", normal_count)
        
        with col5:
            st.metric("❌ N/A", na_count)
        
        # Gráfico de distribuição
        if total_signals > 0:
            signal_data = {
                'Oversold': oversold_count,
                'Overbought': overbought_count,
                'Normal': normal_count,
                'N/A': na_count
            }
            
            st.bar_chart(signal_data)
    
    def render_detailed_analysis(self, all_data, intervals, brick_size, use_renko_always=True):
        """Renderiza análise detalhada."""
        st.subheader("🔍 Análise Detalhada")
        
        # Seletor de par para análise detalhada
        symbols = list(all_data.keys())
        if not symbols:
            return
        
        selected_symbol = st.selectbox("Selecione um par para análise:", symbols)
        
        if selected_symbol:
            symbol_data = all_data[selected_symbol]
            
            # Tabs para diferentes timeframes
            tabs = st.tabs(intervals)
            
            for i, interval in enumerate(intervals):
                with tabs[i]:
                    df = symbol_data[interval]
                    
                    if df.empty:
                        st.warning(f"Sem dados para {selected_symbol} {interval}")
                        continue
                    
                    # Mostra últimos dados
                    st.write(f"**Últimos dados - {selected_symbol} {interval}:**")
                    st.dataframe(df.tail(10))
                    
                    # Mostra dados Renko se usar sempre Renko ou não for 1m
                    if use_renko_always or interval != "1m":
                        renko_df = gerar_renko(df, brick_size)
                        if not renko_df.empty:
                            st.write(f"**Dados Renko (últimos 10 tijolos):**")
                            st.dataframe(renko_df.tail(10))
    
    def display_test_charts(self, all_data, intervals, brick_size, use_atr, atr_period):
        """Exibe gráficos detalhados no modo teste."""
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        
        # Pega os pares de teste
        test_pairs = get_trading_pairs_for_mode("test_mode")
        
        # Cria abas para cada par
        tabs = st.tabs([f"📊 {pair}" for pair in test_pairs])
        
        for i, (tab, symbol) in enumerate(zip(tabs, test_pairs)):
            with tab:
                if symbol not in all_data:
                    st.warning(f"⚠️ Dados não disponíveis para {symbol}")
                    continue
                
                # Cria sub-abas para cada timeframe
                tf_tabs = st.tabs([f"⏰ {tf}" for tf in intervals])
                
                for j, (tf_tab, interval) in enumerate(zip(tf_tabs, intervals)):
                    with tf_tab:
                        if interval not in all_data[symbol]:
                            st.warning(f"⚠️ Dados não disponíveis para {symbol} {interval}")
                            continue
                        
                        df = all_data[symbol][interval]
                        
                        if df.empty:
                            st.warning(f"⚠️ DataFrame vazio para {symbol} {interval}")
                            continue
                        
                        # Gera dados Renko
                        renko_df = gerar_renko(
                            df, 
                            brick_size=brick_size if not use_atr else None,
                            symbol=symbol,
                            use_atr=use_atr,
                            atr_period=atr_period
                        )
                        
                        if renko_df.empty:
                            st.warning(f"⚠️ Erro ao gerar Renko para {symbol} {interval}")
                            continue
                        
                        # Calcula StochRSI - verifica qual coluna usar
                        close_col = 'Close' if 'Close' in renko_df.columns else 'close'
                        if close_col in renko_df.columns:
                            stoch_df = stochrsi(renko_df[close_col])
                        else:
                            st.error(f"❌ Coluna 'close' não encontrada no DataFrame Renko: {list(renko_df.columns)}")
                            continue
                        
                        # Layout em duas colunas
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**📊 Gráfico de Preços - {symbol} {interval}**")
                            
                            # Gráfico de candlestick dos dados originais
                            fig_candle = go.Figure()
                            
                            # Limita a 200 últimas barras para melhor visualização
                            df_plot = df.tail(200)
                            
                            # Verifica se as colunas existem (podem ser maiúsculas ou minúsculas)
                            open_col = 'Open' if 'Open' in df_plot.columns else 'open'
                            high_col = 'High' if 'High' in df_plot.columns else 'high'
                            low_col = 'Low' if 'Low' in df_plot.columns else 'low'
                            close_col = 'Close' if 'Close' in df_plot.columns else 'close'
                            
                            if all(col in df_plot.columns for col in [open_col, high_col, low_col, close_col]):
                                fig_candle.add_trace(go.Candlestick(
                                    x=df_plot.index,
                                    open=df_plot[open_col],
                                    high=df_plot[high_col],
                                    low=df_plot[low_col],
                                    close=df_plot[close_col],
                                    name=f"{symbol} Candlestick"
                                ))
                                
                                fig_candle.update_layout(
                                    title=f"{symbol} {interval} - Candlestick",
                                    xaxis_title="Data",
                                    yaxis_title="Preço",
                                    height=400,
                                    showlegend=False
                                )
                                
                                st.plotly_chart(fig_candle, use_container_width=True)
                            else:
                                st.error(f"❌ Colunas OHLC não encontradas no DataFrame: {list(df_plot.columns)}")
                                st.write(f"Colunas disponíveis: {list(df_plot.columns)}")
                        
                        with col2:
                            st.write(f"**🧱 Gráfico Renko - {symbol} {interval}**")
                            
                            # Gráfico Renko
                            fig_renko = go.Figure()
                            
                            # Limita a 100 últimos tijolos
                            renko_plot = renko_df.tail(100)
                            
                            # Verifica se as colunas existem no DataFrame Renko
                            open_col = 'Open' if 'Open' in renko_plot.columns else 'open'
                            high_col = 'High' if 'High' in renko_plot.columns else 'high'
                            low_col = 'Low' if 'Low' in renko_plot.columns else 'low'
                            close_col = 'Close' if 'Close' in renko_plot.columns else 'close'
                            
                            if all(col in renko_plot.columns for col in [open_col, high_col, low_col, close_col]):
                                # Cores para tijolos (verde para alta, vermelho para baixa)
                                colors = ['green' if close >= open else 'red' 
                                         for open, close in zip(renko_plot[open_col], renko_plot[close_col])]
                                
                                fig_renko.add_trace(go.Candlestick(
                                    x=renko_plot.index,
                                    open=renko_plot[open_col],
                                    high=renko_plot[high_col],
                                    low=renko_plot[low_col],
                                    close=renko_plot[close_col],
                                    name=f"{symbol} Renko"
                                ))
                                
                                fig_renko.update_layout(
                                    title=f"{symbol} {interval} - Renko ({len(renko_df)} tijolos)",
                                    xaxis_title="Índice",
                                    yaxis_title="Preço",
                                    height=400,
                                    showlegend=False
                                )
                                
                                st.plotly_chart(fig_renko, use_container_width=True)
                            else:
                                st.error(f"❌ Colunas OHLC não encontradas no DataFrame Renko: {list(renko_plot.columns)}")
                        
                        # Gráfico do StochRSI (full width)
                        if not stoch_df.empty:
                            st.write(f"**🎯 StochRSI - {symbol} {interval}**")
                            
                            fig_stoch = make_subplots(
                                rows=2, cols=1,
                                subplot_titles=('Preço Renko', 'StochRSI'),
                                vertical_spacing=0.25,  # Aumentado significativamente
                                row_heights=[0.6, 0.4],  # Mais espaço para o StochRSI
                                specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
                            )
                            
                            # Subplot 1: Preço Renko
                            renko_plot = renko_df.tail(100)
                            
                            # Verifica colunas novamente para o StochRSI
                            open_col = 'Open' if 'Open' in renko_plot.columns else 'open'
                            high_col = 'High' if 'High' in renko_plot.columns else 'high'
                            low_col = 'Low' if 'Low' in renko_plot.columns else 'low'
                            close_col = 'Close' if 'Close' in renko_plot.columns else 'close'
                            
                            if all(col in renko_plot.columns for col in [open_col, high_col, low_col, close_col]):
                                # Apenas o gráfico Candlestick no subplot superior
                                fig_stoch.add_trace(
                                    go.Candlestick(
                                        x=renko_plot.index,
                                        open=renko_plot[open_col],
                                        high=renko_plot[high_col],
                                        low=renko_plot[low_col],
                                        close=renko_plot[close_col],
                                        name="Renko",
                                        showlegend=False
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
                                title=f"{symbol} {interval} - Análise Completa",
                                height=750,  # Aumentado para dar mais espaço
                                showlegend=True,
                                margin=dict(l=40, r=40, t=80, b=60)  # Margens maiores
                            )
                            
                            # Configurações específicas para cada subplot
                            fig_stoch.update_yaxes(title_text="Preço (USD)", row=1, col=1)
                            fig_stoch.update_yaxes(title_text="StochRSI (%)", row=2, col=1, range=[0, 100])
                            fig_stoch.update_xaxes(title_text="", row=1, col=1, showticklabels=False)
                            fig_stoch.update_xaxes(title_text="Tempo", row=2, col=1)
                            
                            # Remove grid excessivo
                            fig_stoch.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                            fig_stoch.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                            
                            # Ajusta os títulos dos subplots para não ocupar tanto espaço
                            fig_stoch.update_annotations(font_size=12)
                            
                            st.plotly_chart(fig_stoch, use_container_width=True)
                            
                            # Métricas atuais
                            if len(stoch_df) > 0:
                                last_k = stoch_df['stochrsi_k'].iloc[-1]
                                last_d = stoch_df['stochrsi_d'].iloc[-1]
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("📊 Tijolos Renko", len(renko_df))
                                with col2:
                                    st.metric("🎯 StochRSI %K", f"{last_k:.1f}")
                                with col3:
                                    st.metric("🎯 StochRSI %D", f"{last_d:.1f}")
                                with col4:
                                    if last_k > 80:
                                        st.metric("🚨 Sinal", "Sobrecompra", delta="Venda")
                                    elif last_k < 20:
                                        st.metric("🚨 Sinal", "Sobrevenda", delta="Compra")
                                    else:
                                        st.metric("🚨 Sinal", "Neutro", delta="Aguardar")
                        else:
                            st.warning("⚠️ Erro ao calcular StochRSI - dados insuficientes")
                        
                        st.markdown("---")
    
    def run(self):
        """Executa o dashboard."""
        try:
            # Renderiza sidebar
            trading_pairs, intervals, brick_size, stoch_filter, show_signals_only, use_renko_always, delay_between_requests, batch_size, use_cache_fallback, use_atr, atr_period, force_refresh = self.render_sidebar()
            
            # Renderiza conteúdo principal
            self.render_main_content(trading_pairs, intervals, brick_size, stoch_filter, show_signals_only, use_renko_always, delay_between_requests, batch_size, use_cache_fallback, use_atr, atr_period, force_refresh)
            
        except Exception as e:
            st.error(f"❌ Erro no dashboard: {e}")
            logger.error(f"Erro no dashboard: {e}")
            import traceback
            st.error(traceback.format_exc())

# Execução do dashboard
if __name__ == "__main__":
    dashboard = TradingDashboard()
    dashboard.run()
