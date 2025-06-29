import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import utils as ut
from config import Config
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(**Config.DATABASE_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("Conexão com banco estabelecida")
        except Error as e:
            logger.error(f"Erro ao conectar com o banco: {e}")
            raise
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.lastrowid or self.cursor.rowcount
        except Error as e:
            logger.error(f"Erro ao executar query: {e}")
            self.connection.rollback()
            raise
    
    def create_tables(self):
        """Criar todas as tabelas necessárias"""
        tables = {
            'clientes': '''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    cpf VARCHAR(14) UNIQUE,
                    telefone VARCHAR(20),
                    endereco TEXT,
                    limite_credito DECIMAL(10,2) DEFAULT 500.00,
                    observacoes TEXT,
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',
            'vendas': '''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cliente_id INT NOT NULL,
                    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valor_total DECIMAL(10,2) NOT NULL,
                    valor_pago DECIMAL(10,2) DEFAULT 0.00,
                    valor_restante DECIMAL(10,2) GENERATED ALWAYS AS (valor_total - valor_pago) STORED,
                    status ENUM('aberta', 'paga', 'vencida', 'cancelada') DEFAULT 'aberta',
                    observacoes TEXT,
                    venda_origem_ids TEXT, -- Para rastrear vendas que geraram saldo restante
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''',
            'itens_venda': '''
                CREATE TABLE IF NOT EXISTS itens_venda (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    venda_id INT NOT NULL,
                    descricao VARCHAR(255) NOT NULL,
                    quantidade DECIMAL(8,3) NOT NULL,
                    valor_unitario DECIMAL(10,2) NOT NULL,
                    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (quantidade * valor_unitario) STORED,
                    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE
                )
            ''',
            'pagamentos': '''
                CREATE TABLE IF NOT EXISTS pagamentos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    venda_id INT NOT NULL,
                    valor_pago DECIMAL(10,2) NOT NULL,
                    forma_pagamento ENUM('dinheiro', 'cartao', 'pix') NOT NULL,
                    data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    comprovante_impresso BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (venda_id) REFERENCES vendas(id)
                )
            ''',
            'configuracoes': '''
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave VARCHAR(100) PRIMARY KEY,
                    valor TEXT NOT NULL,
                    descricao VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',
            'logs_sistema': '''
                CREATE TABLE IF NOT EXISTS logs_sistema (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    acao VARCHAR(100) NOT NULL,
                    detalhes TEXT,
                    usuario VARCHAR(100) DEFAULT 'sistema',
                    ip VARCHAR(45),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        for table_name, query in tables.items():
            try:
                self.execute_query(query)
                logger.info(f"Tabela {table_name} criada/verificada")
            except Error as e:
                logger.error(f"Erro ao criar tabela {table_name}: {e}")
    
    def insert_initial_data(self):
        """Inserir dados iniciais do sistema"""
        configs_iniciais = [
            ('limite_inadimplencia_dias', '30', 'Dias para considerar venda vencida'),
            ('limite_credito_default', '500.00', 'Limite de crédito padrão para novos clientes'),
            ('nome_empresa', 'Açougue do João', 'Nome da empresa'),
            ('endereco_empresa', 'Rua das Carnes, 123 - Centro', 'Endereço da empresa'),
            ('telefone_empresa', '(31) 3333-4444', 'Telefone da empresa'),
            ('cnpj_empresa', '12.345.678/0001-90', 'CNPJ da empresa')
        ]
        
        for chave, valor, descricao in configs_iniciais:
            try:
                query = '''INSERT IGNORE INTO configuracoes (chave, valor, descricao) 
                          VALUES (%s, %s, %s)'''
                self.execute_query(query, (chave, valor, descricao))
            except Error as e:
                logger.error(f"Erro ao inserir configuração {chave}: {e}")
    
    # MÉTODOS PARA CLIENTES
    def inserir_cliente(self, dados):
        query = '''INSERT INTO clientes (nome, cpf, telefone, endereco, limite_credito, observacoes)
                   VALUES (%(nome)s, %(cpf)s, %(telefone)s, %(endereco)s, %(limite_credito)s, %(observacoes)s)'''
        return self.execute_query(query, dados)
    
    def atualizar_cliente(self, cliente_id, dados):
        campos = []
        valores = []
        for campo, valor in dados.items():
            if valor is not None:
                campos.append(f"{campo} = %s")
                valores.append(valor)
        
        if not campos:
            return False
        
        valores.append(cliente_id)
        query = f"UPDATE clientes SET {', '.join(campos)} WHERE id = %s"
        return self.execute_query(query, valores)
    
    def buscar_cliente(self, cliente_id):
        query = "SELECT * FROM clientes WHERE id = %s AND ativo = TRUE"
        result = self.execute_query(query, (cliente_id,))
        return result[0] if result else None
    
    def buscar_clientes(self, filtro=None, limite=50):
        if filtro:
            query = '''SELECT c.*, 
                             COALESCE(SUM(v.valor_restante), 0) as saldo_devedor,
                             COUNT(v.id) as total_vendas
                      FROM clientes c
                      LEFT JOIN vendas v ON c.id = v.cliente_id AND v.status IN ('aberta', 'vencida')
                      WHERE c.ativo = TRUE AND (
                          c.nome LIKE %s OR 
                          c.cpf LIKE %s OR 
                          c.telefone LIKE %s
                      )
                      GROUP BY c.id
                      ORDER BY c.nome
                      LIMIT %s'''
            filtro_like = f"%{filtro}%"
            return self.execute_query(query, (filtro_like, filtro_like, filtro_like, limite))
        else:
            query = '''SELECT c.*, 
                             COALESCE(SUM(v.valor_restante), 0) as saldo_devedor,
                             COUNT(v.id) as total_vendas
                      FROM clientes c
                      LEFT JOIN vendas v ON c.id = v.cliente_id AND v.status IN ('aberta', 'vencida')
                      WHERE c.ativo = TRUE
                      GROUP BY c.id
                      ORDER BY c.nome
                      LIMIT %s'''
            return self.execute_query(query, (limite,))
    
    def excluir_cliente(self, cliente_id):
        # Verificar se tem vendas em aberto
        query_check = "SELECT COUNT(*) as count FROM vendas WHERE cliente_id = %s AND status IN ('aberta', 'vencida')"
        result = self.execute_query(query_check, (cliente_id,))
        if result[0]['count'] > 0:
            return False, "Cliente possui vendas em aberto"
        
        # Desativar cliente
        query = "UPDATE clientes SET ativo = FALSE WHERE id = %s"
        self.execute_query(query, (cliente_id,))
        return True, "Cliente excluído com sucesso"
    
    # MÉTODOS PARA VENDAS
    def inserir_venda(self, dados_venda, itens):
        try:
            # Inserir venda
            query_venda = '''INSERT INTO vendas (cliente_id, valor_total, observacoes, venda_origem_ids)
                            VALUES (%(cliente_id)s, %(valor_total)s, %(observacoes)s, %(venda_origem_ids)s)'''
            venda_id = self.execute_query(query_venda, dados_venda)
            
            # Inserir itens
            query_item = '''INSERT INTO itens_venda (venda_id, descricao, quantidade, valor_unitario)
                           VALUES (%s, %s, %s, %s)'''
            for item in itens:
                self.execute_query(query_item, (venda_id, item['descricao'], item['quantidade'], item['valor_unitario']))
            
            return venda_id
        except Error as e:
            logger.error(f"Erro ao inserir venda: {e}")
            raise
    
    def buscar_venda(self, venda_id):
        # Buscar dados da venda
        query_venda = '''SELECT v.*, c.nome as cliente_nome, c.cpf as cliente_cpf
                        FROM vendas v
                        JOIN clientes c ON v.cliente_id = c.id
                        WHERE v.id = %s'''
        venda = self.execute_query(query_venda, (venda_id,))
        if not venda:
            return None
        
        venda = venda[0]
        
        # Buscar itens da venda
        query_itens = "SELECT * FROM itens_venda WHERE venda_id = %s ORDER BY id"
        itens = self.execute_query(query_itens, (venda_id,))
        venda['itens'] = itens
        
        # Buscar pagamentos
        query_pagamentos = "SELECT * FROM pagamentos WHERE venda_id = %s ORDER BY data_pagamento"
        pagamentos = self.execute_query(query_pagamentos, (venda_id,))
        venda['pagamentos'] = pagamentos
        
        return venda
    
    def buscar_vendas(self, filtros=None, limite=50):
        where_clauses = ["1=1"]
        params = []
        
        if filtros:
            if filtros.get('cliente_id'):
                where_clauses.append("v.cliente_id = %s")
                params.append(filtros['cliente_id'])
            
            if filtros.get('status'):
                where_clauses.append("v.status = %s")
                params.append(filtros['status'])
            
            if filtros.get('data_inicio'):
                where_clauses.append("DATE(v.data_venda) >= %s")
                params.append(filtros['data_inicio'])
            
            if filtros.get('data_fim'):
                where_clauses.append("DATE(v.data_venda) <= %s")
                params.append(filtros['data_fim'])
        
        params.append(limite)
        
        query = f'''SELECT v.*, c.nome as cliente_nome, c.telefone as cliente_telefone
                   FROM vendas v
                   JOIN clientes c ON v.cliente_id = c.id
                   WHERE {' AND '.join(where_clauses)}
                   ORDER BY v.data_venda DESC
                   LIMIT %s'''
        
        return self.execute_query(query, params)
    
    def atualizar_status_venda(self, venda_id, novo_status):
        query = "UPDATE vendas SET status = %s WHERE id = %s"
        return self.execute_query(query, (novo_status, venda_id))
    
    # MÉTODOS PARA PAGAMENTOS
    def inserir_pagamento(self, dados_pagamento):
        query = '''INSERT INTO pagamentos (venda_id, valor_pago, forma_pagamento, observacoes)
                   VALUES (%(venda_id)s, %(valor_pago)s, %(forma_pagamento)s, %(observacoes)s)'''
        pagamento_id = self.execute_query(query, dados_pagamento)
        
        # Atualizar valor pago na venda
        query_update = '''UPDATE vendas 
                         SET valor_pago = (
                             SELECT COALESCE(SUM(valor_pago), 0) 
                             FROM pagamentos 
                             WHERE venda_id = %s
                         )
                         WHERE id = %s'''
        self.execute_query(query_update, (dados_pagamento['venda_id'], dados_pagamento['venda_id']))
        
        # Atualizar status se necessário
        self.atualizar_status_venda_apos_pagamento(dados_pagamento['venda_id'])
        
        return pagamento_id
    
    def atualizar_status_venda_apos_pagamento(self, venda_id):
        query = '''UPDATE vendas 
                   SET status = CASE 
                       WHEN valor_restante <= 0 THEN 'paga'
                       WHEN valor_restante > 0 THEN 'aberta'
                   END
                   WHERE id = %s'''
        self.execute_query(query, (venda_id,))
    
    def buscar_vendas_em_aberto_cliente(self, cliente_id):
        query = '''SELECT * FROM vendas 
                   WHERE cliente_id = %s AND status IN ('aberta', 'vencida') 
                   ORDER BY data_venda'''
        return self.execute_query(query, (cliente_id,))
    
    def processar_pagamento_multiplo(self, cliente_id, vendas_ids, valor_total_pago, forma_pagamento):
        """Processa pagamento em múltiplas vendas e cria venda de saldo restante se necessário"""
        vendas = []
        valor_total_devido = 0
        
        # Buscar todas as vendas selecionadas
        for venda_id in vendas_ids:
            venda = self.buscar_venda(venda_id)
            if venda and venda['status'] in ['aberta', 'vencida']:
                vendas.append(venda)
                valor_total_devido += float(venda['valor_restante'])
        
        if not vendas:
            raise Exception("Nenhuma venda válida encontrada")
        
        valor_restante_pagamento = float(valor_total_pago)
        pagamentos_realizados = []
        
        # Processar pagamentos
        for venda in vendas:
            valor_devido_venda = float(venda['valor_restante'])
            
            if valor_restante_pagamento <= 0:
                break
            
            if valor_restante_pagamento >= valor_devido_venda:
                # Pagar a venda completamente
                valor_pago_venda = valor_devido_venda
                valor_restante_pagamento -= valor_devido_venda
            else:
                # Pagamento parcial
                valor_pago_venda = valor_restante_pagamento
                valor_restante_pagamento = 0
            
            # Registrar pagamento
            dados_pagamento = {
                'venda_id': venda['id'],
                'valor_pago': valor_pago_venda,
                'forma_pagamento': forma_pagamento,
                'observacoes': f'Pagamento múltiplo - Vendas: {", ".join([f"#{v}" for v in vendas_ids])}'
            }
            
            pagamento_id = self.inserir_pagamento(dados_pagamento)
            pagamentos_realizados.append(pagamento_id)
        
        # Se sobrou dinheiro, criar nova venda com saldo restante
        venda_saldo_id = None
        if valor_total_devido < valor_total_pago:
            valor_saldo = valor_total_pago - valor_total_devido
            
            # Criar descrição das vendas origem
            vendas_origem_str = ', '.join([f"#{venda['id']}" for venda in vendas])
            data_hoje = datetime.now().strftime('%d/%m/%Y')
            
            dados_venda_saldo = {
                'cliente_id': cliente_id,
                'valor_total': valor_saldo,
                'observacoes': f'Saldo restante do pagamento do dia {data_hoje}',
                'venda_origem_ids': ','.join([str(v['id']) for v in vendas])
            }
            
            itens_saldo = [{
                'descricao': f'Saldo restante das vendas',
                'quantidade': 1,
                'valor_unitario': valor_saldo
            }]
            
            venda_saldo_id = self.inserir_venda(dados_venda_saldo, itens_saldo)
        
        return {
            'pagamentos_realizados': pagamentos_realizados,
            'venda_saldo_id': venda_saldo_id,
            'valor_total_pago': valor_total_pago,
            'valor_total_devido': valor_total_devido
        }

    
    # MÉTODOS PARA ALERTAS
    def buscar_vendas_vencidas(self):
        limite_dias = self.buscar_configuracao('limite_inadimplencia_dias', 30)
        data_limite = datetime.now() - timedelta(days=int(limite_dias))
        
        query = '''SELECT v.*, c.nome as cliente_nome, c.telefone as cliente_telefone
                   FROM vendas v
                   JOIN clientes c ON v.cliente_id = c.id
                   WHERE v.status = 'aberta' AND v.data_venda < %s
                   ORDER BY v.data_venda'''
        
        vendas_vencidas = self.execute_query(query, (data_limite,))
        
        # Atualizar status para vencida
        for venda in vendas_vencidas:
            vendas = ut.convert_decimals_to_float(vendas)
            self.atualizar_status_venda(venda['id'], 'vencida')
        
        return vendas_vencidas
    
    def buscar_clientes_limite_credito(self):
        query = '''SELECT c.*, COALESCE(SUM(v.valor_restante), 0) as saldo_devedor
                   FROM clientes c
                   LEFT JOIN vendas v ON c.id = v.cliente_id AND v.status IN ('aberta', 'vencida')
                   WHERE c.ativo = TRUE
                   GROUP BY c.id
                   HAVING saldo_devedor >= (c.limite_credito * 0.8)
                   ORDER BY saldo_devedor DESC'''
        return self.execute_query(query)
    
    # MÉTODOS PARA CONFIGURAÇÕES
    def buscar_configuracao(self, chave, valor_default=None):
        query = "SELECT valor FROM configuracoes WHERE chave = %s"
        result = self.execute_query(query, (chave,))
        return result[0]['valor'] if result else valor_default
    
    def atualizar_configuracao(self, chave, valor):
        query = '''INSERT INTO configuracoes (chave, valor) VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE valor = %s'''
        return self.execute_query(query, (chave, valor, valor))
    
    # MÉTODOS PARA ESTATÍSTICAS
    def get_estatisticas_dashboard(self):
        stats = {}
        
        # Total de clientes ativos
        query = "SELECT COUNT(*) as total FROM clientes WHERE ativo = TRUE"
        result = self.execute_query(query)
        stats['total_clientes'] = result[0]['total']
        
        # Vendas do mês atual
        query = '''SELECT COUNT(*) as total, COALESCE(SUM(valor_total), 0) as valor_total
                   FROM vendas 
                   WHERE MONTH(data_venda) = MONTH(CURRENT_DATE()) 
                   AND YEAR(data_venda) = YEAR(CURRENT_DATE())'''
        result = self.execute_query(query)
        stats['vendas_mes'] = result[0]
        
        # Vendas em aberto
        query = '''SELECT COUNT(*) as total, COALESCE(SUM(valor_restante), 0) as valor_total
                   FROM vendas WHERE status IN ('aberta', 'vencida')'''
        result = self.execute_query(query)
        stats['vendas_abertas'] = result[0]
        
        # Vendas vencidas
        limite_dias = self.buscar_configuracao('limite_inadimplencia_dias', 30)
        data_limite = datetime.now() - timedelta(days=int(limite_dias))
        query = '''SELECT COUNT(*) as total, COALESCE(SUM(valor_restante), 0) as valor_total
                   FROM vendas 
                   WHERE status = 'vencida' OR (status = 'aberta' AND data_venda < %s)'''
        result = self.execute_query(query, (data_limite,))
        stats['vendas_vencidas'] = result[0]
        
        return stats
    
    def get_dados_graficos(self, periodo_dias=30):
        """Buscar dados para gráficos com tratamento de erro melhorado"""
        try:
            data_inicio = datetime.now() - timedelta(days=periodo_dias)
            
            # Vendas por dia - com tratamento de erro
            try:
                query_vendas = '''SELECT DATE(data_venda) as data, COUNT(*) as quantidade, COALESCE(SUM(valor_total), 0) as valor
                            FROM vendas 
                            WHERE data_venda >= %s
                            GROUP BY DATE(data_venda)
                            ORDER BY data'''
                vendas_por_dia = self.execute_query(query_vendas, (data_inicio,))
                
                # Garantir que temos uma lista
                if not vendas_por_dia:
                    vendas_por_dia = []
                    
            except Exception as e:
                logger.error(f"Erro ao buscar vendas por dia: {e}")
                vendas_por_dia = []
            
            # Formas de pagamento - com tratamento de erro
            try:
                query_pagamentos = '''SELECT p.forma_pagamento, COUNT(*) as quantidade, COALESCE(SUM(p.valor_pago), 0) as valor
                                FROM pagamentos p
                                WHERE p.data_pagamento >= %s
                                GROUP BY p.forma_pagamento'''
                formas_pagamento = self.execute_query(query_pagamentos, (data_inicio,))
                
                # Garantir que temos uma lista
                if not formas_pagamento:
                    formas_pagamento = []
                    
            except Exception as e:
                logger.error(f"Erro ao buscar formas de pagamento: {e}")
                formas_pagamento = []
            
            return {
                'vendas_por_dia': vendas_por_dia,
                'formas_pagamento': formas_pagamento
            }
            
        except Exception as e:
            logger.error(f"Erro geral ao buscar dados dos gráficos: {e}")
            # Retornar estrutura vazia mas válida
            return {
                'vendas_por_dia': [],
                'formas_pagamento': []
            }
    # MÉTODO PARA LOG
    def inserir_log(self, acao, detalhes=None, usuario='sistema', ip=None):
        query = '''INSERT INTO logs_sistema (acao, detalhes, usuario, ip)
                   VALUES (%s, %s, %s, %s)'''
        return self.execute_query(query, (acao, detalhes, usuario, ip))
    
    def __del__(self):
        self.disconnect()