# Sistema de Trading Renko + StochRSI

Sistema completo de análise técnica baseado em gráficos Renko e indicador StochRSI para trading de criptomoedas.

## 🚀 Características

- **Dashboard Web Interativo**: Interface moderna com Streamlit
- **Múltiplos Pares**: Análise simultânea de vários pares de trading
- **Múltiplos Timeframes**: Suporte para diferentes intervalos de tempo
- **Indicadores Técnicos**: Renko + StochRSI integrados
- **Cache Inteligente**: Sistema de cache para otimizar performance
- **Logging Completo**: Sistema de logs para monitoramento
- **Arquitetura Modular**: Código bem organizado e extensível

## 📁 Estrutura do Projeto

```
renko/
├── src/                          # Código fonte principal
│   ├── api/                     # Cliente da API Binance
│   ├── indicators/              # Indicadores técnicos
│   ├── data/                    # Gerenciamento de dados
│   └── utils/                   # Utilitários
├── dashboard/                   # Interface web
├── config/                      # Configurações
├── cache/                       # Cache de dados (gerado automaticamente)
├── requirements.txt             # Dependências
├── run_system.py               # Script principal
└── README.md                   # Este arquivo
```

## 🛠️ Instalação

### 1. Clone ou baixe o projeto

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as credenciais da API Binance

**Opção 1: Variáveis de ambiente (Recomendado)**
```bash
set BINANCE_KEY=sua_api_key_aqui
set BINANCE_SECRET=sua_api_secret_aqui
```

**Opção 2: Arquivo de configuração**
Edite o arquivo `config/settings.py` e altere as variáveis:
```python
BINANCE_CONFIG = {
    'KEY': 'sua_api_key_aqui',
    'SECRET': 'sua_api_secret_aqui',
    # ...
}
```

### 4. Execute o sistema
```bash
python run_system.py
```

## 📊 Como Usar

### Dashboard Principal

1. **Acesse o dashboard**: O sistema abrirá automaticamente no navegador
2. **Selecione pares**: Use a barra lateral para escolher pares de trading
3. **Configure timeframes**: Selecione os intervalos de tempo desejados
4. **Ajuste parâmetros**: Configure tamanho do tijolo Renko e outros parâmetros
5. **Analise resultados**: Visualize os indicadores e sinais gerados

### Filtros Disponíveis

- **Populares**: Pares mais negociados
- **Todos**: Todos os pares disponíveis
- **Por Volume**: Filtro por volume de 24h
- **Stablecoins**: Pares com stablecoins
- **Personalizado**: Filtro por padrão customizado

### Sinais do StochRSI

- 🟢 **Oversold**: Possível sinal de compra (K < 20, D < 20)
- 🔴 **Overbought**: Possível sinal de venda (K > 80, D > 80)
- ⬆️ **Bullish**: Tendência de alta (K > D)
- ⬇️ **Bearish**: Tendência de baixa (K < D)

## 🔧 Configuração Avançada

### Parâmetros do StochRSI

Edite `config/settings.py`:
```python
INDICATOR_CONFIG = {
    'stoch_rsi': {
        'period': 14,           # Período do RSI
        'stoch_period': 14,     # Período do Stochastic
        'k_period': 3,          # Suavização do %K
        'd_period': 3           # Suavização do %D
    }
}
```

### Parâmetros do Renko

```python
INDICATOR_CONFIG = {
    'renko': {
        'default_brick_size': 1000,  # Tamanho padrão do tijolo
        'min_brick_size': 100,       # Tamanho mínimo
        'max_brick_size': 10000      # Tamanho máximo
    }
}
```

### Cache

```python
DATA_CONFIG = {
    'cache_enabled': True,      # Habilitar cache
    'cache_duration': 300,      # Duração em segundos
    'max_retries': 3,           # Tentativas máximas
    'retry_delay': 1            # Delay entre tentativas
}
```

## 🔍 Módulos Principais

### 1. API (`src/api/`)
- **binance_client.py**: Cliente otimizado para API Binance

### 2. Indicadores (`src/indicators/`)
- **renko.py**: Implementação do indicador Renko
- **stoch_rsi.py**: Implementação do StochRSI

### 3. Dados (`src/data/`)
- **data_manager.py**: Gerenciamento de dados com cache
- **trading_pairs.py**: Gerenciamento de pares de trading

### 4. Dashboard (`dashboard/`)
- **dashboard.py**: Interface web principal

### 5. Configuração (`config/`)
- **settings.py**: Configurações centralizadas

## 🚨 Considerações Importantes

### Segurança
- **Nunca compartilhe suas chaves da API**
- Use variáveis de ambiente para credenciais
- Mantenha permissões mínimas na API (apenas leitura)

### Performance
- O cache é habilitado por padrão para melhor performance
- Limite o número de pares simultâneos para evitar rate limiting
- Use timeframes maiores para análises de longo prazo

### Disclaimers
- Este sistema é apenas para fins educacionais e de análise
- Não constitui aconselhamento financeiro
- Trading envolve riscos - use por sua conta e risco

## 🔧 Desenvolvimento

### Estrutura Modular
O código foi projetado para ser facilmente extensível:

```python
# Exemplo: Adicionar novo indicador
from src.indicators.base import BaseIndicator

class NovoIndicador(BaseIndicator):
    def calculate(self, data):
        # Sua implementação aqui
        pass
```

### Logging
Logs são salvos em `trading_system.log`:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Sua mensagem aqui")
```

## 📈 Próximas Funcionalidades

- [ ] Mais indicadores técnicos
- [ ] Backtesting automático
- [ ] Alertas em tempo real
- [ ] Exportação de dados
- [ ] API REST própria
- [ ] Suporte a mais exchanges

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Mantenha a estrutura modular
2. Adicione testes quando possível
3. Documente novas funcionalidades
4. Siga as convenções de código existentes

## 📝 Licença

Este projeto é livre para uso educacional e pessoal.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique os logs em `trading_system.log`
2. Confirme se as credenciais da API estão corretas
3. Verifique a conexão com a internet
4. Consulte a documentação da API Binance

---

**⚠️ Aviso**: Este sistema é apenas para fins educacionais. Trading envolve riscos significativos. Use com responsabilidade.
