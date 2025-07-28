"""
Patch para adicionar auto-refresh ao dashboard.
Este código deve ser integrado na função render_sidebar do dashboard.py
"""

# Adicionar este código logo após a linha atual de force_refresh

def add_auto_refresh_to_sidebar(self, force_refresh_current):
    """
    Adiciona funcionalidade de auto-refresh ao sidebar.
    Esta função deve ser chamada na render_sidebar depois do botão force_refresh.
    """
    # Seção de Auto-Refresh
    st.sidebar.subheader("⏰ Auto-Refresh")
    
    # Toggle para ativar/desativar auto-refresh
    auto_refresh_enabled = st.sidebar.checkbox(
        "🔄 Ativar Atualização Automática",
        value=self.config.get('auto_refresh_enabled', True),
        help="Atualiza os dados automaticamente no intervalo selecionado"
    )
    
    # Seletor de intervalo de auto-refresh
    refresh_options = self.config.get('auto_refresh_options', {
        '30 minutos': 1800,
        '1 hora': 3600,
        '2 horas': 7200,
        '4 horas': 14400,
        '6 horas': 21600,
        '12 horas': 43200,
        '24 horas': 86400
    })
    
    default_interval = self.config.get('auto_refresh_interval', 7200)
    default_label = next((k for k, v in refresh_options.items() if v == default_interval), '2 horas')
    
    refresh_interval_label = st.sidebar.selectbox(
        "⏱️ Intervalo de Atualização:",
        options=list(refresh_options.keys()),
        index=list(refresh_options.keys()).index(default_label),
        help="Escolha com que frequência os dados devem ser atualizados automaticamente"
    )
    
    refresh_interval = refresh_options[refresh_interval_label]
    
    # Sistema de auto-refresh
    force_refresh = force_refresh_current  # Mantém o valor do botão manual
    
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
            
            # Atualiza o contador (mas não com sleep, pois travaria a UI)
            # Em vez disso, use o auto-refresh do streamlit com fragment
            import streamlit as st
            
            # Agenda próxima atualização
            if time_remaining <= 5:  # Nos últimos 5 segundos
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
        st.sidebar.success(f"✅ Auto-refresh ativo: {refresh_interval_label}")
    else:
        st.sidebar.info("⏸️ Auto-refresh desativado")
    
    st.sidebar.info("💡 Os filtros são aplicados instantaneamente usando cache")
    
    return force_refresh
