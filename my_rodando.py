#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar e diagnosticar a conexão com MySQL
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

def teste_conexao_mysql():
    """Testar conexão com MySQL com diferentes configurações"""
    
    print("=" * 60)
    print("TESTE DE CONEXÃO MYSQL - SISTEMA DE CREDIÁRIO")
    print("=" * 60)
    
    # Configurações para testar
    configuracoes_teste = [
        {
            'nome': 'Configuração Original (INCORRETA)',
            'config': {
                'host': '5000',  # Esta estava incorreta
                'user': 'root',
                'password': 'Julio1975$',
                'database': 'acougue_db'
            }
        },
        {
            'nome': 'Configuração Corrigida - localhost',
            'config': {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': 'Julio1975$',
                'database': 'acougue_db'
            }
        },
        {
            'nome': 'Configuração Corrigida - 127.0.0.1',
            'config': {
                'host': '127.0.0.1',
                'port': 3306,
                'user': 'root',
                'password': 'Julio1975$',
                'database': 'acougue_db'
            }
        },
        {
            'nome': 'Teste sem banco específico (para criar)',
            'config': {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': 'Julio1975'
            }
        }
    ]
    
    for i, teste in enumerate(configuracoes_teste, 1):
        print(f"\n[{i}] Testando: {teste['nome']}")
        print("-" * 50)
        
        try:
            connection = mysql.connector.connect(**teste['config'])
            
            if connection.is_connected():
                info_servidor = connection.get_server_info()
                print(f"✅ SUCESSO! Conectado ao MySQL Server {info_servidor}")
                
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE();")
                database_name = cursor.fetchone()
                print(f"   Banco atual: {database_name[0] if database_name[0] else 'Nenhum'}")
                
                # Se conectou sem banco, tentar criar o banco
                if 'database' not in teste['config']:
                    try:
                        cursor.execute("CREATE DATABASE IF NOT EXISTS acougue_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        print("   ✅ Banco 'acougue_db' criado/verificado com sucesso")
                        
                        cursor.execute("SHOW DATABASES LIKE 'acougue_db'")
                        if cursor.fetchone():
                            print("   ✅ Banco 'acougue_db' confirmado existente")
                    except Error as e:
                        print(f"   ❌ Erro ao criar banco: {e}")
                
                # Listar bancos disponíveis
                cursor.execute("SHOW DATABASES")
                bancos = cursor.fetchall()
                print(f"   Bancos disponíveis: {[banco[0] for banco in bancos]}")
                
                cursor.close()
                connection.close()
                print("   Conexão fechada com sucesso")
                
        except Error as e:
            print(f"❌ ERRO: {e}")
            
            # Diagnóstico específico do erro
            if "Can't connect to MySQL server" in str(e):
                print("   💡 Possíveis causas:")
                print("      - MySQL não está rodando")
                print("      - Host/porta incorretos")
                print("      - Firewall bloqueando conexão")
            elif "Access denied" in str(e):
                print("   💡 Possíveis causas:")
                print("      - Usuário ou senha incorretos")
                print("      - Usuário não tem permissão")
            elif "Unknown database" in str(e):
                print("   💡 Causa: Banco de dados não existe")
        
        except Exception as e:
            print(f"❌ ERRO INESPERADO: {e}")

def verificar_mysql_rodando():
    """Verificar se MySQL está rodando"""
    print("\n" + "=" * 60)
    print("VERIFICANDO STATUS DO MYSQL")
    print("=" * 60)
    
    import subprocess
    import platform
    
    sistema = platform.system().lower()
    
    if sistema == "windows":
        try:
            # Verificar serviço MySQL no Windows
            result = subprocess.run(
                ['sc', 'query', 'MySQL80'], 
                capture_output=True, 
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                if "RUNNING" in result.stdout:
                    print("✅ Serviço MySQL80 está RODANDO")
                else:
                    print("❌ Serviço MySQL80 está PARADO")
                    print("   💡 Para iniciar: net start MySQL80")
            else:
                # Tentar outros nomes comuns
                services = ['MySQL', 'MySQL57', 'MySQL56', 'MariaDB']
                found = False
                
                for service in services:
                    result = subprocess.run(
                        ['sc', 'query', service], 
                        capture_output=True, 
                        text=True,
                        shell=True
                    )
                    if result.returncode == 0:
                        print(f"✅ Encontrado serviço: {service}")
                        if "RUNNING" in result.stdout:
                            print(f"   Status: RODANDO")
                        else:
                            print(f"   Status: PARADO")
                            print(f"   💡 Para iniciar: net start {service}")
                        found = True
                        break
                
                if not found:
                    print("❌ Nenhum serviço MySQL encontrado")
                    print("   💡 Verifique se o MySQL está instalado")
        
        except Exception as e:
            print(f"❌ Erro ao verificar serviços: {e}")
    
    else:
        print("ℹ️  Verificação automática disponível apenas no Windows")
        print("   No Linux/Mac, use: sudo systemctl status mysql")

def mostrar_solucoes():
    """Mostrar soluções para problemas comuns"""
    print("\n" + "=" * 60)
    print("SOLUÇÕES PARA PROBLEMAS COMUNS")
    print("=" * 60)
    
    solucoes = [
        {
            'problema': 'MySQL não está rodando',
            'solucoes': [
                'Windows: Abrir Serviços (services.msc) e iniciar MySQL',
                'Windows (cmd): net start MySQL80',
                'Linux: sudo systemctl start mysql',
                'Mac: brew services start mysql'
            ]
        },
        {
            'problema': 'Erro de conexão (host incorreto)',
            'solucoes': [
                'Usar "localhost" em vez de "5000"',
                'Verificar se a porta é 3306 (padrão)',
                'Tentar 127.0.0.1 se localhost não funcionar'
            ]
        },
        {
            'problema': 'Access denied (senha incorreta)',
            'solucoes': [
                'Verificar senha do usuário root',
                'Resetar senha do MySQL se necessário',
                'Criar novo usuário se precisar'
            ]
        },
        {
            'problema': 'Banco não existe',
            'solucoes': [
                'O script criará automaticamente',
                'Ou criar manualmente: CREATE DATABASE acougue_db;'
            ]
        }
    ]
    
    for i, item in enumerate(solucoes, 1):
        print(f"\n{i}. {item['problema']}:")
        for solucao in item['solucoes']:
            print(f"   • {solucao}")

def main():
    """Função principal"""
    print("🔧 DIAGNÓSTICO DE CONEXÃO MYSQL")
    print("Este script vai testar diferentes configurações de conexão\n")
    
    # Verificar se MySQL está rodando
    verificar_mysql_rodando()
    
    # Testar conexões
    teste_conexao_mysql()
    
    # Mostrar soluções
    mostrar_solucoes()
    
    print("\n" + "=" * 60)
    print("PRÓXIMOS PASSOS:")
    print("=" * 60)
    print("1. Se algum teste passou, use essa configuração no config.py")
    print("2. Se nenhum teste passou, verifique se MySQL está instalado e rodando")
    print("3. Corrija o arquivo config.py com a configuração que funcionou")
    print("4. Execute o sistema novamente")
    
    input("\nPressione Enter para finalizar...")

if __name__ == "__main__":
    main()