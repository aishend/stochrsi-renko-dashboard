"""
Configurador do Sistema
=======================

Script para configurar facilmente o sistema.
"""

import os
import sys

def configure_api_keys():
    """Configura as chaves da API."""
    print("🔑 Configuração das Chaves da API Binance")
    print("=" * 50)
    
    print("\n📝 Você pode configurar as chaves de duas formas:")
    print("1. Variáveis de ambiente (recomendado)")
    print("2. Arquivo de configuração")
    
    choice = input("\nEscolha uma opção (1 ou 2): ").strip()
    
    if choice == "1":
        configure_environment_variables()
    elif choice == "2":
        configure_config_file()
    else:
        print("❌ Opção inválida!")
        return False
    
    return True

def configure_environment_variables():
    """Configura variáveis de ambiente."""
    print("\n🌍 Configuração via Variáveis de Ambiente")
    print("-" * 40)
    
    api_key = input("Digite sua API Key: ").strip()
    api_secret = input("Digite sua API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("❌ Chaves não podem estar vazias!")
        return False
    
    print(f"\n💡 Para configurar as variáveis de ambiente:")
    print(f"Windows PowerShell:")
    print(f'$env:BINANCE_KEY="{api_key}"')
    print(f'$env:BINANCE_SECRET="{api_secret}"')
    
    print(f"\nWindows CMD:")
    print(f'set BINANCE_KEY={api_key}')
    print(f'set BINANCE_SECRET={api_secret}')
    
    print(f"\nLinux/Mac:")
    print(f'export BINANCE_KEY={api_key}')
    print(f'export BINANCE_SECRET={api_secret}')
    
    print(f"\n⚠️  Execute um dos comandos acima no terminal antes de executar o sistema!")
    return True

def configure_config_file():
    """Configura arquivo de configuração."""
    print("\n📄 Configuração via Arquivo")
    print("-" * 30)
    
    api_key = input("Digite sua API Key: ").strip()
    api_secret = input("Digite sua API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("❌ Chaves não podem estar vazias!")
        return False
    
    # Atualiza o arquivo de configuração
    config_content = f'''"""
Configuração da API Binance
===========================

Arquivo gerado automaticamente pelo configurador.
"""

# Suas credenciais da API Binance
BINANCE_KEY = "{api_key}"
BINANCE_SECRET = "{api_secret}"

# Configurações opcionais
TESTNET = False
BASE_URL = "https://fapi.binance.com"
'''
    
    try:
        with open('api_config.py', 'w') as f:
            f.write(config_content)
        
        print("✅ Arquivo api_config.py criado com sucesso!")
        
        # Atualiza também o settings.py
        update_settings_file()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo: {e}")
        return False

def update_settings_file():
    """Atualiza o arquivo settings.py para usar api_config.py."""
    try:
        settings_path = 'config/settings.py'
        
        # Lê o arquivo atual
        with open(settings_path, 'r') as f:
            content = f.read()
        
        # Adiciona importação do api_config se não existir
        if 'from api_config import' not in content:
            import_line = '''
# Importa credenciais do arquivo api_config.py se existir
try:
    from api_config import BINANCE_KEY as API_KEY, BINANCE_SECRET as API_SECRET
    api_key_from_file = API_KEY
    api_secret_from_file = API_SECRET
except ImportError:
    api_key_from_file = None
    api_secret_from_file = None
'''
            
            # Substitui a configuração do BINANCE_CONFIG
            old_config = '''# Configurações da API Binance
BINANCE_CONFIG = {
    'KEY': os.environ.get('BINANCE_KEY', 'COLOQUE_SUA_BINANCE_API_KEY_AQUI'),
    'SECRET': os.environ.get('BINANCE_SECRET', 'COLOQUE_SUA_BINANCE_API_SECRET_AQUI'),'''
            
            new_config = '''# Configurações da API Binance
BINANCE_CONFIG = {
    'KEY': os.environ.get('BINANCE_KEY', api_key_from_file or 'COLOQUE_SUA_BINANCE_API_KEY_AQUI'),
    'SECRET': os.environ.get('BINANCE_SECRET', api_secret_from_file or 'COLOQUE_SUA_BINANCE_API_SECRET_AQUI'),'''
            
            # Adiciona a importação no início
            content = import_line + content
            
            # Substitui a configuração
            content = content.replace(old_config, new_config)
            
            # Salva o arquivo
            with open(settings_path, 'w') as f:
                f.write(content)
            
            print("✅ Arquivo settings.py atualizado!")
            
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível atualizar settings.py: {e}")

def install_dependencies():
    """Instala dependências."""
    print("\n📦 Instalação de Dependências")
    print("-" * 30)
    
    install = input("Deseja instalar as dependências automaticamente? (s/n): ").strip().lower()
    
    if install == 's':
        try:
            os.system("pip install -r requirements.txt")
            print("✅ Dependências instaladas!")
        except Exception as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            print("Execute manualmente: pip install -r requirements.txt")
    else:
        print("💡 Execute manualmente: pip install -r requirements.txt")

def main():
    """Função principal."""
    print("🚀 Configurador do Sistema de Trading Renko")
    print("=" * 50)
    
    # Verifica se requirements.txt existe
    if not os.path.exists('requirements.txt'):
        print("❌ Arquivo requirements.txt não encontrado!")
        print("Certifique-se de estar no diretório correto do projeto.")
        return
    
    # Instala dependências
    install_dependencies()
    
    # Configura API
    if not configure_api_keys():
        print("❌ Configuração cancelada!")
        return
    
    print("\n🎉 Configuração concluída!")
    print("\n🧪 Próximos passos:")
    print("1. Execute: python test_system.py")
    print("2. Se tudo estiver OK: python run_system.py")
    print("3. Para dashboard: streamlit run dashboard/dashboard.py")
    
    # Pergunta se quer testar agora
    test_now = input("\nDeseja executar o teste agora? (s/n): ").strip().lower()
    
    if test_now == 's':
        print("\n🧪 Executando teste...")
        os.system("python test_system.py")

if __name__ == "__main__":
    main()
