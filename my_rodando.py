#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar se MySQL está funcionando
Execute este arquivo para testar a conexão
"""

import os
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

print("🔍 VERIFICANDO CONFIGURAÇÃO DO MYSQL")
print("=" * 50)

# Verificar variáveis do .env
print("📋 Variáveis do .env:")
print(f"DB_HOST: '{os.getenv('DB_HOST')}'")
print(f"DB_PORT: '{os.getenv('DB_PORT')}' (tipo: {type(os.getenv('DB_PORT'))})")
print(f"DB_USER: '{os.getenv('DB_USER')}'")
print(f"DB_PASSWORD: {'***' if os.getenv('DB_PASSWORD') else 'VAZIO'}")
print(f"DB_NAME: '{os.getenv('DB_NAME')}'")
print()

# Tentar conexão direta com MySQL
try:
    import mysql.connector
    
    print("🔌 Tentando conectar com MySQL...")
    
    # IMPORTANTE: Converter porta para inteiro
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),  # ← CONVERSÃO PARA INT
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    print(f"📡 Tentando conectar em: {config['host']}:{config['port']}")
    
    connection = mysql.connector.connect(**config)
    
    if connection.is_connected():
        print("✅ CONEXÃO MYSQL BEM-SUCEDIDA!")
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"📊 Versão do MySQL: {version[0]}")
        
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"🗄️ Bancos disponíveis: {[db[0] for db in databases]}")
        
        cursor.close()
        connection.close()
        print("✅ Teste concluído com sucesso!")
        
except ImportError:
    print("❌ mysql-connector-python não está instalado!")
    print("💡 Execute: pip install mysql-connector-python")

except mysql.connector.Error as e:
    print(f"❌ Erro MySQL: {e}")
    print()
    print("🔧 POSSÍVEIS SOLUÇÕES:")
    print("1. Verificar se MySQL está rodando:")
    print("   - Abra 'Serviços' do Windows")
    print("   - Procure 'MySQL84' ou similar")
    print("   - Se parado, clique direito → Iniciar")
    print()
    print("2. Verificar credenciais:")
    print("   - Usuário: root")
    print("   - Senha: Julio1975$")
    print("   - Banco: acougue_db")
    print()
    print("3. Verificar se banco existe:")
    print("   - Abra MySQL Command Line")
    print("   - Execute: CREATE DATABASE acougue_db;")

except Exception as e:
    print(f"❌ Erro inesperado: {e}")

print("\n" + "=" * 50)
