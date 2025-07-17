# binance_client.py
import os
import logging
import nest_asyncio
import pandas as pd
import time
import threading
from datetime import datetime, timedelta
from binance import Client, ThreadedWebsocketManager
from typing import Dict, Optional, Callable

# Aplica nest_asyncio para permitir loops aninhados
nest_asyncio.apply()

# Configuração do logging
logging.basicConfig(level=logging.INFO)

# Controle ULTRA-RIGOROSO de rate limiting para requisições REST
class RateLimiter:
    def __init__(self, max_requests_per_minute=1500):  # REDUZIDO para 1500 (super seguro)
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
        self.last_ban_time = None
        self.ban_duration = 60  # 1 minuto inicial
        self.request_count = 0
        self.window_start = datetime.now()
        self.blocked_count = 0
        self.emergency_mode = False
    
    def _clean_old_requests(self):
        """Remove requisições antigas (mais de 1 minuto)"""
        now = datetime.now()
        self.requests = [req_time for req_time in self.requests if (now - req_time).total_seconds() < 60]
        
        # Reseta contador se janela expirou
        if (now - self.window_start).total_seconds() >= 60:
            self.request_count = len(self.requests)
            self.window_start = now
    
    def can_make_request(self):
        """Verifica se pode fazer requisição SEM fazê-la"""
        with self.lock:
            self._clean_old_requests()
            
            # Verifica ban
            if self.last_ban_time:
                elapsed = (datetime.now() - self.last_ban_time).total_seconds()
                if elapsed < self.ban_duration:
                    return False
            
            # Modo emergência: bloqueia TUDO
            if self.emergency_mode:
                return False
                
            # Verifica limite com margem EXTRA de segurança
            return len(self.requests) < (self.max_requests - 100)  # Margem de 100 requests
    
    def wait_if_needed(self):
        """Aguarda se necessário para respeitar o rate limit - NUNCA PERMITE EXCEDER"""
        with self.lock:
            now = datetime.now()
            
            # Verifica se estamos em período de ban
            if self.last_ban_time:
                elapsed = (now - self.last_ban_time).total_seconds()
                if elapsed < self.ban_duration:
                    remaining_ban = self.ban_duration - elapsed
                    logging.error(f"🚫 SISTEMA BLOQUEADO - Ban ativo. Aguardando {remaining_ban:.1f} segundos...")
                    time.sleep(remaining_ban)
                    self.last_ban_time = None
            
            # Modo emergência: bloqueia TUDO por 5 minutos
            if self.emergency_mode:
                logging.error("🚨 MODO EMERGÊNCIA ATIVO - Bloqueando TODAS as requisições por 5 minutos")
                time.sleep(300)  # 5 minutos
                self.emergency_mode = False
                self.requests = []
                self.request_count = 0
                self.window_start = datetime.now()
            
            # Limpa requisições antigas
            self._clean_old_requests()
            
            # BLOQUEIA COMPLETAMENTE se atingir limite COM MARGEM
            safety_limit = self.max_requests - 100  # Margem de 100 requests
            while len(self.requests) >= safety_limit:
                oldest_request = min(self.requests) if self.requests else now
                wait_time = 60 - (now - oldest_request).total_seconds() + 5  # +5 segundos de segurança
                
                if wait_time > 0:
                    self.blocked_count += 1
                    logging.error(f"🛑 LIMITE ULTRA-PREVENTIVO ATINGIDO ({len(self.requests)}/{self.max_requests})")
                    logging.error(f"🛑 Aguardando {wait_time:.1f} segundos... (bloqueio #{self.blocked_count})")
                    time.sleep(wait_time)
                    now = datetime.now()
                    self._clean_old_requests()
                else:
                    break
            
            # Delay mínimo entre requisições (aumentado)
            if self.requests:
                last_request = max(self.requests)
                min_delay = 0.3  # 300ms entre requisições (aumentado)
                elapsed = (now - last_request).total_seconds()
                if elapsed < min_delay:
                    time.sleep(min_delay - elapsed)
            
            # Registra a requisição ANTES de fazê-la
            self.requests.append(datetime.now())
            self.request_count += 1
            
            # Log de monitoramento mais frequente
            if len(self.requests) > self.max_requests * 0.7:  # 70% do limite
                logging.warning(f"⚠️ LIMITE PRÓXIMO: {len(self.requests)}/{self.max_requests} requisições")
                
            # Ativa modo emergência se muito próximo do limite
            if len(self.requests) > self.max_requests * 0.9:  # 90% do limite
                logging.error(f"🚨 ATIVANDO MODO EMERGÊNCIA - Muito próximo do limite!")
                self.emergency_mode = True
    
    def register_ban(self):
        """Registra que ocorreu um ban para ajustar comportamento"""
        with self.lock:
            self.last_ban_time = datetime.now()
            self.ban_duration = min(self.ban_duration * 2, 600)  # Aumenta até 10 minutos
            logging.error(f"🚨 BAN REGISTRADO! Próxima duração: {self.ban_duration} segundos")
            logging.error(f"🚨 Requests na janela: {len(self.requests)}")
            self.requests = []  # Limpa todas as requisições
            self.request_count = 0
    
    def get_stats(self):
        """Retorna estatísticas do rate limiter"""
        with self.lock:
            self._clean_old_requests()
            now = datetime.now()
            return {
                'current_requests': len(self.requests),
                'max_requests': self.max_requests,
                'usage_percent': (len(self.requests) / self.max_requests) * 100,
                'blocked_count': self.blocked_count,
                'is_banned': self.last_ban_time is not None and 
                           (now - self.last_ban_time).total_seconds() < self.ban_duration,
                'ban_remaining': self.ban_duration - (now - self.last_ban_time).total_seconds() 
                               if self.last_ban_time else 0
            }

def handle_binance_error(error, symbol=None, operation="unknown"):
    """
    Manipula erros da API Binance de forma centralizada.
    
    Args:
        error: Exceção capturada
        symbol: Símbolo relacionado ao erro (opcional)
        operation: Operação que causou o erro
        
    Returns:
        tuple: (should_retry, wait_time, error_type)
    """
    error_msg = str(error).lower()
    symbol_info = f" para {symbol}" if symbol else ""
    
    # Erro -1003: Rate limit / IP banido
    if "1003" in error_msg or "too many requests" in error_msg or "ip banned" in error_msg:
        logging.error(f"🚨 RATE LIMIT/BAN detectado em {operation}{symbol_info}")
        rate_limiter.register_ban()
        return False, 300, "rate_limit"  # Não retry, 5 minutos de espera
    
    # Erro -1121: Símbolo inválido
    elif "1121" in error_msg or "invalid symbol" in error_msg:
        logging.error(f"❌ Símbolo inválido em {operation}{symbol_info}")
        return False, 0, "invalid_symbol"  # Não retry
    
    # Erro -2013: Ordem não encontrada
    elif "2013" in error_msg or "order does not exist" in error_msg:
        logging.warning(f"⚠️ Ordem não encontrada em {operation}{symbol_info}")
        return False, 0, "order_not_found"  # Não retry
    
    # Erro -1000: Erro interno do servidor
    elif "1000" in error_msg or "internal error" in error_msg:
        logging.warning(f"🔧 Erro interno do servidor em {operation}{symbol_info}")
        return True, 5, "server_error"  # Retry após 5 segundos
    
    # Erro de conexão/timeout
    elif "connection" in error_msg or "timeout" in error_msg or "read timed out" in error_msg:
        logging.warning(f"🌐 Erro de conexão em {operation}{symbol_info}")
        return True, 3, "connection_error"  # Retry após 3 segundos
    
    # Outros erros
    else:
        logging.error(f"❓ Erro desconhecido em {operation}{symbol_info}: {error}")
        return True, 2, "unknown_error"  # Retry após 2 segundos

# Instância global do rate limiter
rate_limiter = RateLimiter()

# Lógica para carregar KEY e SECRET de variáveis de ambiente ou do config.py
KEY = os.environ.get('BINANCE_KEY')
SECRET = os.environ.get('BINANCE_SECRET')

if not KEY or not SECRET:
    try:
        # Tenta importar das configurações do sistema
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from config.settings import BINANCE_CONFIG
        KEY = BINANCE_CONFIG['KEY']
        SECRET = BINANCE_CONFIG['SECRET']
    except (ImportError, KeyError) as e:
        try:
            # Tenta importar do arquivo config.py local
            config_path = os.path.join(os.path.dirname(__file__), 'config.py')
            if os.path.exists(config_path):
                # Adiciona o diretório ao sys.path temporariamente
                import sys
                import importlib.util
                spec = importlib.util.spec_from_file_location("local_config", config_path)
                local_config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(local_config)
                KEY = local_config.KEY
                SECRET = local_config.SECRET
            else:
                raise ImportError("Config file not found")
        except (ImportError, AttributeError):
            # Cria o arquivo config.py se não existir
            config_path = os.path.join(os.path.dirname(__file__), 'config.py')
            if not os.path.exists(config_path):
                with open(config_path, 'w') as f:
                    f.write('KEY = "COLOQUE_SUA_BINANCE_API_KEY_AQUI"\n')
                    f.write('SECRET = "COLOQUE_SUA_BINANCE_API_SECRET_AQUI"\n')
                print(f"Arquivo config.py criado em {config_path}. Coloque sua KEY e SECRET nele.")
            raise ImportError(f'Você precisa definir as variáveis de ambiente BINANCE_KEY e BINANCE_SECRET ou preencher o arquivo {config_path} com KEY e SECRET.')
# Inicializa o cliente Binance
client = Client(KEY, SECRET)

# Dicionário global para armazenar dados de kline em tempo real
realtime_data = {}

# Dicionário global para armazenar dados da conta em tempo real
realtime_account_data = {}


def get_futures_klines(symbol: str, interval: str, lookback: str, end_time: Optional[int] = None) -> pd.DataFrame:
    """
    Busca dados históricos de klines dos futuros da Binance.
    ⚠️ ATENÇÃO: Use apenas para dados históricos, não para tempo real!
    Para dados em tempo real, use WebSocket com websocket_manager.add_kline_stream()
    
    Args:
        symbol: Par de negociação (ex: 'BTCUSDT')
        interval: Intervalo de tempo (ex: '1h', '4h', '1d')
        lookback: Timestamp inicial ou string de data
        end_time: Timestamp final (opcional, padrão: agora)
        
    Returns:
        DataFrame com dados OHLCV ou DataFrame vazio em caso de erro
    """
    # Aplica rate limiting antes da requisição
    rate_limiter.wait_if_needed()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if isinstance(lookback, str):
                lookback_time = pd.to_datetime(lookback).timestamp() * 1000
            else:
                lookback_time = lookback
            
            # Se não especificar end_time, usa o momento atual
            if end_time is None:
                end_time = int(datetime.now().timestamp() * 1000)
                
            # Usando o método correto futures_klines com endTime para dados atuais
            raw_data = client.futures_klines(
                symbol=symbol,
                interval=interval,
                startTime=int(lookback_time),
                endTime=int(end_time)
            )
            
            if not raw_data:
                logging.warning(f"Nenhum dado retornado pela API para {symbol} {interval}")
                return pd.DataFrame()
                
            frame = pd.DataFrame(raw_data)
            frame = frame.iloc[:, :6]
            frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            frame = frame.set_index('Time')
            frame.index = pd.to_datetime(frame.index, unit='ms')
            frame = frame.astype(float)
            
            logging.info(f"Dados históricos obtidos para {symbol} {interval}: {len(frame)} registros")
            return frame
            
        except Exception as e:
            should_retry, wait_time, error_type = handle_binance_error(e, symbol, f"get_futures_klines({interval})")
            
            if error_type == "rate_limit":
                logging.error(f"🚨 Rate limit atingido para {symbol} - ABORTANDO operação")
                return pd.DataFrame()
            elif error_type == "invalid_symbol":
                logging.error(f"❌ Símbolo inválido: {symbol}")
                return pd.DataFrame()
            elif should_retry and attempt < max_retries - 1:
                logging.warning(f"🔄 Tentando novamente em {wait_time}s... (tentativa {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logging.error(f"❌ Todas as tentativas falharam para {symbol} {interval}")
                return pd.DataFrame()
    
    return pd.DataFrame()


def extend_klines_to_current(symbol: str, interval: str, existing_data: pd.DataFrame) -> pd.DataFrame:
    """
    Estende dados existentes até o momento atual buscando apenas os candles mais recentes.
    Esta função evita re-buscar dados que já temos, otimizando o uso da API.
    MELHORADO: Mais agressivo na busca por dados atuais.
    
    Args:
        symbol: Par de negociação (ex: 'BTCUSDT')
        interval: Intervalo de tempo (ex: '1h', '4h', '1d')
        existing_data: DataFrame com dados existentes
        
    Returns:
        DataFrame com dados estendidos até o momento atual
    """
    if existing_data.empty:
        return existing_data
    
    try:
        # Pega o timestamp do último candle existente
        last_time = existing_data.index[-1]
        last_timestamp = int(last_time.timestamp() * 1000)
        
        # Mapeamento de intervalos para milissegundos
        interval_ms = {
            '1m': 60000,
            '3m': 180000,
            '5m': 300000,
            '15m': 900000,
            '30m': 1800000,
            '1h': 3600000,
            '2h': 7200000,
            '4h': 14400000,
            '6h': 21600000,
            '8h': 28800000,
            '12h': 43200000,
            '1d': 86400000,
            '3d': 259200000,
            '1w': 604800000,
            '1M': 2592000000
        }
        
        current_time = int(datetime.now().timestamp() * 1000)
        interval_duration = interval_ms.get(interval, 3600000)  # padrão 1h
        
        # Calcula diferença em intervalos
        time_diff = current_time - last_timestamp
        intervals_behind = time_diff // interval_duration
        
        # Se estamos há mais de 1 intervalo atrás, busca desde o último candle
        if intervals_behind >= 1:
            start_time = last_timestamp + interval_duration  # Próximo candle após o último
            
            logging.info(f"Dados {intervals_behind} intervalos atrás para {symbol} {interval}")
            logging.info(f"Último candle: {pd.to_datetime(last_timestamp, unit='ms')}")
            logging.info(f"Buscando desde: {pd.to_datetime(start_time, unit='ms')}")
            logging.info(f"Até agora: {pd.to_datetime(current_time, unit='ms')}")
            
            # Busca dados desde o último candle até agora
            new_data = get_futures_klines(symbol, interval, start_time, current_time)
            
            if new_data.empty:
                logging.warning(f"Nenhum candle novo encontrado para {symbol} {interval}")
                return existing_data
            
            # Mescla dados evitando duplicatas
            combined_data = pd.concat([existing_data, new_data])
            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
            combined_data = combined_data.sort_index()
            
            logging.info(f"✅ Dados estendidos para {symbol} {interval}: {len(new_data)} novos candles adicionados")
            logging.info(f"Novo último candle: {combined_data.index[-1]}")
            return combined_data
        else:
            # Se estamos atualizados (menos de 1 intervalo atrás), mas vamos verificar mesmo assim
            # para casos onde pode haver candles parciais ou delay
            start_time = last_timestamp
            
            logging.info(f"Verificando updates para {symbol} {interval} (dados relativamente atuais)")
            new_data = get_futures_klines(symbol, interval, start_time, current_time)
            
            if not new_data.empty:
                # Remove o primeiro candle se for igual ao último existente
                if not new_data.empty and len(new_data) > 0:
                    if new_data.index[0] == existing_data.index[-1]:
                        new_data = new_data.iloc[1:]
                
                if not new_data.empty:
                    combined_data = pd.concat([existing_data, new_data])
                    combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                    combined_data = combined_data.sort_index()
                    
                    logging.info(f"✅ Pequena atualização para {symbol} {interval}: {len(new_data)} candles")
                    return combined_data
            
            logging.info(f"Dados já atualizados para {symbol} {interval}")
            return existing_data
        
    except Exception as e:
        logging.error(f"Erro ao estender dados para {symbol} {interval}: {e}")
        return existing_data


def process_kline_message(msg):
    """
    Processa mensagens de kline recebidas via websocket.
    
    Args:
        msg: Mensagem recebida do websocket
    """
    if msg.get('e') == 'kline':
        k = msg['k']
        if k.get('x'):  # vela fechada
            symbol = msg['s']
            dt = pd.to_datetime(k['t'], unit='ms')
            data = {
                "Open": float(k['o']),
                "High": float(k['h']),
                "Low": float(k['l']),
                "Close": float(k['c']),
                "Volume": float(k['v'])
            }
            if symbol not in realtime_data:
                realtime_data[symbol] = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
            realtime_data[symbol].loc[dt] = data
            logging.info(f"Realtime: {symbol} atualizado em {dt}")


def start_realtime_kline_socket(symbol: str, interval: str):
    """
    Inicia uma conexão websocket para receber dados de kline em tempo real para futuros.
    ⚠️ RECOMENDADO: Use websocket_manager.add_kline_stream() para melhor controle!
    
    Args:
        symbol: Par de negociação (ex: 'BTCUSDT')
        interval: Intervalo de tempo (ex: '1h', '4h', '1d')
        
    Returns:
        Tupla contendo o objeto ThreadedWebsocketManager e a chave de conexão
    """
    logging.warning("Usando método legado. Recomendado usar websocket_manager.add_kline_stream()")
    
    twm = ThreadedWebsocketManager(api_key=KEY, api_secret=SECRET)
    twm.start()
    stream = f"{symbol.lower()}@kline_{interval}"
    conn_key = twm.start_futures_multiplex_socket(process_kline_message, streams=[stream])
    logging.info(f"Websocket de kline iniciado para {symbol} no intervalo {interval} (stream: {stream})")
    return twm, conn_key


def process_user_message(msg):
    """
    Processa mensagens de usuário recebidas via websocket.
    
    Args:
        msg: Mensagem recebida do websocket
    """
    event_type = msg.get('e')
    if event_type == 'ACCOUNT_UPDATE':
        realtime_account_data['account_update'] = msg
        if 'a' in msg and 'P' in msg['a']:
            realtime_account_data['positions'] = msg['a']['P']
        logging.info("ACCOUNT_UPDATE recebido")
    elif event_type == 'ORDER_TRADE_UPDATE':
        realtime_account_data.setdefault('orders', []).append(msg)
        logging.info("ORDER_TRADE_UPDATE recebido")
    else:
        logging.info(f"Mensagem recebida: {msg}")


def start_realtime_user_socket():
    """
    Inicia uma conexão websocket para receber dados da conta em tempo real.
    
    Returns:
        Tupla contendo o objeto ThreadedWebsocketManager e a chave de conexão
    """
    twm = ThreadedWebsocketManager(api_key=KEY, api_secret=SECRET)
    twm.start()
    conn_key = twm.start_futures_user_socket(callback=process_user_message)
    logging.info("Websocket de usuário iniciado")
    return twm, conn_key


def get_binance_client():
    """
    Retorna o cliente Binance configurado.
    
    Returns:
        Client: Instância do cliente Binance
    """
    return client


def get_realtime_data(symbol: str = None):
    """
    Retorna os dados de kline em tempo real.
    
    Args:
        symbol: Símbolo específico para retornar dados. Se None, retorna todos os dados.
        
    Returns:
        Dict ou DataFrame: Dados de kline em tempo real
    """
    if symbol:
        return realtime_data.get(symbol, pd.DataFrame())
    return realtime_data


def get_realtime_account_data():
    """
    Retorna os dados da conta em tempo real.
    
    Returns:
        Dict: Dados da conta em tempo real
    """
    return realtime_account_data


def clear_realtime_data(symbol: str = None):
    """
    Limpa os dados de kline em tempo real.
    
    Args:
        symbol: Símbolo específico para limpar. Se None, limpa todos os dados.
    """
    if symbol:
        if symbol in realtime_data:
            realtime_data[symbol] = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    else:
        realtime_data.clear()


def clear_realtime_account_data():
    """
    Limpa os dados da conta em tempo real.
    """
    realtime_account_data.clear()

# Gerenciador de WebSockets para múltiplos streams
class WebSocketManager:
    """
    Gerenciador centralizado de WebSockets para evitar múltiplas conexões
    e reduzir o uso de requisições REST.
    """
    
    def __init__(self):
        self.active_connections = {}
        self.twm = None
        self.is_running = False
        self.callbacks = {}
    
    def start(self):
        """Inicia o gerenciador de WebSocket"""
        if not self.is_running:
            self.twm = ThreadedWebsocketManager(api_key=KEY, api_secret=SECRET)
            self.twm.start()
            self.is_running = True
            logging.info("WebSocket Manager iniciado")
    
    def stop(self):
        """Para o gerenciador de WebSocket"""
        if self.is_running and self.twm:
            try:
                self.twm.stop()
                self.active_connections.clear()
                self.callbacks.clear()
                self.is_running = False
                logging.info("WebSocket Manager parado")
            except Exception as e:
                logging.error(f"Erro ao parar WebSocket Manager: {e}")
    
    def add_kline_stream(self, symbol: str, interval: str, callback: Callable = None):
        """
        Adiciona um stream de kline ao gerenciador.
        
        Args:
            symbol: Símbolo do par (ex: 'BTCUSDT')
            interval: Intervalo (ex: '1m', '5m', '1h')
            callback: Função callback personalizada (opcional)
        """
        if not self.is_running:
            self.start()
        
        stream_key = f"{symbol}@{interval}"
        
        if stream_key not in self.active_connections:
            stream = f"{symbol.lower()}@kline_{interval}"
            
            # Usa callback personalizado ou o padrão
            callback_func = callback if callback else self._default_kline_callback
            
            try:
                conn_key = self.twm.start_futures_multiplex_socket(
                    callback_func, 
                    streams=[stream]
                )
                self.active_connections[stream_key] = conn_key
                self.callbacks[stream_key] = callback_func
                logging.info(f"Stream {stream} adicionado com sucesso")
            except Exception as e:
                logging.error(f"Erro ao adicionar stream {stream}: {e}")
    
    def remove_kline_stream(self, symbol: str, interval: str):
        """Remove um stream de kline do gerenciador"""
        stream_key = f"{symbol}@{interval}"
        
        if stream_key in self.active_connections:
            try:
                self.twm.stop_socket(self.active_connections[stream_key])
                del self.active_connections[stream_key]
                del self.callbacks[stream_key]
                logging.info(f"Stream {stream_key} removido")
            except Exception as e:
                logging.error(f"Erro ao remover stream {stream_key}: {e}")
    
    def _default_kline_callback(self, msg):
        """Callback padrão para mensagens de kline"""
        process_kline_message(msg)
    
    def get_active_streams(self):
        """Retorna lista de streams ativos"""
        return list(self.active_connections.keys())

# Instância global do gerenciador de WebSocket
websocket_manager = WebSocketManager()


def get_historical_data_safe(symbol: str, interval: str, days: int = 7) -> pd.DataFrame:
    """
    Busca dados históricos de forma segura, respeitando rate limits.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo de tempo
        days: Número de dias para buscar dados históricos
        
    Returns:
        DataFrame com dados históricos
    """
    start_time = datetime.now() - timedelta(days=days)
    start_timestamp = int(start_time.timestamp() * 1000)
    
    logging.info(f"Buscando dados históricos para {symbol} {interval} (últimos {days} dias)")
    return get_futures_klines(symbol, interval, start_timestamp)


def start_multiple_kline_streams(symbols_intervals: list, callback: Callable = None):
    """
    Inicia múltiplos streams de kline de uma vez.
    
    Args:
        symbols_intervals: Lista de tuplas (symbol, interval)
        callback: Função callback personalizada (opcional)
    
    Example:
        start_multiple_kline_streams([
            ('BTCUSDT', '1m'),
            ('ETHUSDT', '1m'),
            ('SOLUSDT', '5m')
        ])
    """
    for symbol, interval in symbols_intervals:
        websocket_manager.add_kline_stream(symbol, interval, callback)
        time.sleep(0.1)  # Pequeno delay para evitar sobrecarga


def stop_all_streams():
    """Para todos os streams ativos"""
    websocket_manager.stop()


def get_active_streams():
    """Retorna lista de streams ativos"""
    return websocket_manager.get_active_streams()


def is_websocket_running():
    """Verifica se o WebSocket está rodando"""
    return websocket_manager.is_running


def get_current_kline_data(symbol: str, interval: str, use_websocket: bool = True) -> pd.DataFrame:
    """
    Obtém dados de kline atuais. SEMPRE prioriza WebSocket para evitar rate limit.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo de tempo
        use_websocket: Se deve usar WebSocket (ALTAMENTE RECOMENDADO)
        
    Returns:
        DataFrame com dados atuais
    """
    if use_websocket:
        stream_key = f"{symbol}@{interval}"
        
        # Verifica se o stream já existe
        if stream_key not in websocket_manager.get_active_streams():
            logging.info(f"Iniciando WebSocket para {symbol} {interval}")
            websocket_manager.add_kline_stream(symbol, interval)
            time.sleep(5)  # Aguarda mais tempo para dados iniciais
        
        # Retry para aguardar dados do WebSocket
        for attempt in range(5):  # 5 tentativas
            if symbol in realtime_data and not realtime_data[symbol].empty:
                logging.info(f"Dados WebSocket obtidos para {symbol}: {len(realtime_data[symbol])} registros")
                return realtime_data[symbol].copy()
            
            logging.info(f"Aguardando dados WebSocket para {symbol} (tentativa {attempt + 1}/5)")
            time.sleep(2)  # Delay entre retries
        
        logging.warning(f"WebSocket não retornou dados para {symbol} após 5 tentativas")
    
    # Fallback para REST API apenas se WebSocket falhar completamente
    logging.warning(f"FALLBACK para REST API em {symbol} {interval} - use WebSocket sempre que possível!")
    return get_historical_data_safe(symbol, interval, days=1)


def get_multiple_symbols_data(symbols: list, interval: str, use_websocket: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Obtém dados para múltiplos símbolos de forma eficiente.
    SEMPRE prioriza WebSocket para evitar rate limit.
    
    Args:
        symbols: Lista de símbolos
        interval: Intervalo de tempo
        use_websocket: Se deve usar WebSocket (ALTAMENTE RECOMENDADO)
        
    Returns:
        Dicionário com dados para cada símbolo
    """
    result = {}
    
    if use_websocket:
        logging.info(f"Iniciando WebSockets para {len(symbols)} símbolos no intervalo {interval}")
        
        # Inicia WebSockets para todos os símbolos
        symbols_intervals = [(symbol, interval) for symbol in symbols]
        start_multiple_kline_streams(symbols_intervals)
        
        # Aguarda dados chegarem com timeout progressivo
        max_wait_time = 10  # 10 segundos máximo
        for wait_time in range(1, max_wait_time + 1):
            time.sleep(1)
            
            # Verifica quantos símbolos já têm dados
            symbols_with_data = [s for s in symbols if s in realtime_data and not realtime_data[s].empty]
            
            logging.info(f"Aguardando WebSocket dados: {len(symbols_with_data)}/{len(symbols)} símbolos prontos")
            
            if len(symbols_with_data) >= len(symbols) * 0.8:  # 80% dos símbolos têm dados
                break
        
        # Coleta dados dos WebSockets
        for symbol in symbols:
            if symbol in realtime_data and not realtime_data[symbol].empty:
                result[symbol] = realtime_data[symbol].copy()
                logging.info(f"WebSocket dados obtidos para {symbol}: {len(result[symbol])} registros")
            else:
                logging.warning(f"WebSocket sem dados para {symbol} - SEM FALLBACK para evitar rate limit")
                # SEM FALLBACK para REST - evita rate limit
                result[symbol] = pd.DataFrame()
    else:
        # FORÇA uso de WebSocket para evitar rate limits
        logging.error("🚨 FORÇANDO WebSocket para múltiplos símbolos - evitando rate limit!")
        return get_multiple_symbols_data(symbols, interval, use_websocket=True)
    
    logging.info(f"Dados obtidos para {len(result)} símbolos")
    return result


def cleanup_old_data(max_age_hours: int = 24):
    """
    Limpa dados antigos do cache para economizar memória.
    
    Args:
        max_age_hours: Idade máxima dos dados em horas
    """
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    for symbol in list(realtime_data.keys()):
        if symbol in realtime_data and not realtime_data[symbol].empty:
            # Filtra dados mais recentes que o cutoff
            df = realtime_data[symbol]
            if hasattr(df.index, 'to_pydatetime'):
                recent_data = df[df.index > cutoff_time]
                realtime_data[symbol] = recent_data
                
                if recent_data.empty:
                    del realtime_data[symbol]
                    logging.info(f"Dados antigos removidos para {symbol}")


def get_connection_status() -> Dict[str, any]:
    """
    Retorna status das conexões WebSocket.
    
    Returns:
        Dicionário com informações de status
    """
    return {
        'websocket_running': websocket_manager.is_running,
        'active_streams': websocket_manager.get_active_streams(),
        'symbols_with_data': list(realtime_data.keys()),
        'total_data_points': sum(len(df) for df in realtime_data.values())
    }


def restart_websocket_manager():
    """
    Reinicia o gerenciador de WebSocket em caso de problemas.
    """
    logging.info("Reiniciando WebSocket Manager...")
    websocket_manager.stop()
    time.sleep(2)
    websocket_manager.start()
    logging.info("WebSocket Manager reiniciado")


# Função para inicialização automática
def initialize_trading_streams(symbols: list, intervals: list):
    """
    Inicializa streams de trading para múltiplos símbolos e intervalos.
    
    Args:
        symbols: Lista de símbolos (ex: ['BTCUSDT', 'ETHUSDT'])
        intervals: Lista de intervalos (ex: ['1m', '5m', '1h'])
    """
    logging.info(f"Inicializando streams para {len(symbols)} símbolos e {len(intervals)} intervalos")
    
    # Cria todas as combinações símbolo-intervalo
    streams_to_start = []
    for symbol in symbols:
        for interval in intervals:
            streams_to_start.append((symbol, interval))
    
    # Inicia todos os streams
    start_multiple_kline_streams(streams_to_start)
    
    logging.info(f"Iniciados {len(streams_to_start)} streams de trading")


def validate_symbol(symbol: str) -> bool:
    """
    Valida se um símbolo é válido na Binance Futures.
    
    Args:
        symbol: Símbolo a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    try:
        # Usa rate limiter para esta verificação
        rate_limiter.wait_if_needed()
        
        exchange_info = client.futures_exchange_info()
        valid_symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
        
        is_valid = symbol in valid_symbols
        if not is_valid:
            logging.warning(f"Símbolo {symbol} não é válido ou não está sendo negociado")
        
        return is_valid
        
    except Exception as e:
        logging.error(f"Erro ao validar símbolo {symbol}: {e}")
        return False


def preload_symbols_data(symbols: list, intervals: list, validate_symbols: bool = True):
    """
    Pré-carrega dados para múltiplos símbolos e intervalos usando WebSocket.
    Ideal para inicialização do sistema.
    
    Args:
        symbols: Lista de símbolos
        intervals: Lista de intervalos
        validate_symbols: Se deve validar símbolos antes de iniciar
    """
    logging.info(f"Pré-carregando dados para {len(symbols)} símbolos e {len(intervals)} intervalos")
    
    # Validação opcional de símbolos
    if validate_symbols:
        valid_symbols = []
        for symbol in symbols:
            if validate_symbol(symbol):
                valid_symbols.append(symbol)
            else:
                logging.warning(f"Símbolo {symbol} ignorado por ser inválido")
        symbols = valid_symbols
    
    if not symbols:
        logging.error("Nenhum símbolo válido encontrado")
        return
    
    # Inicializa streams para todas as combinações
    initialize_trading_streams(symbols, intervals)
    
    # Aguarda dados chegarem
    logging.info("Aguardando dados iniciais dos WebSockets...")
    time.sleep(10)  # Aguarda tempo suficiente para dados iniciais
    
    # Verifica status
    status = get_connection_status()
    logging.info(f"Pré-carregamento concluído:")
    logging.info(f"- WebSocket ativo: {status['websocket_running']}")
    logging.info(f"- Streams ativos: {len(status['active_streams'])}")
    logging.info(f"- Símbolos com dados: {len(status['symbols_with_data'])}")
    
    return status


def auto_cleanup_scheduler():
    """
    Scheduler automático para limpeza de dados antigos.
    Execute em thread separada para manutenção automática.
    """
    import threading
    
    def cleanup_loop():
        while websocket_manager.is_running:
            try:
                cleanup_old_data(max_age_hours=24)
                time.sleep(3600)  # Limpa a cada hora
            except Exception as e:
                logging.error(f"Erro na limpeza automática: {e}")
                time.sleep(300)  # Aguarda 5 minutos se houver erro
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logging.info("Scheduler de limpeza automática iniciado")


def get_system_health() -> Dict[str, any]:
    """
    Retorna informações detalhadas sobre a saúde do sistema.
    
    Returns:
        Dict com métricas de saúde
    """
    status = get_connection_status()
    
    health = {
        'websocket_manager': {
            'running': status['websocket_running'],
            'active_streams': len(status['active_streams']),
            'streams_list': status['active_streams']
        },
        'data_cache': {
            'symbols_with_data': len(status['symbols_with_data']),
            'total_data_points': status['total_data_points'],
            'symbols_list': status['symbols_with_data']
        },
        'rate_limiter': {
            'recent_requests': len(rate_limiter.requests),
            'max_requests_per_minute': rate_limiter.max_requests,
            'in_ban_period': rate_limiter.last_ban_time is not None and 
                           (datetime.now() - rate_limiter.last_ban_time).seconds < rate_limiter.ban_duration
        },
        'memory_usage': {
            'realtime_data_size': len(realtime_data),
            'account_data_size': len(realtime_account_data)
        }
    }
    
    return health


def emergency_reset():
    """
    Reset de emergência do sistema em caso de problemas graves.
    """
    logging.warning("Executando reset de emergência do sistema...")
    
    try:
        # Para todos os streams
        stop_all_streams()
        time.sleep(2)
        
        # Limpa todos os dados
        clear_realtime_data()
        clear_realtime_account_data()
        
        # Reseta rate limiter
        rate_limiter.requests = []
        rate_limiter.last_ban_time = None
        rate_limiter.ban_duration = 60
        
        logging.info("Reset de emergência concluído")
        
    except Exception as e:
        logging.error(f"Erro durante reset de emergência: {e}")


def safe_shutdown():
    """
    Encerramento seguro do sistema com cleanup completo.
    """
    logging.info("Iniciando encerramento seguro do sistema...")
    
    try:
        # Para scheduler de limpeza se estiver rodando
        # (o scheduler é daemon thread e será encerrado automaticamente)
        
        # Encerra conexões usando as funções existentes
        stop_all_streams()
        clear_realtime_data()
        clear_realtime_account_data()
        
        # Aguarda um pouco para garantir que tudo foi encerrado
        time.sleep(2)
        
        logging.info("Sistema encerrado com segurança")
        
    except Exception as e:
        logging.error(f"Erro durante encerramento seguro: {e}")
        
    finally:
        # Força limpeza final
        try:
            clear_realtime_data()
            clear_realtime_account_data()
        except:
            pass
            pass

def get_rate_limit_status():
    """
    Retorna status detalhado do rate limiter para monitoramento.
    
    Returns:
        dict: Status completo do rate limiter
    """
    stats = rate_limiter.get_stats()
    
    # Calcula estatísticas adicionais
    percentage_used = (stats['current_requests'] / stats['max_requests']) * 100
    
    status = {
        'requests_current': stats['current_requests'],
        'requests_max': stats['max_requests'],
        'requests_available': stats['max_requests'] - stats['current_requests'],
        'percentage_used': percentage_used,
        'blocked_count': stats['blocked_count'],
        'is_banned': stats['is_banned'],
        'ban_remaining': stats.get('ban_remaining', 0),
        'emergency_mode': getattr(rate_limiter, 'emergency_mode', False),
        'status': 'EMERGENCY' if getattr(rate_limiter, 'emergency_mode', False) else
                 'BANNED' if stats['is_banned'] else
                 'DANGER' if percentage_used > 90 else
                 'WARNING' if percentage_used > 70 else
                 'OK'
    }
    
    return status


def force_emergency_mode():
    """
    Força o sistema a entrar em modo emergência por 5 minutos.
    Use apenas em caso de problemas graves de rate limit.
    """
    logging.error("🚨 MODO EMERGÊNCIA ATIVADO MANUALMENTE")
    rate_limiter.emergency_mode = True
    

def reset_rate_limiter():
    """
    Reseta completamente o rate limiter.
    Use apenas quando necessário e com cuidado.
    """
    logging.warning("🔄 RESETANDO Rate Limiter manualmente")
    rate_limiter.force_reset()


def log_rate_limit_status():
    """
    Registra o status atual do rate limiter nos logs.
    """
    status = get_rate_limit_status()
    logging.info(f"📊 Rate Limiter Status: {status['status']} - "
                f"{status['requests_current']}/{status['requests_max']} "
                f"({status['percentage_used']:.1f}%)")
    
    if status['blocked_count'] > 0:
        logging.warning(f"🛑 Bloqueios preventivos: {status['blocked_count']}")
    
    if status['is_banned']:
        logging.error(f"🚫 Sistema banido - Restam {status['ban_remaining']:.1f}s")


def safe_request_check(operation_name="unknown"):
    """
    Verifica se é seguro fazer uma requisição REST.
    
    Args:
        operation_name: Nome da operação para log
        
    Returns:
        bool: True se seguro, False caso contrário
    """
    can_request = rate_limiter.can_make_request()
    
    if not can_request:
        status = get_rate_limit_status()
        logging.warning(f"⚠️ Requisição {operation_name} BLOQUEADA - Status: {status['status']}")
        return False
    
    return True


# Função para testar a conectividade sem fazer requisições que consomem rate limit
def test_connection():
    """
    Testa a conectividade com a API Binance sem consumir rate limit.
    
    Returns:
        bool: True se conectado, False caso contrário
    """
    try:
        # Usa endpoint que não consome rate limit
        server_time = client.get_server_time()
        logging.info(f"✅ Conexão OK - Server time: {server_time['serverTime']}")
        return True
    except Exception as e:
        logging.error(f"❌ Erro de conexão: {e}")
        return False

def safe_rest_request(func, *args, **kwargs):
    """
    Wrapper seguro para requisições REST que aplica rate limiting e error handling.
    
    Args:
        func: Função da API Binance para chamar
        *args: Argumentos posicionais para a função
        **kwargs: Argumentos nomeados para a função
        
    Returns:
        Resultado da função ou None em caso de erro
    """
    operation_name = func.__name__ if hasattr(func, '__name__') else str(func)
    
    # Verifica se é seguro fazer a requisição
    if not safe_request_check(operation_name):
        logging.error(f"🚫 Requisição {operation_name} NEGADA - Rate limit preventivo")
        return None
    
    # Aplica rate limiting
    rate_limiter.wait_if_needed()
    
    try:
        result = func(*args, **kwargs)
        logging.debug(f"✅ {operation_name} executado com sucesso")
        return result
    except Exception as e:
        should_retry, wait_time, error_type = handle_binance_error(e, operation=operation_name)
        
        if error_type == "rate_limit":
            logging.error(f"🚨 Rate limit em {operation_name} - OPERAÇÃO ABORTADA")
            return None
        else:
            logging.error(f"❌ Erro em {operation_name}: {e}")
            return None


# Exemplo de uso do wrapper seguro
def get_futures_klines_ultra_safe(symbol: str, interval: str, lookback) -> pd.DataFrame:
    """
    Versão ULTRA SEGURA do get_futures_klines que nunca causa rate limit.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo de tempo
        lookback: Timestamp inicial
        
    Returns:
        DataFrame com dados ou DataFrame vazio se não puder fazer requisição
    """
    # Verifica se é seguro fazer requisição
    if not safe_request_check(f"get_futures_klines({symbol}, {interval})"):
        logging.warning(f"⚠️ Requisição para {symbol} {interval} BLOQUEADA por rate limit preventivo")
        return pd.DataFrame()
    
    # Preparar argumentos
    if isinstance(lookback, str):
        lookback_time = pd.to_datetime(lookback).timestamp() * 1000
    else:
        lookback_time = lookback
    
    # Fazer requisição usando o wrapper seguro
    raw_data = safe_rest_request(
        client.futures_klines,
        symbol=symbol,
        interval=interval,
        startTime=int(lookback_time)
    )
    
    if raw_data is None:
        logging.warning(f"Nenhum dado retornado para {symbol} {interval}")
        return pd.DataFrame()
    
    try:
        # Processar dados
        if not raw_data:
            logging.warning(f"Lista vazia retornada para {symbol} {interval}")
            return pd.DataFrame()
            
        frame = pd.DataFrame(raw_data)
        frame = frame.iloc[:, :6]
        frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        frame = frame.set_index('Time')
        frame.index = pd.to_datetime(frame.index, unit='ms')
        frame = frame.astype(float)
        
        logging.info(f"✅ Dados processados para {symbol} {interval}: {len(frame)} registros")
        return frame
        
    except Exception as e:
        logging.error(f"❌ Erro ao processar dados para {symbol} {interval}: {e}")
        return pd.DataFrame()

