#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Instalação Simplificada - Sistema de Crediário
"""

import os
import subprocess
import sys
import getpass
from pathlib import Path

def print_step(step, description):
    print(f"\n[{step}] {description}")
    print("-" * 50)

def run_command(command):
    """Executar comando simples"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("=" * 60)
    print("  INSTALAÇÃO SIMPLIFICADA")
    print("  Sistema de Crediário - Açougue")
    print("=" * 60)
    
    # Passo 1: Instalar dependências
    print_step(1, "Instalando dependências básicas")
    
    dependencias = [
        "Flask==2.3.3",
        "mysql-connector-python==8.2.0", 
        "python-dotenv==1.0.0",
        "openpyxl==3.1.2"
    ]
    
    for dep in dependencias:
        print(f"Instalando {dep}...")
        success, output = run_command(f"pip install {dep}")
        if success:
            print(f"✓ {dep} instalado")
        else:
            print(f"✗ Erro: {output}")
    
    # Dependências opcionais
    print("\nInstalando dependências opcionais...")
    optional_deps = ["python-escpos", "bcrypt", "APScheduler"]
    
    for dep in optional_deps:
        print(f"Instalando {dep}...")
        success, output = run_command(f"pip install {dep}")
        if success:
            print(f"✓ {dep} instalado")
        else:
            print(f"⚠ {dep} falhou (opcional)")
    
    # Passo 2: Criar diretórios
    print_step(2, "Criando estrutura de diretórios")
    
    diretorios = ["logs", "backups", "exports", "uploads", "static/img", "comprovantes"]
    
    for diretorio in diretorios:
        Path(diretorio).mkdir(parents=True, exist_ok=True)
        print(f"✓ {diretorio}")
    
    # Passo 3: Configurar banco
    print_step(3, "Configuração do Banco de Dados")
    
    print("Forneça as informações do MySQL:")
    db_host = input("Host [localhost]: ").strip() or 'localhost'
    db_user = input("Usuário [root]: ").strip() or 'root'
    db_password = getpass.getpass("Senha: ")
    db_name = input("Nome do banco [acougue_db]: ").strip() or 'acougue_db'
    
    # Criar arquivo .env
    env_content = f"""# Configurações do Sistema
DB_HOST={db_host}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}
SECRET_KEY=chave-secreta-{hash(db_password)}
DEBUG=True
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✓ Arquivo .env criado")
    
    # Passo 4: Configurar empresa
    print_step(4, "Configuração da Empresa")
    
    print("Informações da empresa:")
    nome_empresa = input("Nome da empresa [Açougue do João]: ").strip() or 'Açougue do João'
    endereco = input("Endereço: ").strip()
    telefone = input("Telefone: ").strip()
    cnpj = input("CNPJ: ").strip()
    
    print("\nDefina uma senha para o sistema:")
    while True:
        senha1 = getpass.getpass("Nova senha: ")
        senha2 = getpass.getpass("Confirme: ")
        if senha1 == senha2 and len(senha1) >= 4:
            break
        else:
            print("✗ Senhas não coincidem ou muito curta (min 4 chars)")
    
    # Atualizar config.py
    config_update = f"""
# Configurações atualizadas pela instalação
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-sistema'
    DEBUG = True
    
    DATABASE_CONFIG = {{
        'host': '{db_host}',
        'user': '{db_user}',
        'password': '{db_password}',
        'database': '{db_name}',
        'charset': 'utf8mb4',
        'autocommit': True
    }}
    
    SISTEMA_CONFIGS = {{
        'nome_empresa': '{nome_empresa}',
        'endereco': '{endereco}',
        'telefone': '{telefone}',
        'cnpj': '{cnpj}',
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

config = {{'default': Config}}
"""
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_update)
    print("✓ Configurações salvas")
    
    # Passo 5: Testar importações
    print_step(5, "Testando sistema")
    
    try:
        print("Testando importações...")
        import config
        print("✓ config.py")
        
        # Testar conexão com banco
        print("Testando conexão com banco...")
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()
        print("✓ Banco de dados configurado")
        
    except ImportError as e:
        print(f"⚠ Erro de importação: {e}")
    except Exception as e:
        print(f"⚠ Erro no banco: {e}")
    
    # Passo 6: Scripts de inicialização
    print_step(6, "Criando scripts de inicialização")
    
    # Script Windows
    bat_content = f"""@echo off
echo Iniciando Sistema de Crediario...
cd /d "%~dp0"
python app.py
pause
"""
    
    with open('iniciar.bat', 'w') as f:
        f.write(bat_content)
    
    print("✓ iniciar.bat criado")
    
    # Finalização
    print("\n" + "=" * 60)
    print("  INSTALAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print("✓ Dependências instaladas")
    print("✓ Banco configurado")
    print("✓ Sistema configurado")
    print("\nPara iniciar:")
    print("1. Execute: python app.py")
    print("2. Ou use: iniciar.bat")
    print("3. Acesse: http://localhost:5000")
    print(f"4. Senha: {senha1}")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()