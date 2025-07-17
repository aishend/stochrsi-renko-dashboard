# Sistema de Trading Renko - Uso com Todos os Pares

## 🚀 Comandos Disponíveis

### 1. Dashboard com Todos os Pares
```bash
python run_system.py --all-pairs
```
- Carrega **TODOS** os pares do arquivo `trading_pairs.py`
- Interface web completa
- Análise em tempo real
- Filtros avançados

### 2. Dashboard no Modo Teste
```bash
python run_system.py --test
```
- Usa apenas 5 pares (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, ADAUSDT)
- Ideal para desenvolvimento
- Carregamento rápido

### 3. Dashboard Padrão
```bash
python run_system.py
```
- Usa os primeiros 20 pares
- Balanceio entre performance e abrangência
- Carregamento médio

### 4. Análise Completa (Sem Interface)
```bash
python run_system.py --analysis
```
- Processa todos os pares
- Salva resultados em JSON
- Execução em lote

### 5. Teste de Todos os Pares
```bash
python test_all_pairs.py
```
- Testa sistema com todos os pares
- Mostra relatório detalhado
- Salva resultados em arquivo

## 📊 Pares Disponíveis

O sistema usa o arquivo `trading_pairs.py` que contém **{total_pares}** pares de trading:

### Principais Categorias:
- **USDT**: Pares com Tether (maioria)
- **BTC**: Pares com Bitcoin
- **ETH**: Pares com Ethereum
- **USDC**: Pares com USD Coin

### Exemplos de Pares:
```
BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT,
ADAUSDT, DOGEUSDT, AVAXUSDT, TRXUSDT, LINKUSDT,
DOTUSDT, MATICUSDT, LTCUSDT, SHIBUSDT, UNIUSDT,
... e muitos mais
```

## ⚙️ Configurações

### Timeframes Disponíveis:
- `1m` - 1 minuto
- `5m` - 5 minutos
- `15m` - 15 minutos
- `1h` - 1 hora
- `4h` - 4 horas
- `1d` - 1 dia

### Filtros StochRSI:
- **Todos Acima**: Mostra apenas pares com StochRSI acima de um valor
- **Todos Abaixo**: Mostra apenas pares com StochRSI abaixo de um valor
- **Extremos**: Filtra pares em sobrecompra/sobrevenda
- **Intervalo**: Filtra pares em faixa específica

## 🔧 Parâmetros Avançados

### ATR (Average True Range):
- **Período**: 14 (padrão)
- **Automático**: Calcula brick size baseado na volatilidade
- **Fixo**: Usa valor fixo para brick size

### Cache:
- **Ativo**: Usa dados em cache quando disponível
- **Forçar**: Força coleta de novos dados
- **Fallback**: Usa cache se API falhar

### Performance:
- **Batch Size**: 10 pares por vez
- **Delay**: 0.1s entre requisições
- **Timeout**: 30s por requisição

## 📈 Exemplos de Uso

### Exemplo 1: Análise Rápida
```bash
# Inicia dashboard com todos os pares
python run_system.py --all-pairs

# Configurações recomendadas:
# - Timeframes: 1h, 4h, 1d
# - Filtro: Todos abaixo de 30 (sobrevenda)
# - ATR: Automático
```

### Exemplo 2: Busca por Sinais
```bash
# Teste todos os pares e salva resultados
python test_all_pairs.py

# Depois abra o dashboard para análise visual
python run_system.py --all-pairs
```

### Exemplo 3: Desenvolvimento
```bash
# Modo teste para desenvolvimento
python run_system.py --test

# Apenas 5 pares para testes rápidos
```

## 📊 Interpretação dos Resultados

### StochRSI:
- **0-20**: Sobrevenda (possível compra)
- **20-80**: Zona neutra
- **80-100**: Sobrecompra (possível venda)

### Sinais Renko:
- **Tijolo Verde**: Movimento de alta
- **Tijolo Vermelho**: Movimento de baixa
- **Sequência**: Tendência confirmada

### Filtros:
- **Todos Acima 70**: Mercado em alta
- **Todos Abaixo 30**: Oportunidades de compra
- **Extremos**: Reversões potenciais

## 🚨 Avisos Importantes

### Rate Limiting:
- **Delay**: Sistema usa delay automático
- **Batch**: Processa pares em lotes
- **Cache**: Usa cache para evitar requisições

### Performance:
- **Todos os pares**: Pode demorar 2-3 minutos para carregar
- **Modo teste**: Carrega em ~30 segundos
- **Análise**: Pode demorar 5-10 minutos

### Dados:
- **Histórico**: Usa períodos otimizados por timeframe
- **Qualidade**: Valida dados antes de processar
- **Fallback**: Usa cache se API falhar

## 📞 Suporte

### Logs:
- **Arquivo**: `trading_system.log`
- **Nível**: INFO/ERROR
- **Rotação**: Automática

### Troubleshooting:
1. **Erro de API**: Verifique configurações em `config/settings.py`
2. **Dados insuficientes**: Aguarde ou use cache
3. **Rate limit**: Aumente delay entre requisições
4. **Memória**: Use modo teste para desenvolvimento

### Comandos Úteis:
```bash
# Limpa cache
rm -rf cache/

# Verifica logs
tail -f trading_system.log

# Teste de conectividade
python -c "from src.api.binance_client import test_connection; test_connection()"
```

---

## 🎯 Resumo dos Comandos

| Comando | Descrição | Pares | Tempo |
|---------|-----------|-------|-------|
| `python run_system.py --all-pairs` | Dashboard completo | Todos | ~3 min |
| `python run_system.py --test` | Dashboard teste | 5 | ~30 seg |
| `python run_system.py` | Dashboard padrão | 20 | ~1 min |
| `python run_system.py --analysis` | Análise em lote | Todos | ~5 min |
| `python test_all_pairs.py` | Teste completo | Todos | ~10 min |

**Recomendação**: Use `--all-pairs` para análise completa de mercado!
