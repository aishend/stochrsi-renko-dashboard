"""
Data Manager
============

Gerenciador central de dados para o sistema de trading.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pickle
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from src.api.binance_client import get_binance_client, get_futures_klines, extend_klines_to_current
from src.utils.data_requirements import get_optimized_days_for_renko_stochrsi
from config.settings import DATA_CONFIG

logger = logging.getLogger(__name__)

class DataManager:
    """
    Gerenciador de dados com cache e otimizações.
    """
    
    def __init__(self, cache_enabled: bool = None):
        """
        Inicializa o gerenciador de dados.
        
        Args:
            cache_enabled: Habilita cache (opcional, usa config)
        """
        self.cache_enabled = cache_enabled if cache_enabled is not None else DATA_CONFIG['cache_enabled']
        self.cache_duration = DATA_CONFIG['cache_duration']
        self.cache_dir = 'cache'
        self.client = get_binance_client()
        
        # Cria diretório de cache se não existir
        if self.cache_enabled:
            try:
                if not os.path.exists(self.cache_dir):
                    os.makedirs(self.cache_dir, exist_ok=True)
                    logger.debug(f"Diretório de cache criado: {self.cache_dir}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório de cache: {e}")
                self.cache_enabled = False  # Desabilita cache se não conseguir criar diretório
        
        # Configuração automática de dias baseada no timeframe
        # ATUALIZADO: Valores otimizados para Renko + StochRSI
        self.timeframe_requirements = {
            '1m': 7,     # 7 dias para 1 minuto (otimizado para Renko)
            '3m': 10,    # 10 dias para 3 minutos
            '5m': 14,    # 14 dias para 5 minutos
            '15m': 21,   # 21 dias para 15 minutos
            '30m': 30,   # 30 dias para 30 minutos
            '1h': 45,    # 45 dias para 1 hora
            '2h': 60,    # 60 dias para 2 horas
            '4h': 90,    # 90 dias para 4 horas (aumentado para Renko)
            '6h': 120,   # 120 dias para 6 horas
            '8h': 150,   # 150 dias para 8 horas
            '12h': 180,  # 180 dias para 12 horas
            '1d': 365,   # 365 dias para 1 dia (aumentado para Renko)
            '3d': 500,   # 500 dias para 3 dias
            '1w': 700,   # 700 dias para 1 semana
        }
        
        # Mapeamento de timeframes para período de cache
        self.cache_validity = {
            '1m': 30,    # 30 segundos para 1 minuto
            '3m': 60,    # 1 minuto para 3 minutos
            '5m': 120,   # 2 minutos para 5 minutos
            '15m': 300,  # 5 minutos para 15 minutos
            '30m': 600,  # 10 minutos para 30 minutos
            '1h': 1800,  # 30 minutos para 1 hora
            '2h': 3600,  # 1 hora para 2 horas
            '4h': 7200,  # 2 horas para 4 horas
            '6h': 10800, # 3 horas para 6 horas
            '8h': 14400, # 4 horas para 8 horas
            '12h': 21600, # 6 horas para 12 horas
            '1d': 43200,  # 12 horas para 1 dia
            '3d': 86400,  # 24 horas para 3 dias
            '1w': 172800, # 48 horas para 1 semana
        }
        
        # Lock para operações thread-safe
        self.cache_lock = threading.Lock()
        
        # Limpa cache desnecessário na inicialização
        self.cleanup_cache()
    
    
    def get_required_days(self, interval: str, brick_size: int = 1000) -> int:
        """
        Calcula automaticamente o número de dias necessários para um timeframe.
        ATUALIZADO: Considera Renko + StochRSI.
        
        Args:
            interval: Intervalo de tempo
            brick_size: Tamanho do tijolo Renko (None para ATR dinâmico, usa padrão 1000)
            
        Returns:
            Número de dias necessários
        """
        # Se brick_size é None (ATR dinâmico), usa valor padrão conservador
        if brick_size is None:
            brick_size = 1000
            
        # Primeiro tenta usar o cálculo otimizado para Renko
        try:
            return self.get_required_days_for_renko(interval, brick_size)
        except Exception as e:
            logger.warning(f"Erro no cálculo otimizado para {interval}: {e}")
            # Fallback para valores padrão
            return self.timeframe_requirements.get(interval, 90)
    
    def _get_cache_filename(self, symbol: str, interval: str, brick_size: int = 1000) -> str:
        """Gera nome do arquivo de cache baseado no cálculo automático."""
        # Se brick_size é None (ATR dinâmico), usa valor padrão para nome do cache
        if brick_size is None:
            brick_size = 1000
            
        days = self.get_required_days(interval, brick_size)
        return os.path.join(self.cache_dir, f"{symbol}_{interval}_{days}d_b{brick_size}.pkl")
    
    def _is_cache_valid(self, cache_file: str, interval: str) -> bool:
        """Verifica se o cache ainda é válido baseado no timeframe."""
        try:
            if not os.path.exists(cache_file):
                return False
            
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            cache_duration = self.cache_validity.get(interval, self.cache_duration)
            return (datetime.now() - file_time).seconds < cache_duration
            
        except (OSError, PermissionError) as e:
            logger.debug(f"Erro ao verificar cache {cache_file}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Erro inesperado ao verificar cache {cache_file}: {e}")
            return False

    def _is_cache_useful_for_indicators(self, cache_file: str, symbol: str, interval: str) -> bool:
        """
        Verifica se o cache pode ser útil para indicadores mesmo sendo antigo.
        Preserva dados que:
        - Não são muito antigos (até 7 dias)
        - Podem ser úteis para cálculos de indicadores
        - Contêm dados históricos necessários
        """
        try:
            if not os.path.exists(cache_file):
                return False
            
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            days_old = (datetime.now() - file_time).days
            
            # Preserva cache que não seja muito antigo
            if days_old > 7:
                return False
            
            # Preserva cache de timeframes importantes para indicadores
            important_intervals = ['1h', '4h', '1d']
            if interval in important_intervals:
                return True
            
            # Verifica se há dados suficientes no cache
            try:
                data = self._load_from_cache(cache_file)
                if data is not None and len(data) >= 200:  # Dados suficientes para indicadores
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Erro ao verificar utilidade do cache {cache_file}: {e}")
            return False
    
    def get_cache_statistics(self) -> Dict:
        """
        Retorna estatísticas sobre o cache para melhor gerenciamento.
        """
        if not self.cache_enabled or not os.path.exists(self.cache_dir):
            return {
                'total_files': 0,
                'total_size': 0,
                'valid_files': 0,
                'useful_files': 0,
                'outdated_files': 0
            }
        
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
            total_files = len(cache_files)
            total_size = 0
            valid_files = 0
            useful_files = 0
            outdated_files = 0
            
            for file in cache_files:
                file_path = os.path.join(self.cache_dir, file)
                
                try:
                    # Calcula o tamanho do arquivo
                    total_size += os.path.getsize(file_path)
                    
                    # Extrai informações do nome do arquivo
                    parts = file.replace('.pkl', '').split('_')
                    if len(parts) >= 3:
                        symbol = parts[0]
                        interval = parts[1]
                        
                        # Verifica se é válido
                        if self._is_cache_valid(file_path, interval):
                            valid_files += 1
                        elif self._is_cache_useful_for_indicators(file_path, symbol, interval):
                            useful_files += 1
                        else:
                            outdated_files += 1
                            
                except Exception as e:
                    logger.debug(f"Erro ao processar estatísticas do cache {file}: {e}")
                    continue
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'valid_files': valid_files,
                'useful_files': useful_files,
                'outdated_files': outdated_files
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {
                'total_files': 0,
                'total_size': 0,
                'valid_files': 0,
                'useful_files': 0,
                'outdated_files': 0
            }
    
    def _load_from_cache(self, cache_file: str) -> Optional[pd.DataFrame]:
        """Carrega dados do cache de forma thread-safe."""
        with self.cache_lock:
            try:
                if os.path.exists(cache_file):
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
            except FileNotFoundError:
                # File não encontrado é esperado - cache não existe
                logger.debug(f"Cache não encontrado: {cache_file}")
            except PermissionError:
                # Erro de permissão - arquivo pode estar sendo usado por outro processo
                logger.debug(f"Erro de permissão ao acessar cache: {cache_file}")
            except Exception as e:
                # Outros erros podem ser problemas reais
                logger.error(f"Erro inesperado ao carregar cache {cache_file}: {e}")
        return None
    
    def _save_to_cache(self, data: pd.DataFrame, cache_file: str):
        """Salva dados no cache de forma thread-safe."""
        with self.cache_lock:
            try:
                # Assegura que o diretório existe
                cache_dir = os.path.dirname(cache_file)
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
                    
                logger.debug(f"Cache salvo com sucesso: {cache_file}")
                
            except PermissionError:
                # Erro de permissão - arquivo pode estar sendo usado por outro processo
                logger.debug(f"Erro de permissão ao salvar cache: {cache_file}")
            except OSError as e:
                # Erros do sistema operacional (espaço em disco, etc.)
                logger.warning(f"Erro do sistema ao salvar cache {cache_file}: {e}")
            except Exception as e:
                # Outros erros podem ser problemas reais
                logger.error(f"Erro inesperado ao salvar cache {cache_file}: {e}")
    
    def cleanup_cache(self):
        """Limpa arquivos de cache desnecessários ou expirados de forma inteligente."""
        if not self.cache_enabled:
            return
            
        # Assegura que o diretório de cache existe
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                logger.debug(f"Diretório de cache criado: {self.cache_dir}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório de cache: {e}")
            return
        
        try:
            current_time = datetime.now()
            cleaned_files = 0
            preserved_files = 0
            
            # Lista arquivos de cache com tratamento de erros
            try:
                cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
            except (OSError, PermissionError) as e:
                logger.warning(f"Erro ao listar arquivos de cache: {e}")
                return
            
            for file in cache_files:
                file_path = os.path.join(self.cache_dir, file)
                
                # Extrai informações do nome do arquivo
                try:
                    parts = file.replace('.pkl', '').split('_')
                    if len(parts) >= 3:
                        symbol = parts[0]
                        interval = parts[1]
                        
                        # Verifica se o cache ainda é válido baseado no tempo
                        if not self._is_cache_valid(file_path, interval):
                            # Verifica se o cache pode ser útil para indicadores
                            if self._is_cache_useful_for_indicators(file_path, symbol, interval):
                                preserved_files += 1
                                logger.debug(f"Cache preservado para indicadores: {file}")
                            else:
                                try:
                                    os.remove(file_path)
                                    cleaned_files += 1
                                    logger.debug(f"Arquivo de cache removido: {file}")
                                except (OSError, PermissionError) as e:
                                    logger.debug(f"Não foi possível remover cache {file}: {e}")
                        else:
                            logger.debug(f"Cache ainda válido: {file}")
                                
                except Exception as e:
                    logger.debug(f"Erro ao processar arquivo de cache {file}: {e}")
                    continue
            
            if cleaned_files > 0:
                logger.info(f"Cache limpo: {cleaned_files} arquivos removidos, {preserved_files} preservados")
            else:
                logger.debug("Nenhum arquivo de cache expirado encontrado")
                
        except Exception as e:
            logger.error(f"Erro inesperado ao limpar cache: {e}")
    
    def get_symbol_data(self, symbol: str, interval: str, force_cache: bool = False, brick_size: int = 1000, extend_to_current: bool = True) -> pd.DataFrame:
        """
        Obtém dados de um símbolo específico com cálculo automático de dias.
        ATUALIZADO: Considera brick_size para Renko e usa cache inteligente.
        NOVO: Suporte para extend_to_current que busca dados até o momento atual.
        
        Args:
            symbol: Símbolo do par
            interval: Intervalo de tempo
            force_cache: Força uso de cache mesmo se expirado
            brick_size: Tamanho do tijolo Renko (padrão: 1000)
            extend_to_current: Se True, estende dados até o momento atual
        
        Returns:
            DataFrame com dados OHLCV
        """
        cache_file = self._get_cache_filename(symbol, interval, brick_size)
        
        # Verifica cache se habilitado
        if self.cache_enabled:
            if force_cache or self._is_cache_valid(cache_file, interval):
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None:
                    logger.debug(f"Dados carregados do cache para {symbol} {interval} (brick_size {brick_size})")
                    
                    # Se extend_to_current é True, busca dados mais recentes
                    if extend_to_current and not cached_data.empty:
                        logger.info(f"Estendendo dados para {symbol} {interval} até o momento atual")
                        extended_data = extend_klines_to_current(symbol, interval, cached_data)
                        
                        # Salva dados estendidos no cache
                        if not extended_data.empty and len(extended_data) > len(cached_data):
                            self._save_to_cache(extended_data, cache_file)
                            logger.info(f"Cache atualizado para {symbol} {interval} com {len(extended_data) - len(cached_data)} novos candles")
                        
                        return extended_data
                    
                    return cached_data
            
            # Verifica se existe cache útil mesmo se expirado
            elif self._is_cache_useful_for_indicators(cache_file, symbol, interval):
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None and len(cached_data) >= 200:
                    logger.debug(f"Usando cache útil para indicadores: {symbol} {interval}")
                    
                    # Se extend_to_current é True, busca dados mais recentes
                    if extend_to_current and not cached_data.empty:
                        logger.info(f"Estendendo dados úteis para {symbol} {interval} até o momento atual")
                        extended_data = extend_klines_to_current(symbol, interval, cached_data)
                        
                        # Salva dados estendidos no cache
                        if not extended_data.empty and len(extended_data) > len(cached_data):
                            self._save_to_cache(extended_data, cache_file)
                            logger.info(f"Cache útil atualizado para {symbol} {interval} com {len(extended_data) - len(cached_data)} novos candles")
                        
                        return extended_data
                    
                    return cached_data
        
        # Busca dados da API - usando cálculo otimizado para Renko
        days = self.get_required_days(interval, brick_size)
        start_time = datetime.now() - timedelta(days=days)
        start_timestamp = int(start_time.timestamp() * 1000)
        
        logger.info(f"Buscando {days} dias de dados para {symbol} {interval} (brick_size {brick_size})")
        
        try:
            # Busca dados da API até o momento atual
            current_timestamp = int(datetime.now().timestamp() * 1000)
            data = get_futures_klines(symbol, interval, start_timestamp, current_timestamp)
            
            # Salva no cache se dados válidos
            if self.cache_enabled and not data.empty:
                self._save_to_cache(data, cache_file)
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados para {symbol} {interval}: {e}")
            
            # Tenta carregar do cache como fallback
            if self.cache_enabled:
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None:
                    logger.warning(f"Usando dados em cache (possivelmente expirados) para {symbol} {interval}")
                    return cached_data
            
            return pd.DataFrame()
    
    def get_multi_symbol_data(self, symbols: List[str], intervals: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Obtém dados para múltiplos símbolos e intervalos usando multithreading.
        
        Args:
            symbols: Lista de símbolos
            intervals: Lista de intervalos
        
        Returns:
            Dictionary com estrutura: {symbol: {interval: dataframe}}
        """
        all_data = {}
        
        # Cria lista de tarefas
        tasks = []
        for symbol in symbols:
            for interval in intervals:
                tasks.append((symbol, interval))
        
        # Executa tarefas em paralelo com mais workers
        with ThreadPoolExecutor(max_workers=30) as executor:
            # Submete todas as tarefas
            future_to_task = {
                executor.submit(self.get_symbol_data, symbol, interval): (symbol, interval)
                for symbol, interval in tasks
            }
            
            # Processa resultados conforme completam
            for future in as_completed(future_to_task):
                symbol, interval = future_to_task[future]
                
                # Inicializa estrutura se necessário
                if symbol not in all_data:
                    all_data[symbol] = {}
                
                try:
                    data = future.result()
                    all_data[symbol][interval] = data
                    
                    if not data.empty:
                        logger.debug(f"Dados obtidos para {symbol} {interval}: {len(data)} registros")
                    else:
                        logger.warning(f"Nenhum dado obtido para {symbol} {interval}")
                        
                except Exception as e:
                    logger.error(f"Erro ao obter dados para {symbol} {interval}: {e}")
                    all_data[symbol][interval] = pd.DataFrame()
        
        return all_data
    
    def get_multi_symbol_data_batched(self, symbols: List[str], intervals: List[str], 
                                     batch_size: int = 10, delay_between_requests: float = 0.1, 
                                     fallback_to_cache: bool = True) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Obtém dados para múltiplos símbolos em lotes com delays para evitar rate limiting.
        
        Args:
            symbols: Lista de símbolos
            intervals: Lista de intervalos
            batch_size: Tamanho do lote (número de requisições paralelas)
            delay_between_requests: Delay entre requisições (em segundos)
            fallback_to_cache: Se deve usar cache como fallback em caso de erro
        
        Returns:
            Dictionary com estrutura: {symbol: {interval: dataframe}}
        """
        all_data = {}
        rate_limit_count = 0
        
        # Cria lista de tarefas
        tasks = []
        for symbol in symbols:
            for interval in intervals:
                tasks.append((symbol, interval))
        
        # Processa em lotes para evitar rate limiting
        total_tasks = len(tasks)
        processed_tasks = 0
        
        logger.info(f"Processando {total_tasks} tarefas em lotes de {batch_size} com delay de {delay_between_requests}s")
        
        for i in range(0, total_tasks, batch_size):
            batch_tasks = tasks[i:i + batch_size]
            
            # Executa lote atual com mais workers
            with ThreadPoolExecutor(max_workers=min(batch_size, 30)) as executor:
                # Submete tarefas do lote
                future_to_task = {
                    executor.submit(self.get_symbol_data, symbol, interval): (symbol, interval)
                    for symbol, interval in batch_tasks
                }
                
                # Processa resultados do lote
                for future in as_completed(future_to_task):
                    symbol, interval = future_to_task[future]
                    
                    # Inicializa estrutura se necessário
                    if symbol not in all_data:
                        all_data[symbol] = {}
                    
                    try:
                        data = future.result()
                        all_data[symbol][interval] = data
                        processed_tasks += 1
                        
                        if not data.empty:
                            logger.debug(f"Dados obtidos para {symbol} {interval}: {len(data)} registros ({processed_tasks}/{total_tasks})")
                        else:
                            logger.warning(f"Nenhum dado obtido para {symbol} {interval} ({processed_tasks}/{total_tasks})")
                            
                    except Exception as e:
                        if "Rate limit" in str(e):
                            rate_limit_count += 1
                            
                        logger.error(f"Erro ao obter dados para {symbol} {interval}: {e}")
                        
                        # Tenta fallback para cache se habilitado
                        if fallback_to_cache and self.cache_enabled:
                            try:
                                cached_data = self.get_symbol_data(symbol, interval, force_cache=True)
                                all_data[symbol][interval] = cached_data
                                if not cached_data.empty:
                                    logger.info(f"Usando dados em cache para {symbol} {interval}")
                                else:
                                    all_data[symbol][interval] = pd.DataFrame()
                            except:
                                all_data[symbol][interval] = pd.DataFrame()
                        else:
                            all_data[symbol][interval] = pd.DataFrame()
                            
                        processed_tasks += 1
            
            # Delay entre lotes para evitar rate limiting
            if i + batch_size < total_tasks:  # Não faz delay no último lote
                logger.debug(f"Lote {i//batch_size + 1} processado. Aguardando {delay_between_requests}s...")
                time.sleep(delay_between_requests)
        
        logger.info(f"Processamento concluído: {processed_tasks} tarefas processadas")
        if rate_limit_count > 0:
            logger.warning(f"Rate limiting detectado em {rate_limit_count} requisições")
            
        return all_data
    
    def get_required_days_for_renko(self, interval: str, brick_size: int = 1000) -> int:
        """
        Calcula dias necessários considerando Renko + StochRSI.
        
        Args:
            interval: Intervalo de tempo
            brick_size: Tamanho do tijolo Renko (None para ATR dinâmico)
            
        Returns:
            Número de dias necessários
        """
        # Se brick_size é None (ATR dinâmico), usa valor padrão conservador
        if brick_size is None:
            brick_size = 1000
            
        # Usa a função otimizada para Renko + StochRSI
        optimized_days = get_optimized_days_for_renko_stochrsi(interval, brick_size)
        
        # Aplica limite máximo para evitar requisições muito grandes
        max_days = {
            '1m': 30,      # Máximo 30 dias para 1 minuto
            '3m': 45,      # Máximo 45 dias para 3 minutos
            '5m': 60,      # Máximo 60 dias para 5 minutos
            '15m': 90,     # Máximo 90 dias para 15 minutos
            '30m': 120,    # Máximo 120 dias para 30 minutos
            '1h': 180,     # Máximo 180 dias para 1 hora
            '2h': 240,     # Máximo 240 dias para 2 horas
            '4h': 365,     # Máximo 365 dias para 4 horas
            '6h': 450,     # Máximo 450 dias para 6 horas
            '8h': 500,     # Máximo 500 dias para 8 horas
            '12h': 600,    # Máximo 600 dias para 12 horas
            '1d': 730,     # Máximo 730 dias para 1 dia (2 anos)
            '3d': 1095,    # Máximo 1095 dias para 3 dias (3 anos)
            '1w': 1460,    # Máximo 1460 dias para 1 semana (4 anos)
        }
        
        max_allowed = max_days.get(interval, 365)
        final_days = min(optimized_days, max_allowed)
        
        logger.debug(f"Dias calculados para {interval} (brick_size {brick_size}): "
                    f"otimizado={optimized_days}, máximo={max_allowed}, final={final_days}")
        
        return final_days

    def get_available_pairs(self) -> List[str]:
        """
        Obtém lista de pares disponíveis.
        
        Returns:
            Lista de símbolos disponíveis
        """
        # Corrigido: usando o método correto da API
        exchange_info = self.client.futures_exchange_info()
        return [symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['status'] == 'TRADING']
    
    def clear_cache(self):
        """Limpa todo o cache."""
        if not self.cache_enabled:
            logger.debug("Cache desabilitado, nenhuma limpeza necessária")
            return
        
        if not os.path.exists(self.cache_dir):
            logger.debug("Diretório de cache não existe, nenhuma limpeza necessária")
            return
        
        try:
            removed_files = 0
            total_files = 0
            
            # Lista todos os arquivos de cache
            try:
                cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
                total_files = len(cache_files)
            except (OSError, PermissionError) as e:
                logger.warning(f"Erro ao listar arquivos de cache: {e}")
                return
            
            # Remove cada arquivo
            for file in cache_files:
                file_path = os.path.join(self.cache_dir, file)
                try:
                    os.remove(file_path)
                    removed_files += 1
                    logger.debug(f"Arquivo de cache removido: {file}")
                except (OSError, PermissionError) as e:
                    logger.debug(f"Não foi possível remover cache {file}: {e}")
                except Exception as e:
                    logger.warning(f"Erro inesperado ao remover cache {file}: {e}")
            
            if removed_files > 0:
                logger.info(f"Cache limpo: {removed_files}/{total_files} arquivos removidos")
            else:
                logger.debug("Nenhum arquivo de cache foi removido")
                
        except Exception as e:
            logger.error(f"Erro inesperado ao limpar cache: {e}")
    
    def get_cache_info(self) -> Dict:
        """
        Obtém informações sobre o cache.
        
        Returns:
            Dict com informações sobre cache
        """
        if not self.cache_enabled:
            return {
                "enabled": False,
                "cache_dir": None,
                "cache_duration": 0,
                "files_count": 0,
                "total_size": 0
            }
        
        info = {
            "enabled": True,
            "cache_dir": self.cache_dir,
            "cache_duration": self.cache_duration,
            "files_count": 0,
            "total_size": 0
        }
        
        # Adiciona estatísticas detalhadas
        stats = self.get_cache_statistics()
        info.update(stats)
        
        return info

    def smart_cache_cleanup(self, force: bool = False) -> Dict:
        """
        Executa limpeza inteligente do cache.
        
        Args:
            force: Força limpeza mesmo se não for necessária
            
        Returns:
            Dict com resultados da limpeza
        """
        if not self.cache_enabled:
            return {
                "enabled": False,
                "cleaned_files": 0,
                "preserved_files": 0,
                "size_saved": 0
            }
        
        # Verifica se é necessário fazer limpeza
        if not force:
            stats = self.get_cache_statistics()
            total_files = stats.get('total_files', 0)
            outdated_files = stats.get('outdated_files', 0)
            
            # Só limpa se houver muitos arquivos desatualizados
            if total_files < 50 or outdated_files < 10:
                return {
                    "enabled": True,
                    "cleaned_files": 0,
                    "preserved_files": stats.get('useful_files', 0),
                    "size_saved": 0,
                    "reason": "Limpeza desnecessária"
                }
        
        # Executa limpeza
        initial_stats = self.get_cache_statistics()
        self.cleanup_cache()
        final_stats = self.get_cache_statistics()
        
        return {
            "enabled": True,
            "cleaned_files": initial_stats.get('outdated_files', 0),
            "preserved_files": final_stats.get('useful_files', 0) + final_stats.get('valid_files', 0),
            "size_saved": initial_stats.get('total_size', 0) - final_stats.get('total_size', 0),
            "reason": "Limpeza executada"
        }


# Instância global do gerenciador
_data_manager = None

def get_data_manager() -> DataManager:
    """
    Obtém a instância singleton do gerenciador de dados.
    
    Returns:
        Instância do DataManager
    """
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager

# Funções de conveniência (mantidas para compatibilidade)
def coletar_ohlc_multi(pairs: List[str], intervals: List[str], days: int = None) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Função de conveniência para coletar dados multi-timeframe.
    
    Args:
        pairs: Lista de pares
        intervals: Lista de intervalos
        days: Número de dias (ignorado - calculado automaticamente)
    
    Returns:
        Dictionary com dados
    """
    manager = get_data_manager()
    return manager.get_multi_symbol_data(pairs, intervals)
