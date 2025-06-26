
# Configurações atualizadas pela instalação
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-sistema'
    DEBUG = True
    
    DATABASE_CONFIG = {
        'host': '5000',
        'user': 'root',
        'password': 'Julio1975$',
        'database': 'acougue_db',
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    SISTEMA_CONFIGS = {
        'nome_empresa': 'Casa de Carnes São José',
        'endereco': 'Rua Governador Valadares, Centro',
        'telefone': '(31)3861-1575',
        'cnpj': '24356000101',
        'limite_inadimplencia_dias': 30,
        'limite_credito_default': 500.00,
        'senha_sistema': '1234'
    }
    
    PRINTER_CONFIG = {
        'interface': 'usb',
        'vendor_id': 0x1a2b,
        'product_id': 0x3c4d,
        'timeout': 5000,
        'codepage': 'cp850'
    }
    
    UPLOAD_FOLDER = 'uploads'
    BACKUP_FOLDER = 'backups'
    EXPORT_FOLDER = 'exports'
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

config = {'default': Config}
