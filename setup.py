#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
SISTEMA DE CREDIÁRIO - AÇOUGUE
Script de Instalação e Configuração
========================================

Este script configura o sistema automaticamente:
- Instala dependências
- Configura banco de dados
- Cria estrutura inicial
- Testa componentes
- Gera executável (opcional)

Uso:
    python setup.py --install          # Instalação completa
    python setup.py --config-db        # Apenas configurar BD
    python setup.py --test             # Apenas testar
    python setup.py --build-exe        # Gerar executável
    python setup.py --help             # Ajuda
"""

import os
import sys
import subprocess
import argparse
import json
import getpass
from pathlib import Path
import shutil
import time

# Cores para output no terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKGREEN):
    """Imprimir mensagem colorida"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(title):
    """Imprimir cabeçalho"""
    print("\n" + "="*60)
    print_colored(f"  {title}", Colors.HEADER + Colors.BOLD)
    print("="*60)

def print_step(step, total, description):
    """Imprimir passo atual"""
    print_colored(f"\n[{step}/{total}] {description}", Colors.OKCYAN)

def print_success(message):
    """Imprimir mensagem de sucesso"""
    print_colored(f"✓ {message}", Colors.OKGREEN)

def print_warning(message):
    """Imprimir aviso"""
    print_colored(f"⚠ {message}", Colors.WARNING)

def print_error(message):
    """Imprimir erro"""
    print_colored(f"✗ {message}", Colors.FAIL)

def run_command(command, description="", check=True):
    """Executar comando do sistema"""
    if description:
        print(f"  → {description}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        
        if result.returncode == 0:
            if description:
                print_success(f"{description} - Concluído")
            return True, result.stdout
        else:
            print_error(f"Erro: {result.stderr}")
            return False, result.stderr
            
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao executar: {e}")
        return False, str(e)

def check_python_version():
    """Verificar versão do Python"""
    print_step(1, 10, "Verificando versão do Python")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} não suportado. Necessário Python 3.8+")
        return False

def create_virtual_environment():
    """Criar ambiente virtual"""
    print_step(2, 10, "Criando ambiente virtual")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Ambiente virtual já existe. Removendo...")
        shutil.rmtree(venv_path)
    
    success, output = run_command(
        f"{sys.executable} -m venv venv",
        "Criando ambiente virtual"
    )
    
    if success:
        print_success("Ambiente virtual criado")
        return True
    else:
        print_error("Falha ao criar ambiente virtual")
        return False

def install_dependencies():
    """Instalar dependências"""
    print_step(3, 10, "Instalando dependências")
    
    # Determinar comando pip baseado no OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Linux/Mac
        pip_cmd = "venv/bin/pip"
    
    # Atualizar pip
    success, _ = run_command(
        f"{pip_cmd} install --upgrade pip",
        "Atualizando pip"
    )
    
    if not success:
        print_warning("Falha ao atualizar pip, continuando...")
    
    # Instalar dependências básicas primeiro
    basic_deps = [
        "Flask==2.3.3",
        "mysql-connector-python==8.2.0",
        "python-dotenv==1.0.0",
        "openpyxl==3.1.2"
    ]
    
    for dep in basic_deps:
        success, _ = run_command(
            f"{pip_cmd} install {dep}",
            f"Instalando {dep.split('==')[0]}"
        )
        if not success:
            print_error(f"Falha ao instalar {dep}")
            return False
    
    # Tentar instalar dependências opcionais
    optional_deps = [
        "python-escpos==3.0a9",
        "bcrypt==4.0.1",
        "APScheduler==3.10.4"
    ]
    
    for dep in optional_deps:
        success, _ = run_command(
            f"{pip_cmd} install {dep}",
            f"Instalando {dep.split('==')[0]} (opcional)",
            check=False
        )
        if not success:
            print_warning(f"Dependência opcional {dep.split('==')[0]} não instalada")
    
    print_success("Dependências instaladas")
    return True

def create_directory_structure():
    """Criar estrutura de diretórios"""
    print_step(4, 10, "Criando estrutura de diretórios")
    
    directories = [
        "logs",
        "backups",
        "exports",
        "uploads",
        "static/img",
        "comprovantes"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"  → Diretório {directory} criado")
    
    print_success("Estrutura de diretórios criada")
    return True

def configure_database():
    """Configurar banco de dados"""
    print_step(5, 10, "Configurando banco de dados")
    
    print("\nConfiguração do Banco de Dados MySQL:")
    print("Por favor, forneça as informações de conexão:\n")
    
    # Coletar informações do banco
    db_config = {}
    db_config['host'] = input("Host do MySQL [localhost]: ").strip() or 'localhost'
    db_config['user'] = input("Usuário do MySQL [root]: ").strip() or 'root'
    db_config['password'] = getpass.getpass("Senha do MySQL: ")
    db_config['database'] = input("Nome do banco [acougue_db]: ").strip() or 'acougue_db'
    
    # Testar conexão
    try:
        import mysql.connector
        
        # Primeiro, conectar sem especificar banco para criá-lo
        print("  → Testando conexão...")
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cursor = connection.cursor()
        
        # Criar banco se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print_success(f"Banco {db_config['database']} criado/verificado")
        
        cursor.close()
        connection.close()
        
        # Testar conexão com o banco específico
        connection = mysql.connector.connect(**db_config)
        connection.close()
        
        print_success("Conexão com banco estabelecida")
        
        # Criar arquivo .env
        env_content = f"""# Configurações do Banco de Dados
DB_HOST={db_config['host']}
DB_USER={db_config['user']}
DB_PASSWORD={db_config['password']}
DB_NAME={db_config['database']}

# Configurações do Sistema
SECRET_KEY=sua-chave-secreta-{int(time.time())}
DEBUG=True
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print_success("Arquivo .env criado")
        return True
        
    except ImportError:
        print_error("mysql-connector-python não instalado")
        return False
    except Exception as e:
        print_error(f"Erro ao conectar: {e}")
        return False

def create_database_tables():
    """Criar tabelas do banco"""
    print_step(6, 10, "Criando tabelas do banco")
    
    try:
        # Importar módulo da aplicação
        sys.path.insert(0, '.')
        from database import Database
        
        db = Database()
        db.create_tables()
        db.insert_initial_data()
        
        print_success("Tabelas criadas com sucesso")
        return True
        
    except Exception as e:
        print_error(f"Erro ao criar tabelas: {e}")
        return False

def configure_system():
    """Configurar sistema"""
    print_step(7, 10, "Configurando sistema")
    
    print("\nConfiguração do Sistema:")
    
    # Configurações da empresa
    empresa_config = {}
    empresa_config['nome_empresa'] = input("Nome da empresa [Açougue do João]: ").strip() or 'Açougue do João'
    empresa_config['endereco'] = input("Endereço da empresa: ").strip()
    empresa_config['telefone'] = input("Telefone da empresa: ").strip()
    empresa_config['cnpj'] = input("CNPJ da empresa: ").strip()
    
    # Senha do sistema
    print("\n" + "-"*40)
    print("IMPORTANTE: Defina uma senha para acessar o sistema")
    while True:
        senha1 = getpass.getpass("Nova senha do sistema: ")
        senha2 = getpass.getpass("Confirme a senha: ")
        
        if senha1 == senha2:
            if len(senha1) >= 6:
                break
            else:
                print_error("Senha deve ter pelo menos 6 caracteres")
        else:
            print_error("Senhas não coincidem")
    
    # Atualizar config.py com as configurações
    try:
        config_template = f"""import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-{int(time.time())}'
    DEBUG = True
    
    DATABASE_CONFIG = {{
        'host': os.environ.get('DB_HOST') or 'localhost',
        'user': os.environ.get('DB_USER') or 'root',
        'password': os.environ.get('DB_PASSWORD') or '',
        'database': os.environ.get('DB_NAME') or 'acougue_db',
        'charset': 'utf8mb4',
        'autocommit': True
    }}
    
    SISTEMA_CONFIGS = {{
        'nome_empresa': '{empresa_config['nome_empresa']}',
        'endereco': '{empresa_config['endereco']}',
        'telefone': '{empresa_config['telefone']}',
        'cnpj': '{empresa_config['cnpj']}',
        'limite_inadimplencia_dias': 30,
        'limite_credito_default': 500.00,
        'senha_sistema': '{senha1}'
    }}
    
    PRINTER_CONFIG = {{
        'interface': 'usb',
        'vendor_id': 0x1a2b,
        'product_id': 0x3c4d,
        'timeout': 5000,
        'codepage': 'cp850'
    }}
    
    UPLOAD_FOLDER = 'uploads'
    BACKUP_FOLDER = 'backups'
    EXPORT_FOLDER = 'exports'
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {{
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}}
"""
        
        # Backup do config original se existir
        if os.path.exists('config.py'):
            shutil.copy2('config.py', 'config.py.backup')
        
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_template)
        
        print_success("Configurações do sistema salvas")
        return True
        
    except Exception as e:
        print_error(f"Erro ao salvar configurações: {e}")
        return False

def test_system():
    """Testar sistema"""
    print_step(8, 10, "Testando sistema")
    
    try:
        # Importar e testar módulos principais
        print("  → Testando importações...")
        
        sys.path.insert(0, '.')
        import config
        print("    ✓ config.py")
        
        import database
        print("    ✓ database.py")
        
        import business
        print("    ✓ business.py")
        
        import utils
        print("    ✓ utils.py")
        
        # Testar conexão com banco
        print("  → Testando conexão com banco...")
        db = database.Database()
        stats = db.get_estatisticas_dashboard()
        print("    ✓ Conexão com banco funcionando")
        
        # Testar importação da aplicação Flask
        print("  → Testando aplicação Flask...")
        import app
        print("    ✓ Aplicação Flask carregada")
        
        print_success("Todos os testes passaram")
        return True
        
    except Exception as e:
        print_error(f"Erro nos testes: {e}")
        return False

def create_launcher_scripts():
    """Criar scripts de inicialização"""
    print_step(9, 10, "Criando scripts de inicialização")
    
    # Script para Windows
    windows_script = """@echo off
echo Iniciando Sistema de Crediario do Acougue...
cd /d "%~dp0"
call venv\\Scripts\\activate
python app.py
pause
"""
    
    with open('iniciar_sistema.bat', 'w', encoding='utf-8') as f:
        f.write(windows_script)
    
    # Script para Linux/Mac
    linux_script = """#!/bin/bash
echo "Iniciando Sistema de Crediário do Açougue..."
cd "$(dirname "$0")"
source venv/bin/activate
python app.py
"""
    
    with open('iniciar_sistema.sh', 'w', encoding='utf-8') as f:
        f.write(linux_script)
    
    # Tornar executável no Linux/Mac
    if os.name != 'nt':
        os.chmod('iniciar_sistema.sh', 0o755)
    
    print_success("Scripts de inicialização criados")
    return True

def create_documentation():
    """Criar documentação básica"""
    print_step(10, 10, "Criando documentação")
    
    readme_content = """# Sistema de Crediário - Açougue

## Como usar

### Windows
Execute: `iniciar_sistema.bat`

### Linux/Mac
Execute: `./iniciar_sistema.sh`

### Manual
```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\\Scripts\\activate   # Windows

# Iniciar sistema
python app.py
```

## Acesso
- Abra o navegador em: http://localhost:5000
- Use a senha configurada durante a instalação

## Funcionalidades
- ✅ Gestão de clientes
- ✅ Controle de vendas
- ✅ Processamento de pagamentos
- ✅ Relatórios
- ✅ Impressão de comprovantes
- ✅ Backup automático

## Suporte
Para suporte, verifique os logs em `logs/sistema.log`

## Backup
Backups são salvos automaticamente em `backups/`
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print_success("Documentação criada")
    return True

def build_executable():
    """Gerar executável com PyInstaller"""
    print_header("GERANDO EXECUTÁVEL")
    
    try:
        # Verificar se PyInstaller está instalado
        success, _ = run_command("pyinstaller --version", check=False)
        if not success:
            print("PyInstaller não encontrado. Instalando...")
            if os.name == 'nt':  # Windows
                pip_cmd = "venv\\Scripts\\pip"
            else:  # Linux/Mac
                pip_cmd = "venv/bin/pip"
            
            success, _ = run_command(f"{pip_cmd} install pyinstaller")
            if not success:
                print_error("Falha ao instalar PyInstaller")
                return False
        
        print("Gerando executável... (pode demorar alguns minutos)")
        
        # Comando PyInstaller
        cmd = """pyinstaller --onefile --windowed --add-data "templates;templates" --add-data "static;static" --name "SistemaAcougue" app.py"""
        
        success, _ = run_command(cmd, "Compilando aplicação")
        
        if success:
            print_success("Executável criado em dist/SistemaAcougue.exe")
            return True
        else:
            print_error("Falha ao gerar executável")
            return False
            
    except Exception as e:
        print_error(f"Erro ao gerar executável: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Setup do Sistema de Crediário')
    parser.add_argument('--install', action='store_true', help='Instalação completa')
    parser.add_argument('--config-db', action='store_true', help='Apenas configurar banco')
    parser.add_argument('--test', action='store_true', help='Apenas testar sistema')
    parser.add_argument('--build-exe', action='store_true', help='Gerar executável')
    
    args = parser.parse_args()
    
    print_header("SISTEMA DE CREDIÁRIO - AÇOUGUE")
    print_colored("Setup e Configuração Automática", Colors.OKBLUE)
    
    if args.config_db:
        configure_database()
        create_database_tables()
        
    elif args.test:
        test_system()
        
    elif args.build_exe:
        build_executable()
        
    elif args.install:
        # Instalação completa
        steps = [
            check_python_version,
            create_virtual_environment,
            install_dependencies,
            create_directory_structure,
            configure_database,
            create_database_tables,
            configure_system,
            test_system,
            create_launcher_scripts,
            create_documentation
        ]
        
        success = True
        for step in steps:
            if not step():
                success = False
                break
        
        if success:
            print_header("INSTALAÇÃO CONCLUÍDA!")
            print_colored("✓ Sistema instalado e configurado com sucesso!", Colors.OKGREEN)
            print_colored("\nPara iniciar o sistema:", Colors.OKBLUE)
            print_colored("  Windows: iniciar_sistema.bat", Colors.OKCYAN)
            print_colored("  Linux/Mac: ./iniciar_sistema.sh", Colors.OKCYAN)
            print_colored("\nOu execute manualmente: python app.py", Colors.OKCYAN)
            print_colored("\nAcesse: http://localhost:5000", Colors.OKGREEN)
        else:
            print_header("INSTALAÇÃO FALHOU!")
            print_colored("Verifique os erros acima e tente novamente.", Colors.FAIL)
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()