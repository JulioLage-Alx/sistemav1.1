from database import Database
from utils import validar_cpf, formatar_moeda, calcular_troco
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ClienteBusiness:
    @staticmethod
    def criar_cliente(dados):
        """Criar novo cliente com validações"""
        try:
            # Validações
            erros = []
            
            if not dados.get('nome') or len(dados['nome'].strip()) < 2:
                erros.append('Nome deve ter pelo menos 2 caracteres')
            
            if dados.get('cpf') and not validar_cpf(dados['cpf']):
                erros.append('CPF inválido')
            
            if not dados.get('telefone'):
                erros.append('Telefone é obrigatório')
            
            if erros:
                return {'sucesso': False, 'erros': erros}
            
            # Preparar dados
            dados_cliente = {
                'nome': dados['nome'].strip().title(),
                'cpf': dados.get('cpf', '').replace('.', '').replace('-', '') if dados.get('cpf') else None,
                'telefone': dados['telefone'].strip(),
                'endereco': dados.get('endereco', '').strip(),
                'limite_credito': float(dados.get('limite_credito', 500.00)),
                'observacoes': dados.get('observacoes', '').strip()
            }
            
            db = Database()
            cliente_id = db.inserir_cliente(dados_cliente)
            
            # Log da operação
            db.inserir_log('CLIENTE_CRIADO', f'Cliente {dados_cliente["nome"]} (ID: {cliente_id})')
            
            return {
                'sucesso': True, 
                'cliente_id': cliente_id,
                'mensagem': f'Cliente {dados_cliente["nome"]} cadastrado com sucesso'
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def atualizar_cliente(cliente_id, dados):
        """Atualizar dados do cliente"""
        try:
            db = Database()
            
            # Verificar se cliente existe
            cliente_atual = db.buscar_cliente(cliente_id)
            if not cliente_atual:
                return {'sucesso': False, 'erro': 'Cliente não encontrado'}
            
            # Validações
            erros = []
            dados_atualizacao = {}
            
            if 'nome' in dados:
                if not dados['nome'] or len(dados['nome'].strip()) < 2:
                    erros.append('Nome deve ter pelo menos 2 caracteres')
                else:
                    dados_atualizacao['nome'] = dados['nome'].strip().title()
            
            if 'cpf' in dados and dados['cpf']:
                if not validar_cpf(dados['cpf']):
                    erros.append('CPF inválido')
                else:
                    dados_atualizacao['cpf'] = dados['cpf'].replace('.', '').replace('-', '')
            
            if 'telefone' in dados:
                if not dados['telefone']:
                    erros.append('Telefone é obrigatório')
                else:
                    dados_atualizacao['telefone'] = dados['telefone'].strip()
            
            if 'endereco' in dados:
                dados_atualizacao['endereco'] = dados['endereco'].strip()
            
            if 'limite_credito' in dados:
                try:
                    dados_atualizacao['limite_credito'] = float(dados['limite_credito'])
                except:
                    erros.append('Limite de crédito deve ser um número válido')
            
            if 'observacoes' in dados:
                dados_atualizacao['observacoes'] = dados['observacoes'].strip()
            
            if erros:
                return {'sucesso': False, 'erros': erros}
            
            # Atualizar
            db.atualizar_cliente(cliente_id, dados_atualizacao)
            
            # Log da operação
            db.inserir_log('CLIENTE_ATUALIZADO', f'Cliente ID: {cliente_id}')
            
            return {'sucesso': True, 'mensagem': 'Cliente atualizado com sucesso'}
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def buscar_clientes(filtro=None, limite=50):
        """Buscar clientes com filtro opcional"""
        try:
            db = Database()
            clientes = db.buscar_clientes(filtro, limite)
            
            # Formatar dados para exibição
            for cliente in clientes:
                cliente['cpf_formatado'] = ClienteBusiness.formatar_cpf(cliente.get('cpf'))
                cliente['saldo_devedor_formatado'] = formatar_moeda(cliente.get('saldo_devedor', 0))
                cliente['limite_credito_formatado'] = formatar_moeda(cliente.get('limite_credito', 0))
                
                # Calcular percentual do limite usado
                if cliente.get('limite_credito', 0) > 0:
                    percentual = (cliente.get('saldo_devedor', 0) / cliente['limite_credito']) * 100
                    cliente['percentual_limite_usado'] = min(percentual, 100)
                else:
                    cliente['percentual_limite_usado'] = 0
            
            return {'sucesso': True, 'clientes': clientes}
            
        except Exception as e:
            logger.error(f"Erro ao buscar clientes: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def buscar_cliente(cliente_id):
        """Buscar cliente específico com histórico"""
        try:
            db = Database()
            cliente = db.buscar_cliente(cliente_id)
            
            if not cliente:
                return {'sucesso': False, 'erro': 'Cliente não encontrado'}
            
            # Buscar histórico de vendas
            vendas = db.buscar_vendas({'cliente_id': cliente_id}, limite=100)
            
            # Calcular estatísticas
            total_compras = len(vendas)
            valor_total_compras = sum(venda['valor_total'] for venda in vendas)
            vendas_abertas = [v for v in vendas if v['status'] in ['aberta', 'vencida']]
            valor_em_aberto = sum(venda['valor_restante'] for venda in vendas_abertas)
            
            # Formatações
            cliente['cpf_formatado'] = ClienteBusiness.formatar_cpf(cliente.get('cpf'))
            cliente['limite_credito_formatado'] = formatar_moeda(cliente.get('limite_credito', 0))
            
            return {
                'sucesso': True,
                'cliente': cliente,
                'vendas': vendas,
                'estatisticas': {
                    'total_compras': total_compras,
                    'valor_total_compras': valor_total_compras,
                    'valor_total_compras_formatado': formatar_moeda(valor_total_compras),
                    'valor_em_aberto': valor_em_aberto,
                    'valor_em_aberto_formatado': formatar_moeda(valor_em_aberto),
                    'vendas_abertas': len(vendas_abertas)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def excluir_cliente(cliente_id):
        """Excluir (desativar) cliente"""
        try:
            db = Database()
            sucesso, mensagem = db.excluir_cliente(cliente_id)
            
            if sucesso:
                db.inserir_log('CLIENTE_EXCLUIDO', f'Cliente ID: {cliente_id}')
            
            return {'sucesso': sucesso, 'mensagem': mensagem}
            
        except Exception as e:
            logger.error(f"Erro ao excluir cliente: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def formatar_cpf(cpf):
        """Formatar CPF para exibição"""
        if not cpf or len(cpf) != 11:
            return cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @staticmethod
    def get_alertas_inadimplencia():
        """Buscar alertas de inadimplência"""
        try:
            db = Database()
            vendas_vencidas = db.buscar_vendas_vencidas()
            clientes_limite = db.buscar_clientes_limite_credito()
            
            alertas = []
            
            if vendas_vencidas:
                valor_total = sum(v['valor_restante'] for v in vendas_vencidas)
                alertas.append({
                    'tipo': 'vendas_vencidas',
                    'titulo': f'{len(vendas_vencidas)} venda(s) vencida(s)',
                    'descricao': f'Total em aberto: {formatar_moeda(valor_total)}',
                    'urgencia': 'alta',
                    'dados': vendas_vencidas
                })
            
            if clientes_limite:
                alertas.append({
                    'tipo': 'limite_credito',
                    'titulo': f'{len(clientes_limite)} cliente(s) próximo(s) do limite',
                    'descricao': 'Verificar limite de crédito',
                    'urgencia': 'media',
                    'dados': clientes_limite
                })
            
            return {'sucesso': True, 'alertas': alertas}
            
        except Exception as e:
            logger.error(f"Erro ao buscar alertas: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}

class VendaBusiness:
    @staticmethod
    def criar_venda(dados):
        """Criar nova venda"""
        try:
            # Validações
            erros = []
            
            if not dados.get('cliente_id'):
                erros.append('Cliente é obrigatório')
            
            if not dados.get('itens') or len(dados['itens']) == 0:
                erros.append('Pelo menos um item é obrigatório')
            
            # Validar itens
            itens_validados = []
            valor_total = 0
            
            for i, item in enumerate(dados.get('itens', [])):
                if not item.get('descricao'):
                    erros.append(f'Item {i+1}: Descrição é obrigatória')
                    continue
                
                try:
                    quantidade = float(item['quantidade'])
                    valor_unitario = float(item['valor_unitario'])
                    
                    if quantidade <= 0:
                        erros.append(f'Item {i+1}: Quantidade deve ser maior que zero')
                        continue
                    
                    if valor_unitario <= 0:
                        erros.append(f'Item {i+1}: Valor unitário deve ser maior que zero')
                        continue
                    
                    subtotal = quantidade * valor_unitario
                    valor_total += subtotal
                    
                    itens_validados.append({
                        'descricao': item['descricao'].strip(),
                        'quantidade': quantidade,
                        'valor_unitario': valor_unitario,
                        'subtotal': subtotal
                    })
                    
                except (ValueError, TypeError):
                    erros.append(f'Item {i+1}: Quantidade e valor devem ser números válidos')
            
            if erros:
                return {'sucesso': False, 'erros': erros}
            
            # Verificar limite de crédito do cliente
            db = Database()
            cliente = db.buscar_cliente(dados['cliente_id'])
            if not cliente:
                return {'sucesso': False, 'erro': 'Cliente não encontrado'}
            
            vendas_abertas = db.buscar_vendas_em_aberto_cliente(dados['cliente_id'])
            valor_em_aberto = sum(v['valor_restante'] for v in vendas_abertas)
            
            if (valor_em_aberto + valor_total) > cliente['limite_credito']:
                return {
                    'sucesso': False, 
                    'erro': f'Limite de crédito excedido. Disponível: {formatar_moeda(cliente["limite_credito"] - valor_em_aberto)}'
                }
            
            # Preparar dados da venda
            dados_venda = {
                'cliente_id': dados['cliente_id'],
                'valor_total': valor_total,
                'observacoes': dados.get('observacoes', '').strip(),
                'venda_origem_ids': dados.get('venda_origem_ids', None)
            }
            
            # Inserir venda
            venda_id = db.inserir_venda(dados_venda, itens_validados)
            
            # Log da operação
            db.inserir_log('VENDA_CRIADA', f'Venda ID: {venda_id}, Cliente: {cliente["nome"]}, Valor: {formatar_moeda(valor_total)}')
            
            return {
                'sucesso': True,
                'venda_id': venda_id,
                'valor_total': valor_total,
                'valor_total_formatado': formatar_moeda(valor_total),
                'mensagem': f'Venda criada com sucesso. Total: {formatar_moeda(valor_total)}'
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar venda: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def buscar_vendas(filtros=None, limite=50):
        """Buscar vendas com filtros"""
        try:
            db = Database()
            vendas = db.buscar_vendas(filtros, limite)
            
            # Formatar dados para exibição
            for venda in vendas:
                venda['valor_total_formatado'] = formatar_moeda(venda['valor_total'])
                venda['valor_pago_formatado'] = formatar_moeda(venda['valor_pago'])
                venda['valor_restante_formatado'] = formatar_moeda(venda['valor_restante'])
                venda['data_venda_formatada'] = venda['data_venda'].strftime('%d/%m/%Y %H:%M')
                
                # Status em português
                status_map = {
                    'aberta': 'Em Aberto',
                    'paga': 'Paga',
                    'vencida': 'Vencida',
                    'cancelada': 'Cancelada'
                }
                venda['status_texto'] = status_map.get(venda['status'], venda['status'])
                
                # Calcular dias em aberto (se aplicável)
                if venda['status'] in ['aberta', 'vencida']:
                    dias_aberto = (datetime.now() - venda['data_venda']).days
                    venda['dias_em_aberto'] = dias_aberto
            
            return {'sucesso': True, 'vendas': vendas}
            
        except Exception as e:
            logger.error(f"Erro ao buscar vendas: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def buscar_venda(venda_id):
        """Buscar venda específica com detalhes"""
        try:
            db = Database()
            venda = db.buscar_venda(venda_id)
            
            if not venda:
                return {'sucesso': False, 'erro': 'Venda não encontrada'}
            
            # Formatações
            venda['valor_total_formatado'] = formatar_moeda(venda['valor_total'])
            venda['valor_pago_formatado'] = formatar_moeda(venda['valor_pago'])
            venda['valor_restante_formatado'] = formatar_moeda(venda['valor_restante'])
            venda['data_venda_formatada'] = venda['data_venda'].strftime('%d/%m/%Y %H:%M')
            
            # Formatar itens
            for item in venda['itens']:
                item['valor_unitario_formatado'] = formatar_moeda(item['valor_unitario'])
                item['subtotal_formatado'] = formatar_moeda(item['subtotal'])
                item['quantidade_formatada'] = f"{item['quantidade']:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            # Formatar pagamentos
            for pagamento in venda['pagamentos']:
                pagamento['valor_pago_formatado'] = formatar_moeda(pagamento['valor_pago'])
                pagamento['data_pagamento_formatada'] = pagamento['data_pagamento'].strftime('%d/%m/%Y %H:%M')
                
                # Forma de pagamento em português
                forma_map = {
                    'dinheiro': 'Dinheiro',
                    'cartao': 'Cartão',
                    'pix': 'PIX'
                }
                pagamento['forma_pagamento_texto'] = forma_map.get(pagamento['forma_pagamento'], pagamento['forma_pagamento'])
            
            # Se é venda de saldo restante, buscar vendas origem
            if venda.get('venda_origem_ids'):
                vendas_origem_ids = venda['venda_origem_ids'].split(',')
                vendas_origem = []
                for origem_id in vendas_origem_ids:
                    if origem_id.strip():
                        venda_origem = db.buscar_venda(int(origem_id.strip()))
                        if venda_origem:
                            venda_origem['valor_total_formatado'] = formatar_moeda(venda_origem['valor_total'])
                            venda_origem['data_venda_formatada'] = venda_origem['data_venda'].strftime('%d/%m/%Y')
                            vendas_origem.append(venda_origem)
                venda['vendas_origem'] = vendas_origem
            
            return {'sucesso': True, 'venda': venda}
            
        except Exception as e:
            logger.error(f"Erro ao buscar venda: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def get_estatisticas_dashboard():
        """Buscar estatísticas para o dashboard"""
        try:
            db = Database()
            stats = db.get_estatisticas_dashboard()
            
            # Formatar valores
            stats['vendas_mes']['valor_total_formatado'] = formatar_moeda(stats['vendas_mes']['valor_total'])
            stats['vendas_abertas']['valor_total_formatado'] = formatar_moeda(stats['vendas_abertas']['valor_total'])
            stats['vendas_vencidas']['valor_total_formatado'] = formatar_moeda(stats['vendas_vencidas']['valor_total'])
            
            return {'sucesso': True, 'estatisticas': stats}
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}

class PagamentoBusiness:
    @staticmethod
    def processar_pagamento_simples(venda_id, valor_pago, forma_pagamento, observacoes=''):
        """Processar pagamento em uma única venda"""
        try:
            db = Database()
            
            # Verificar se venda existe e está em aberto
            venda = db.buscar_venda(venda_id)
            if not venda:
                return {'sucesso': False, 'erro': 'Venda não encontrada'}
            
            if venda['status'] not in ['aberta', 'vencida']:
                return {'sucesso': False, 'erro': 'Venda não está em aberto'}
            
            # Validações
            try:
                valor_pago = float(valor_pago)
            except:
                return {'sucesso': False, 'erro': 'Valor deve ser um número válido'}
            
            if valor_pago <= 0:
                return {'sucesso': False, 'erro': 'Valor deve ser maior que zero'}
            
            if valor_pago > venda['valor_restante']:
                return {'sucesso': False, 'erro': f'Valor maior que o restante da venda ({formatar_moeda(venda["valor_restante"])})'}
            
            if forma_pagamento not in ['dinheiro', 'cartao', 'pix']:
                return {'sucesso': False, 'erro': 'Forma de pagamento inválida'}
            
            # Processar pagamento
            dados_pagamento = {
                'venda_id': venda_id,
                'valor_pago': valor_pago,
                'forma_pagamento': forma_pagamento,
                'observacoes': observacoes.strip()
            }
            
            pagamento_id = db.inserir_pagamento(dados_pagamento)
            
            # Buscar venda atualizada
            venda_atualizada = db.buscar_venda(venda_id)
            
            # Calcular troco se pagamento em dinheiro
            troco = 0
            if forma_pagamento == 'dinheiro' and venda_atualizada['status'] == 'paga':
                troco = calcular_troco(valor_pago, venda['valor_restante'])
            
            # Log da operação
            db.inserir_log('PAGAMENTO_PROCESSADO', f'Venda ID: {venda_id}, Valor: {formatar_moeda(valor_pago)}, Forma: {forma_pagamento}')
            
            resultado = {
                'sucesso': True,
                'pagamento_id': pagamento_id,
                'venda_quitada': venda_atualizada['status'] == 'paga',
                'valor_restante': venda_atualizada['valor_restante'],
                'valor_restante_formatado': formatar_moeda(venda_atualizada['valor_restante']),
                'troco': troco,
                'troco_formatado': formatar_moeda(troco),
                'mensagem': f'Pagamento de {formatar_moeda(valor_pago)} processado com sucesso'
            }
            
            # Se venda foi quitada, incluir dados para impressão
            if venda_atualizada['status'] == 'paga':
                resultado['dados_impressao'] = PagamentoBusiness.preparar_dados_impressao(venda_atualizada, valor_pago, forma_pagamento, troco)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def processar_pagamento_multiplo(cliente_id, vendas_ids, valor_pago, forma_pagamento):
        """Processar pagamento em múltiplas vendas"""
        try:
            if not vendas_ids or len(vendas_ids) == 0:
                return {'sucesso': False, 'erro': 'Selecione pelo menos uma venda'}
            
            try:
                valor_pago = float(valor_pago)
            except:
                return {'sucesso': False, 'erro': 'Valor deve ser um número válido'}
            
            if valor_pago <= 0:
                return {'sucesso': False, 'erro': 'Valor deve ser maior que zero'}
            
            if forma_pagamento not in ['dinheiro', 'cartao', 'pix']:
                return {'sucesso': False, 'erro': 'Forma de pagamento inválida'}
            
            db = Database()
            
            # Processar pagamento múltiplo
            resultado_pagamento = db.processar_pagamento_multiplo(cliente_id, vendas_ids, valor_pago, forma_pagamento)
            
            # Log da operação
            vendas_str = ', '.join([f"#{vid}" for vid in vendas_ids])
            db.inserir_log('PAGAMENTO_MULTIPLO', f'Cliente ID: {cliente_id}, Vendas: {vendas_str}, Valor: {formatar_moeda(valor_pago)}')
            
            resultado = {
                'sucesso': True,
                'pagamentos_realizados': resultado_pagamento['pagamentos_realizados'],
                'venda_saldo_id': resultado_pagamento['venda_saldo_id'],
                'valor_total_pago': resultado_pagamento['valor_total_pago'],
                'valor_total_devido': resultado_pagamento['valor_total_devido'],
                'sobrou_saldo': resultado_pagamento['venda_saldo_id'] is not None,
                'mensagem': f'Pagamento múltiplo de {formatar_moeda(valor_pago)} processado com sucesso'
            }
            
            if resultado['sobrou_saldo']:
                valor_saldo = resultado['valor_total_pago'] - resultado['valor_total_devido']
                resultado['valor_saldo'] = valor_saldo
                resultado['valor_saldo_formatado'] = formatar_moeda(valor_saldo)
                resultado['mensagem'] += f'. Nova venda criada com saldo de {formatar_moeda(valor_saldo)}'
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento múltiplo: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def buscar_vendas_em_aberto_cliente(cliente_id):
        """Buscar vendas em aberto de um cliente para pagamento múltiplo"""
        try:
            db = Database()
            vendas = db.buscar_vendas_em_aberto_cliente(cliente_id)
            
            # Formatar dados
            for venda in vendas:
                venda['valor_total_formatado'] = formatar_moeda(venda['valor_total'])
                venda['valor_restante_formatado'] = formatar_moeda(venda['valor_restante'])
                venda['data_venda_formatada'] = venda['data_venda'].strftime('%d/%m/%Y')
                
                # Calcular dias em aberto
                dias_aberto = (datetime.now() - venda['data_venda']).days
                venda['dias_em_aberto'] = dias_aberto
            
            # Calcular totais
            valor_total_devido = sum(v['valor_restante'] for v in vendas)
            
            return {
                'sucesso': True,
                'vendas': vendas,
                'valor_total_devido': valor_total_devido,
                'valor_total_devido_formatado': formatar_moeda(valor_total_devido),
                'quantidade_vendas': len(vendas)
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar vendas em aberto: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def preparar_dados_impressao(venda, valor_pago, forma_pagamento, troco):
        """Preparar dados para impressão do comprovante"""
        try:
            db = Database()
            configs = {
                'nome_empresa': db.buscar_configuracao('nome_empresa', 'Açougue do João'),
                'endereco_empresa': db.buscar_configuracao('endereco_empresa', ''),
                'telefone_empresa': db.buscar_configuracao('telefone_empresa', ''),
                'cnpj_empresa': db.buscar_configuracao('cnpj_empresa', '')
            }
            
            dados_impressao = {
                'empresa': configs,
                'venda': venda,
                'valor_pago': valor_pago,
                'valor_pago_formatado': formatar_moeda(valor_pago),
                'forma_pagamento': forma_pagamento,
                'troco': troco,
                'troco_formatado': formatar_moeda(troco),
                'data_pagamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            return dados_impressao
            
        except Exception as e:
            logger.error(f"Erro ao preparar dados de impressão: {e}")
            return None

class RelatoriosBusiness:
    @staticmethod
    def get_dados_graficos(periodo_dias=30):
        """Buscar dados para gráficos do dashboard"""
        try:
            db = Database()
            dados = db.get_dados_graficos(periodo_dias)
            
            # Formatar dados para Chart.js
            
            # Vendas por dia
            vendas_por_dia = dados['vendas_por_dia']
            labels_vendas = [v['data'].strftime('%d/%m') for v in vendas_por_dia]
            valores_vendas = [float(v['valor']) for v in vendas_por_dia]
            quantidades_vendas = [v['quantidade'] for v in vendas_por_dia]
            
            # Formas de pagamento
            formas_pagamento = dados['formas_pagamento']
            labels_formas = [f['forma_pagamento'].title() for f in formas_pagamento]
            valores_formas = [float(f['valor']) for f in formas_pagamento]
            
            return {
                'sucesso': True,
                'graficos': {
                    'vendas_por_dia': {
                        'labels': labels_vendas,
                        'valores': valores_vendas,
                        'quantidades': quantidades_vendas
                    },
                    'formas_pagamento': {
                        'labels': labels_formas,
                        'valores': valores_formas
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados dos gráficos: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def gerar_relatorio_vendas(filtros):
        """Gerar relatório de vendas para exportação"""
        try:
            db = Database()
            vendas = db.buscar_vendas(filtros, limite=10000)  # Buscar todas
            
            # Preparar dados para exportação
            dados_exportacao = []
            for venda in vendas:
                dados_exportacao.append({
                    'ID': venda['id'],
                    'Data': venda['data_venda'].strftime('%d/%m/%Y %H:%M'),
                    'Cliente': venda['cliente_nome'],
                    'Telefone': venda['cliente_telefone'],
                    'Valor Total': venda['valor_total'],
                    'Valor Pago': venda['valor_pago'],
                    'Valor Restante': venda['valor_restante'],
                    'Status': venda['status'].title(),
                    'Observações': venda.get('observacoes', '')
                })
            
            return {
                'sucesso': True,
                'dados': dados_exportacao,
                'total_registros': len(dados_exportacao),
                'valor_total': sum(v['valor_total'] for v in vendas),
                'valor_pago': sum(v['valor_pago'] for v in vendas),
                'valor_restante': sum(v['valor_restante'] for v in vendas)
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de vendas: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}
    
    @staticmethod
    def gerar_relatorio_inadimplentes():
        """Gerar relatório de clientes inadimplentes"""
        try:
            db = Database()
            vendas_vencidas = db.buscar_vendas_vencidas()
            
            # Agrupar por cliente
            clientes_inadimplentes = {}
            for venda in vendas_vencidas:
                cliente_id = venda['cliente_id']
                if cliente_id not in clientes_inadimplentes:
                    clientes_inadimplentes[cliente_id] = {
                        'cliente_nome': venda['cliente_nome'],
                        'cliente_telefone': venda['cliente_telefone'],
                        'vendas': [],
                        'valor_total': 0,
                        'dias_max_vencimento': 0
                    }
                
                dias_vencimento = (datetime.now() - venda['data_venda']).days
                clientes_inadimplentes[cliente_id]['vendas'].append({
                    'id': venda['id'],
                    'data_venda': venda['data_venda'].strftime('%d/%m/%Y'),
                    'valor_restante': venda['valor_restante'],
                    'dias_vencimento': dias_vencimento
                })
                clientes_inadimplentes[cliente_id]['valor_total'] += venda['valor_restante']
                clientes_inadimplentes[cliente_id]['dias_max_vencimento'] = max(
                    clientes_inadimplentes[cliente_id]['dias_max_vencimento'],
                    dias_vencimento
                )
            
            # Preparar dados para exportação
            dados_exportacao = []
            for cliente_data in clientes_inadimplentes.values():
                dados_exportacao.append({
                    'Cliente': cliente_data['cliente_nome'],
                    'Telefone': cliente_data['cliente_telefone'],
                    'Quantidade Vendas': len(cliente_data['vendas']),
                    'Valor Total Devido': cliente_data['valor_total'],
                    'Dias Máx. Vencimento': cliente_data['dias_max_vencimento']
                })
            
            # Ordenar por valor devido (maior primeiro)
            dados_exportacao.sort(key=lambda x: x['Valor Total Devido'], reverse=True)
            
            return {
                'sucesso': True,
                'dados': dados_exportacao,
                'clientes_detalhados': list(clientes_inadimplentes.values()),
                'total_clientes': len(clientes_inadimplentes),
                'valor_total_devido': sum(c['valor_total'] for c in clientes_inadimplentes.values())
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de inadimplentes: {e}")
            return {'sucesso': False, 'erro': 'Erro interno do sistema'}