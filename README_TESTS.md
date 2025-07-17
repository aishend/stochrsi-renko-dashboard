# Testes ATR Renko - 5 Pares

Este documento explica como usar os scripts de teste simplificados para testar o sistema ATR Renko com apenas 5 pares de moedas.

## 📁 Arquivos de Teste

### 1. `test_5_pairs.py`
Script principal que executa todos os testes com 5 pares de moedas:
- BTCUSDT
- ETHUSDT
- BNBUSDT
- SOLUSDT
- ADAUSDT

### 2. `test_pairs_config.py`
Configuração dos pares de teste e suas características específicas.

### 3. `dashboard_test.py`
Dashboard simplificado para visualizar os resultados dos testes.

### 4. `run_tests.py`
Script para executar diferentes tipos de testes de forma interativa.

## 🚀 Como Executar

### Opção 1: Teste Direto (Recomendado)
```bash
python test_5_pairs.py
```

### Opção 2: Menu Interativo
```bash
python run_tests.py
```

### Opção 3: Dashboard de Teste
```bash
python -m streamlit run dashboard_test.py
```

### Opção 4: Testes Específicos
```bash
# Apenas teste de 5 pares
python run_tests.py --test 5pairs

# Dashboard de teste
python run_tests.py --test dashboard

# Dashboard principal
python run_tests.py --test main
```

## 🧪 Testes Executados

### Teste 1: Cálculo do ATR
- Calcula ATR para cada par e timeframe
- Verifica se o brick size é calculado corretamente
- Mostra valores de ATR e brick size

### Teste 2: Geração de Renko
- Gera dados Renko com ATR dinâmico
- Compara com brick size fixo
- Conta número de tijolos gerados

### Teste 3: Brick Size Calculation
- Testa apenas o cálculo do brick size
- Diferentes períodos de ATR (7, 14, 21, 30)
- Sem gerar dados Renko

### Teste 4: Classe RenkoIndicator
- Testa a classe diretamente
- ATR automático vs brick size fixo
- Funcionalidade de alternar ATR

### Teste 5: Adaptação à Volatilidade + StochRSI
- Mostra como o brick size se adapta à volatilidade
- Diferentes timeframes
- Cálculo de volatilidade dos retornos
- Cálculo do StochRSI nos dados Renko

### Teste 6: Cálculo do StochRSI
- Teste específico do indicador StochRSI
- Estatísticas completas (média, desvio, range)
- Classificação de sinais (sobrecompra/sobrevenda/neutro)
- Comparação entre tijolos Renko e períodos StochRSI

## 📊 Exemplo de Saída

```
🚀 INICIANDO TESTES ATR RENKO - 5 PARES
📅 Data: 2025-01-15 10:30:00
🪙 Pares: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, ADAUSDT
⏰ Timeframes: 15m, 1h, 4h, 1d

============================================================
TESTE 1: Cálculo do ATR para 5 pares
============================================================

📊 Testando BTCUSDT:
   ✅ 15m: ATR=45.123456, Brick Size=45.120000
   ✅ 1h: ATR=132.364953, Brick Size=132.360000
   ✅ 4h: ATR=298.742156, Brick Size=298.740000
   ✅ 1d: ATR=756.893421, Brick Size=756.890000
```

## ⚙️ Configurações

### Pares de Teste
Definidos em `test_pairs_config.py`:
```python
TEST_PAIRS = [
    'BTCUSDT',
    'ETHUSDT',
    'BNBUSDT',
    'SOLUSDT',
    'ADAUSDT'
]
```

### Timeframes
```python
TEST_TIMEFRAMES = ['15m', '1h', '4h', '1d']
```

### Configurações Específicas por Par
```python
PAIR_CONFIGS = {
    'BTCUSDT': {
        'tick_size': 0.01,
        'min_brick_size': 10,
        'max_brick_size': 1000,
    },
    'ADAUSDT': {
        'tick_size': 0.0001,
        'min_brick_size': 0.001,
        'max_brick_size': 0.1,
    }
    # ...
}
```

## 🔧 Personalização

### Alterar Pares de Teste
Edite `test_pairs_config.py` e modifique a lista `TRADING_PAIRS_TEST`.

### Alterar Timeframes
Modifique `TEST_TIMEFRAMES` no mesmo arquivo.

### Configurar Delay
Para evitar rate limiting, ajuste o delay entre requisições:
```python
time.sleep(0.5)  # 500ms entre requisições
```

## 📈 Benefícios dos Testes Limitados

1. **Velocidade**: Testes executam em ~20-30 segundos
2. **Foco**: Concentra nos pares mais importantes
3. **Depuração**: Mais fácil identificar problemas
4. **Recursos**: Menor uso de API calls
5. **Desenvolvimento**: Iteração mais rápida

## 🚨 Troubleshooting

### Problema: Rate Limiting
```
Solução: Aumente o delay entre requisições
time.sleep(1.0)  # 1 segundo
```

### Problema: Dados Insuficientes
```
Solução: Verifique se há dados em cache ou conectividade
```

### Problema: Erro de Importação
```
Solução: Certifique-se de estar no diretório correto
cd "c:\Users\leandro afonso\Desktop\renko"
```

## 📝 Logs

Os logs são salvos em `trading_system.log` e mostram:
- Cálculos de ATR
- Geração de dados Renko
- Brick sizes calculados
- Erros e warnings

## 🔄 Desenvolvimento

Para adicionar novos testes:
1. Edite `test_5_pairs.py`
2. Adicione nova função de teste
3. Chame a função em `main()`
4. Documente no README

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs
2. Execute teste individual
3. Valide configurações
4. Teste conectividade de rede
