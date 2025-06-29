from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
from datetime import datetime, timedelta
import os
import logging
from functools import wraps

# Importar módulos do sistema
from config import Config
from database import Database
from business import ClienteBusiness, VendaBusiness, PagamentoBusiness, RelatoriosBusiness
from utils import validar_cpf, formatar_moeda, exportar_para_csv, exportar_para_excel, Logger
from printer import imprimir_comprovante_venda, testar_impressora, PrinterFallback

# Configurar logging
Logger.setup_logging()
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)

# Verificar se está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ROTAS DE AUTENTICAÇÃO
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == Config.SISTEMA_CONFIGS['senha_sistema']:
            session['authenticated'] = True
            session['login_time'] = datetime.now().isoformat()
            
            # Log do login
            db = Database()
            db.inserir_log('LOGIN', 'Login realizado', 'usuario', request.remote_addr)
            
            return redirect(url_for('dashboard'))
        else:
            flash('Senha incorreta', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ROTA PRINCIPAL - DASHBOARD
# ROTA PRINCIPAL - DASHBOARD (CORRIGIDA)
@app.route('/')
@login_required
def dashboard():
    try:
        # Buscar estatísticas
        stats_result = VendaBusiness.get_estatisticas_dashboard()
        alertas_result = ClienteBusiness.get_alertas_inadimplencia()
        graficos_result = RelatoriosBusiness.get_dados_graficos(30)
        
        # Tratar resultados de forma mais segura
        stats = {}
        alertas = []
        graficos = {}
        
        # Processar estatísticas
        if stats_result and stats_result.get('sucesso'):
            stats = stats_result.get('estatisticas', {})
        else:
            # Valores padrão se não conseguir buscar
            stats = {
                'total_clientes': 0,
                'vendas_mes': {'total': 0, 'valor_total': 0, 'valor_total_formatado': 'R$ 0,00'},
                'vendas_abertas': {'total': 0, 'valor_total': 0, 'valor_total_formatado': 'R$ 0,00'},
                'vendas_vencidas': {'total': 0, 'valor_total': 0, 'valor_total_formatado': 'R$ 0,00'}
            }
        
        # Processar alertas
        if alertas_result and alertas_result.get('sucesso'):
            alertas = alertas_result.get('alertas', [])
        
        # Processar gráficos
        if graficos_result and graficos_result.get('sucesso'):
            graficos = graficos_result.get('graficos', {})
        else:
            # Valores padrão para gráficos
            graficos = {
                'vendas_por_dia': {'labels': [], 'valores': [], 'quantidades': []},
                'formas_pagamento': {'labels': [], 'valores': []}
            }
        
        return render_template('index.html', 
                             stats=stats, 
                             alertas=alertas, 
                             graficos=graficos)
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        
        # Em caso de erro, retornar com dados vazios
        stats = {
            'total_clientes': 0,
            'vendas_mes': {'total': 0, 'valor_total': 0, 'valor_total_formatado': 'R$ 0,00'},
            'vendas_abertas': {'total': 0, 'valor_total': 0, 'valor_total_formatado': 'R$ 0,00'},
            'vendas_vencidas': {'total': 0, 'valor_total': 0, 'valor_total_formatado': 'R$ 0,00'}
        }
        alertas = []
        graficos = {
            'vendas_por_dia': {'labels': [], 'valores': [], 'quantidades': []},
            'formas_pagamento': {'labels': [], 'valores': []}
        }
        
        flash('Erro ao carregar dashboard - usando dados padrão', 'warning')
        return render_template('index.html', 
                             stats=stats, 
                             alertas=alertas, 
                             graficos=graficos)
# ROTAS DE CLIENTES
@app.route('/clientes')
@login_required
def clientes():
    return render_template('clientes.html')

@app.route('/api/clientes', methods=['GET'])
@login_required
def api_listar_clientes():
    try:
        filtro = request.args.get('filtro', '')
        limite = int(request.args.get('limite', 50))
        
        resultado = ClienteBusiness.buscar_clientes(filtro if filtro else None, limite)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/clientes', methods=['POST'])
@login_required
def api_criar_cliente():
    try:
        dados = request.json
        resultado = ClienteBusiness.criar_cliente(dados)
        
        if resultado['sucesso']:
            # Log da operação
            db = Database()
            db.inserir_log('CLIENTE_CRIADO', f"Cliente: {dados.get('nome')}", 'usuario', request.remote_addr)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/clientes/<int:cliente_id>', methods=['GET'])
@login_required
def api_buscar_cliente(cliente_id):
    try:
        resultado = ClienteBusiness.buscar_cliente(cliente_id)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar cliente: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
@login_required
def api_atualizar_cliente(cliente_id):
    try:
        dados = request.json
        resultado = ClienteBusiness.atualizar_cliente(cliente_id, dados)
        
        if resultado['sucesso']:
            # Log da operação
            db = Database()
            db.inserir_log('CLIENTE_ATUALIZADO', f"Cliente ID: {cliente_id}", 'usuario', request.remote_addr)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao atualizar cliente: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required
def api_excluir_cliente(cliente_id):
    try:
        resultado = ClienteBusiness.excluir_cliente(cliente_id)
        
        if resultado['sucesso']:
            # Log da operação
            db = Database()
            db.inserir_log('CLIENTE_EXCLUIDO', f"Cliente ID: {cliente_id}", 'usuario', request.remote_addr)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao excluir cliente: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE VENDAS
@app.route('/vendas')
@login_required
def vendas():
    return render_template('vendas.html')

@app.route('/api/vendas', methods=['GET'])
@login_required
def api_listar_vendas():
    try:
        filtros = {}
        
        if request.args.get('cliente_id'):
            filtros['cliente_id'] = int(request.args.get('cliente_id'))
        
        if request.args.get('status'):
            filtros['status'] = request.args.get('status')
        
        if request.args.get('data_inicio'):
            filtros['data_inicio'] = request.args.get('data_inicio')
        
        if request.args.get('data_fim'):
            filtros['data_fim'] = request.args.get('data_fim')
        
        limite = int(request.args.get('limite', 50))
        
        resultado = VendaBusiness.buscar_vendas(filtros if filtros else None, limite)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao listar vendas: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/vendas', methods=['POST'])
@login_required
def api_criar_venda():
    try:
        dados = request.json
        resultado = VendaBusiness.criar_venda(dados)
        
        if resultado['sucesso']:
            # Log da operação
            db = Database()
            db.inserir_log('VENDA_CRIADA', f"Venda ID: {resultado['venda_id']}, Valor: {formatar_moeda(resultado['valor_total'])}", 'usuario', request.remote_addr)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao criar venda: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/vendas/<int:venda_id>', methods=['GET'])
@login_required
def api_buscar_venda(venda_id):
    try:
        resultado = VendaBusiness.buscar_venda(venda_id)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar venda: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE PAGAMENTOS
@app.route('/pagamentos')
@login_required
def pagamentos():
    return render_template('pagamentos.html')

@app.route('/api/pagamentos/simples', methods=['POST'])
@login_required
def api_pagamento_simples():
    try:
        dados = request.json
        resultado = PagamentoBusiness.processar_pagamento_simples(
            dados['venda_id'],
            dados['valor_pago'],
            dados['forma_pagamento'],
            dados.get('observacoes', '')
        )
        
        if resultado['sucesso']:
            # Log da operação
            db = Database()
            db.inserir_log('PAGAMENTO_PROCESSADO', f"Venda ID: {dados['venda_id']}, Valor: {formatar_moeda(dados['valor_pago'])}", 'usuario', request.remote_addr)
            
            # Se venda foi quitada e tem dados para impressão, tentar imprimir
            if resultado.get('venda_quitada') and resultado.get('dados_impressao'):
                try:
                    sucesso_impressao, msg_impressao = imprimir_comprovante_venda(
                        resultado['dados_impressao']['venda'],
                        resultado['dados_impressao']
                    )
                    resultado['impressao'] = {
                        'sucesso': sucesso_impressao,
                        'mensagem': msg_impressao
                    }
                except Exception as e:
                    logger.error(f"Erro na impressão: {e}")
                    resultado['impressao'] = {
                        'sucesso': False,
                        'mensagem': f'Erro na impressão: {str(e)}'
                    }
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao processar pagamento: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/pagamentos/multiplo', methods=['POST'])
@login_required
def api_pagamento_multiplo():
    try:
        dados = request.json
        resultado = PagamentoBusiness.processar_pagamento_multiplo(
            dados['cliente_id'],
            dados['vendas_ids'],
            dados['valor_pago'],
            dados['forma_pagamento']
        )
        
        if resultado['sucesso']:
            # Log da operação
            db = Database()
            vendas_str = ', '.join([f"#{vid}" for vid in dados['vendas_ids']])
            db.inserir_log('PAGAMENTO_MULTIPLO', f"Cliente ID: {dados['cliente_id']}, Vendas: {vendas_str}, Valor: {formatar_moeda(dados['valor_pago'])}", 'usuario', request.remote_addr)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao processar pagamento múltiplo: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/pagamentos/vendas-em-aberto/<int:cliente_id>')
@login_required
def api_vendas_em_aberto_cliente(cliente_id):
    try:
        resultado = PagamentoBusiness.buscar_vendas_em_aberto_cliente(cliente_id)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar vendas em aberto: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE RELATÓRIOS
@app.route('/relatorios')
@login_required
def relatorios():
    return render_template('relatorios.html')

@app.route('/api/relatorios/vendas/exportar')
@login_required
def api_exportar_vendas():
    try:
        # Parâmetros de filtro
        filtros = {}
        if request.args.get('cliente_id'):
            filtros['cliente_id'] = int(request.args.get('cliente_id'))
        if request.args.get('status'):
            filtros['status'] = request.args.get('status')
        if request.args.get('data_inicio'):
            filtros['data_inicio'] = request.args.get('data_inicio')
        if request.args.get('data_fim'):
            filtros['data_fim'] = request.args.get('data_fim')
        
        formato = request.args.get('formato', 'excel')  # excel ou csv
        
        # Gerar relatório
        resultado = RelatoriosBusiness.gerar_relatorio_vendas(filtros)
        
        if not resultado['sucesso']:
            return jsonify(resultado)
        
        # Gerar arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'csv':
            nome_arquivo = f'relatorio_vendas_{timestamp}.csv'
            sucesso, caminho = exportar_para_csv(resultado['dados'], nome_arquivo)
        else:
            nome_arquivo = f'relatorio_vendas_{timestamp}.xlsx'
            sucesso, caminho = exportar_para_excel(resultado['dados'], nome_arquivo, 'Vendas')
        
        if sucesso:
            # Log da operação
            db = Database()
            db.inserir_log('RELATORIO_EXPORTADO', f"Relatório de vendas: {nome_arquivo}", 'usuario', request.remote_addr)
            
            return send_file(caminho, as_attachment=True, download_name=nome_arquivo)
        else:
            return jsonify({'sucesso': False, 'erro': caminho})
        
    except Exception as e:
        logger.error(f"Erro ao exportar relatório: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/relatorios/inadimplentes/exportar')
@login_required
def api_exportar_inadimplentes():
    try:
        formato = request.args.get('formato', 'excel')
        
        # Gerar relatório
        resultado = RelatoriosBusiness.gerar_relatorio_inadimplentes()
        
        if not resultado['sucesso']:
            return jsonify(resultado)
        
        # Gerar arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'csv':
            nome_arquivo = f'relatorio_inadimplentes_{timestamp}.csv'
            sucesso, caminho = exportar_para_csv(resultado['dados'], nome_arquivo)
        else:
            nome_arquivo = f'relatorio_inadimplentes_{timestamp}.xlsx'
            sucesso, caminho = exportar_para_excel(resultado['dados'], nome_arquivo, 'Inadimplentes')
        
        if sucesso:
            # Log da operação
            db = Database()
            db.inserir_log('RELATORIO_EXPORTADO', f"Relatório de inadimplentes: {nome_arquivo}", 'usuario', request.remote_addr)
            
            return send_file(caminho, as_attachment=True, download_name=nome_arquivo)
        else:
            return jsonify({'sucesso': False, 'erro': caminho})
        
    except Exception as e:
        logger.error(f"Erro ao exportar relatório de inadimplentes: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/graficos/<int:periodo_dias>')
@login_required
def api_dados_graficos(periodo_dias):
    try:
        resultado = RelatoriosBusiness.get_dados_graficos(periodo_dias)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados dos gráficos: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE IMPRESSÃO
@app.route('/api/impressao/teste')
@login_required
def api_teste_impressora():
    try:
        sucesso, mensagem = testar_impressora()
        
        # Log da operação
        db = Database()
        db.inserir_log('TESTE_IMPRESSORA', mensagem, 'usuario', request.remote_addr)
        
        return jsonify({
            'sucesso': sucesso,
            'mensagem': mensagem
        })
        
    except Exception as e:
        logger.error(f"Erro no teste de impressora: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/impressao/comprovante/<int:venda_id>')
@login_required
def api_reimprimir_comprovante(venda_id):
    try:
        # Buscar dados da venda
        resultado_venda = VendaBusiness.buscar_venda(venda_id)
        
        if not resultado_venda['sucesso']:
            return jsonify(resultado_venda)
        
        venda = resultado_venda['venda']
        
        # Tentar imprimir
        sucesso, mensagem = imprimir_comprovante_venda(venda)
        
        if not sucesso:
            # Se falhou, tentar salvar como arquivo
            sucesso_arquivo, caminho_arquivo = PrinterFallback.salvar_comprovante_arquivo(venda)
            if sucesso_arquivo:
                mensagem = f"Impressora não disponível. Comprovante salvo em: {caminho_arquivo}"
                sucesso = True
        
        # Log da operação
        db = Database()
        db.inserir_log('REIMPRESSAO_COMPROVANTE', f"Venda ID: {venda_id}, Sucesso: {sucesso}", 'usuario', request.remote_addr)
        
        return jsonify({
            'sucesso': sucesso,
            'mensagem': mensagem
        })
        
    except Exception as e:
        logger.error(f"Erro ao reimprimir comprovante: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE BUSCA GLOBAL
@app.route('/api/busca')
@login_required
def api_busca_global():
    try:
        termo = request.args.get('q', '').strip()
        
        if not termo or len(termo) < 2:
            return jsonify({'sucesso': False, 'erro': 'Digite pelo menos 2 caracteres'})
        
        resultados = {
            'clientes': [],
            'vendas': []
        }
        
        # Buscar clientes
        resultado_clientes = ClienteBusiness.buscar_clientes(termo, 10)
        if resultado_clientes['sucesso']:
            resultados['clientes'] = resultado_clientes['clientes']
        
        # Buscar vendas (por ID ou nome do cliente)
        filtros = {}
        if termo.isdigit():
            # Se for número, buscar por ID da venda
            try:
                venda_result = VendaBusiness.buscar_venda(int(termo))
                if venda_result['sucesso']:
                    resultados['vendas'] = [venda_result['venda']]
            except:
                pass
        
        return jsonify({
            'sucesso': True,
            'resultados': resultados,
            'total': len(resultados['clientes']) + len(resultados['vendas'])
        })
        
    except Exception as e:
        logger.error(f"Erro na busca global: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE ALERTAS
@app.route('/api/alertas')
@login_required
def api_buscar_alertas():
    try:
        resultado = ClienteBusiness.get_alertas_inadimplencia()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar alertas: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE CONFIGURAÇÃO
@app.route('/api/configuracao', methods=['GET'])
@login_required
def api_buscar_configuracao():
    try:
        db = Database()
        configuracoes = {
            'nome_empresa': db.buscar_configuracao('nome_empresa', 'Açougue do João'),
            'endereco_empresa': db.buscar_configuracao('endereco_empresa', ''),
            'telefone_empresa': db.buscar_configuracao('telefone_empresa', ''),
            'cnpj_empresa': db.buscar_configuracao('cnpj_empresa', ''),
            'limite_inadimplencia_dias': db.buscar_configuracao('limite_inadimplencia_dias', '30'),
            'limite_credito_default': db.buscar_configuracao('limite_credito_default', '500.00')
        }
        
        return jsonify({
            'sucesso': True,
            'configuracoes': configuracoes
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar configurações: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

@app.route('/api/configuracao', methods=['POST'])
@login_required
def api_salvar_configuracao():
    try:
        dados = request.json
        db = Database()
        
        for chave, valor in dados.items():
            db.atualizar_configuracao(chave, valor)
        
        # Log da operação
        db.inserir_log('CONFIGURACAO_ATUALIZADA', f"Configurações atualizadas", 'usuario', request.remote_addr)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Configurações salvas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# ROTAS DE BACKUP
@app.route('/api/backup/criar')
@login_required
def api_criar_backup():
    try:
        from utils import gerar_nome_arquivo_backup, criar_diretorio_se_nao_existe
        import subprocess
        
        # Criar diretório de backup
        criar_diretorio_se_nao_existe('backups')
        
        # Gerar nome do arquivo
        nome_arquivo = gerar_nome_arquivo_backup()
        caminho_backup = os.path.join('backups', nome_arquivo)
        
        # Comando mysqldump
        config_db = Config.DATABASE_CONFIG
        comando = [
            'mysqldump',
            f'--host={config_db["host"]}',
            f'--user={config_db["user"]}',
            f'--password={config_db["password"]}',
            '--single-transaction',
            '--routines',
            '--triggers',
            config_db['database']
        ]
        
        # Executar backup
        with open(caminho_backup, 'w') as arquivo_backup:
            resultado = subprocess.run(comando, stdout=arquivo_backup, stderr=subprocess.PIPE, text=True)
        
        if resultado.returncode == 0:
            # Log da operação
            db = Database()
            db.inserir_log('BACKUP_CRIADO', f"Backup: {nome_arquivo}", 'usuario', request.remote_addr)
            
            return jsonify({
                'sucesso': True,
                'mensagem': f'Backup criado com sucesso: {nome_arquivo}',
                'arquivo': nome_arquivo
            })
        else:
            return jsonify({
                'sucesso': False,
                'erro': f'Erro ao criar backup: {resultado.stderr}'
            })
        
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'})

# MANIPULADORES DE ERRO
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Erro interno: {e}")
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Erro não tratado: {e}")
    return jsonify({'sucesso': False, 'erro': 'Erro interno do sistema'}), 500

# CONTEXTO DE TEMPLATE GLOBAL
@app.context_processor
def inject_globals():
    return {
        'config': Config.SISTEMA_CONFIGS,
        'now': datetime.now(),
        'formatar_moeda': formatar_moeda
    }

# INICIALIZAÇÃO DA APLICAÇÃO
def criar_tabelas_iniciais():
    """Criar tabelas e dados iniciais se necessário"""
    try:
        db = Database()
        db.create_tables()
        db.insert_initial_data()
        logger.info("Tabelas e dados iniciais verificados/criados")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas iniciais: {e}")

if __name__ == '__main__':
    # Criar tabelas iniciais
    criar_tabelas_iniciais()
    
    # Configurar e iniciar aplicação
    debug_mode = Config.DEBUG
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Iniciando aplicação na porta {port}, debug={debug_mode}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )