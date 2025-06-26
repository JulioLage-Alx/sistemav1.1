try:
    from escpos.printer import Usb, Network, Serial
    from escpos.exceptions import USBNotFoundError, Error as EscposError
except ImportError:
    print("Biblioteca python-escpos não encontrada. Instale com: pip install python-escpos")
    Usb = Network = Serial = None
    USBNotFoundError = EscposError = Exception

from datetime import datetime
from config import Config
from utils import formatar_moeda, formatar_data_hora_brasileira
import logging,os

logger = logging.getLogger(__name__)

class PrinterManager:
    """Gerenciador de impressora ESC/POS"""
    
    def __init__(self):
        self.printer = None
        self.connected = False
        self.config = Config.PRINTER_CONFIG
    
    def conectar(self):
        """Conectar com a impressora"""
        try:
            if self.config['interface'] == 'usb':
                self.printer = Usb(
                    idVendor=self.config['vendor_id'],
                    idProduct=self.config['product_id'],
                    timeout=self.config['timeout']
                )
            elif self.config['interface'] == 'network':
                self.printer = Network(
                    host=self.config.get('host', '192.168.1.100'),
                    port=self.config.get('port', 9100)
                )
            elif self.config['interface'] == 'serial':
                self.printer = Serial(
                    devfile=self.config.get('device', '/dev/ttyUSB0'),
                    baudrate=self.config.get('baudrate', 9600)
                )
            else:
                raise Exception("Interface de impressora não configurada")
            
            # Testar conexão
            if self.printer:
                self.printer.open()
                self.connected = True
                logger.info("Impressora conectada com sucesso")
                return True
            
        except USBNotFoundError:
            logger.error("Impressora USB não encontrada")
            self.connected = False
            return False
        except EscposError as e:
            logger.error(f"Erro ESC/POS: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Erro ao conectar impressora: {e}")
            self.connected = False
            return False
        
        return False
    
    def desconectar(self):
        """Desconectar da impressora"""
        try:
            if self.printer and self.connected:
                self.printer.close()
                self.connected = False
                logger.info("Impressora desconectada")
        except Exception as e:
            logger.error(f"Erro ao desconectar impressora: {e}")
    
    def testar_impressora(self):
        """Testar impressora com página de teste"""
        try:
            if not self.conectar():
                return False, "Não foi possível conectar com a impressora"
            
            # Imprimir página de teste
            self.printer.set(align='center', text_type='B', width=2, height=2)
            self.printer.text("TESTE DE IMPRESSORA\n")
            
            self.printer.set(align='left', text_type='normal', width=1, height=1)
            self.printer.text(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            self.printer.text("Impressora funcionando corretamente!\n")
            self.printer.text("-" * 32 + "\n")
            
            # Cortar papel
            self.printer.cut()
            
            self.desconectar()
            return True, "Teste de impressora realizado com sucesso"
            
        except Exception as e:
            logger.error(f"Erro no teste de impressora: {e}")
            self.desconectar()
            return False, f"Erro no teste: {str(e)}"
    
    def imprimir_comprovante(self, dados_venda, dados_pagamento=None):
        """Imprimir comprovante de venda"""
        try:
            if not self.conectar():
                return False, "Não foi possível conectar com a impressora"
            
            # Cabeçalho da empresa
            self._imprimir_cabecalho()
            
            # Dados da venda
            self._imprimir_dados_venda(dados_venda)
            
            # Itens da venda
            self._imprimir_itens(dados_venda.get('itens', []))
            
            # Totais
            self._imprimir_totais(dados_venda)
            
            # Dados do pagamento (se fornecido)
            if dados_pagamento:
                self._imprimir_dados_pagamento(dados_pagamento)
            
            # Rodapé
            self._imprimir_rodape()
            
            # Cortar papel
            self.printer.cut()
            
            self.desconectar()
            
            # Marcar comprovante como impresso no banco
            self._marcar_comprovante_impresso(dados_venda.get('id'))
            
            return True, "Comprovante impresso com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao imprimir comprovante: {e}")
            self.desconectar()
            return False, f"Erro na impressão: {str(e)}"
    
    def _imprimir_cabecalho(self):
        """Imprimir cabeçalho do comprovante"""
        empresa_config = Config.SISTEMA_CONFIGS
        
        # Nome da empresa (centralizado, negrito, tamanho maior)
        self.printer.set(align='center', text_type='B', width=2, height=2)
        self.printer.text(f"{empresa_config['nome_empresa']}\n")
        
        # Dados da empresa (centralizados, tamanho normal)
        self.printer.set(align='center', text_type='normal', width=1, height=1)
        if empresa_config.get('endereco'):
            self.printer.text(f"{empresa_config['endereco']}\n")
        if empresa_config.get('telefone'):
            self.printer.text(f"Tel: {empresa_config['telefone']}\n")
        if empresa_config.get('cnpj'):
            self.printer.text(f"CNPJ: {empresa_config['cnpj']}\n")
        
        # Linha separadora
        self.printer.text("-" * 32 + "\n")
        
        # Título do comprovante
        self.printer.set(align='center', text_type='B', width=1, height=1)
        self.printer.text("COMPROVANTE DE VENDA\n")
        self.printer.text("-" * 32 + "\n")
    
    def _imprimir_dados_venda(self, dados_venda):
        """Imprimir dados básicos da venda"""
        self.printer.set(align='left', text_type='normal', width=1, height=1)
        
        # Número da venda
        self.printer.text(f"Venda #: {dados_venda.get('id', 'N/A')}\n")
        
        # Data da venda
        if dados_venda.get('data_venda'):
            data_formatada = formatar_data_hora_brasileira(dados_venda['data_venda'])
            self.printer.text(f"Data: {data_formatada}\n")
        
        # Cliente
        if dados_venda.get('cliente_nome'):
            self.printer.text(f"Cliente: {dados_venda['cliente_nome']}\n")
        
        # CPF do cliente (se disponível)
        if dados_venda.get('cliente_cpf'):
            self.printer.text(f"CPF: {dados_venda['cliente_cpf']}\n")
        
        self.printer.text("-" * 32 + "\n")
    
    def _imprimir_itens(self, itens):
        """Imprimir itens da venda"""
        self.printer.set(align='left', text_type='normal', width=1, height=1)
        self.printer.text("ITENS:\n")
        
        for item in itens:
            # Descrição do item
            descricao = item.get('descricao', 'Item')
            if len(descricao) > 30:
                descricao = descricao[:27] + "..."
            self.printer.text(f"{descricao}\n")
            
            # Quantidade, valor unitário e subtotal
            qtd = item.get('quantidade', 0)
            valor_unit = item.get('valor_unitario', 0)
            subtotal = item.get('subtotal', qtd * valor_unit)
            
            qtd_str = f"{qtd:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            valor_unit_str = formatar_moeda(valor_unit)
            subtotal_str = formatar_moeda(subtotal)
            
            # Formatação: Qtd x Valor = Subtotal
            linha_item = f"{qtd_str} x {valor_unit_str} = {subtotal_str}"
            
            # Se a linha for muito longa, quebrar
            if len(linha_item) > 32:
                self.printer.text(f"  {qtd_str} x {valor_unit_str}\n")
                self.printer.text(f"  = {subtotal_str}\n")
            else:
                self.printer.text(f"  {linha_item}\n")
        
        self.printer.text("-" * 32 + "\n")
    
    def _imprimir_totais(self, dados_venda):
        """Imprimir totais da venda"""
        self.printer.set(align='left', text_type='normal', width=1, height=1)
        
        valor_total = dados_venda.get('valor_total', 0)
        valor_pago = dados_venda.get('valor_pago', 0)
        valor_restante = dados_venda.get('valor_restante', valor_total - valor_pago)
        
        # Total da venda
        self.printer.set(align='left', text_type='B', width=1, height=1)
        self.printer.text(f"TOTAL: {formatar_moeda(valor_total)}\n")
        
        # Se há pagamentos
        if valor_pago > 0:
            self.printer.set(align='left', text_type='normal', width=1, height=1)
            self.printer.text(f"Pago: {formatar_moeda(valor_pago)}\n")
            
            if valor_restante > 0:
                self.printer.text(f"Restante: {formatar_moeda(valor_restante)}\n")
            else:
                self.printer.set(align='center', text_type='B', width=1, height=1)
                self.printer.text("*** PAGO ***\n")
        
        self.printer.text("-" * 32 + "\n")
    
    def _imprimir_dados_pagamento(self, dados_pagamento):
        """Imprimir dados do pagamento"""
        self.printer.set(align='left', text_type='normal', width=1, height=1)
        
        self.printer.text("PAGAMENTO:\n")
        
        # Valor pago
        valor_pago = dados_pagamento.get('valor_pago', 0)
        self.printer.text(f"Valor Pago: {formatar_moeda(valor_pago)}\n")
        
        # Forma de pagamento
        forma_map = {
            'dinheiro': 'Dinheiro',
            'cartao': 'Cartão',
            'pix': 'PIX'
        }
        forma = dados_pagamento.get('forma_pagamento', 'N/A')
        forma_texto = forma_map.get(forma, forma)
        self.printer.text(f"Forma: {forma_texto}\n")
        
        # Troco (se pagamento em dinheiro)
        if forma == 'dinheiro':
            troco = dados_pagamento.get('troco', 0)
            if troco > 0:
                self.printer.set(align='left', text_type='B', width=1, height=1)
                self.printer.text(f"TROCO: {formatar_moeda(troco)}\n")
                self.printer.set(align='left', text_type='normal', width=1, height=1)
        
        # Data do pagamento
        if dados_pagamento.get('data_pagamento'):
            data_pag = dados_pagamento['data_pagamento']
            if isinstance(data_pag, str):
                self.printer.text(f"Data Pag.: {data_pag}\n")
            else:
                self.printer.text(f"Data Pag.: {formatar_data_hora_brasileira(data_pag)}\n")
        
        self.printer.text("-" * 32 + "\n")
    
    def _imprimir_rodape(self):
        """Imprimir rodapé do comprovante"""
        self.printer.set(align='center', text_type='normal', width=1, height=1)
        
        # Mensagem de agradecimento
        self.printer.text("Obrigado pela preferencia!\n")
        self.printer.text("Volte sempre!\n")
        self.printer.text("\n")
        
        # Data e hora da impressão
        agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.printer.text(f"Impresso em: {agora}\n")
        
        # Espaço antes do corte
        self.printer.text("\n\n")
    
    def _marcar_comprovante_impresso(self, venda_id):
        """Marcar comprovante como impresso no banco"""
        try:
            if venda_id:
                from database import Database
                db = Database()
                db.execute_query(
                    "UPDATE pagamentos SET comprovante_impresso = TRUE WHERE venda_id = %s",
                    (venda_id,)
                )
                logger.info(f"Comprovante da venda {venda_id} marcado como impresso")
        except Exception as e:
            logger.error(f"Erro ao marcar comprovante como impresso: {e}")
    
    def imprimir_relatorio_vendas_dia(self, data, vendas):
        """Imprimir relatório de vendas do dia"""
        try:
            if not self.conectar():
                return False, "Não foi possível conectar com a impressora"
            
            # Cabeçalho
            self._imprimir_cabecalho_relatorio("VENDAS DO DIA", data)
            
            # Resumo
            total_vendas = len(vendas)
            valor_total = sum(v.get('valor_total', 0) for v in vendas)
            valor_pago = sum(v.get('valor_pago', 0) for v in vendas)
            
            self.printer.set(align='left', text_type='normal', width=1, height=1)
            self.printer.text(f"Total de Vendas: {total_vendas}\n")
            self.printer.text(f"Valor Total: {formatar_moeda(valor_total)}\n")
            self.printer.text(f"Valor Pago: {formatar_moeda(valor_pago)}\n")
            self.printer.text(f"Em Aberto: {formatar_moeda(valor_total - valor_pago)}\n")
            self.printer.text("-" * 32 + "\n")
            
            # Lista de vendas
            for venda in vendas:
                self.printer.text(f"#{venda.get('id')}: {venda.get('cliente_nome', 'Cliente')} - {formatar_moeda(venda.get('valor_total', 0))}\n")
            
            self.printer.text("\n\n")
            self.printer.cut()
            
            self.desconectar()
            return True, "Relatório impresso com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao imprimir relatório: {e}")
            self.desconectar()
            return False, f"Erro na impressão: {str(e)}"
    
    def _imprimir_cabecalho_relatorio(self, titulo, data=None):
        """Imprimir cabeçalho de relatório"""
        empresa_config = Config.SISTEMA_CONFIGS
        
        # Nome da empresa
        self.printer.set(align='center', text_type='B', width=1, height=2)
        self.printer.text(f"{empresa_config['nome_empresa']}\n")
        
        # Título do relatório
        self.printer.set(align='center', text_type='B', width=1, height=1)
        self.printer.text(f"{titulo}\n")
        
        # Data (se fornecida)
        if data:
            self.printer.set(align='center', text_type='normal', width=1, height=1)
            self.printer.text(f"Data: {data}\n")
        
        # Data de geração
        agora = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.printer.text(f"Gerado em: {agora}\n")
        
        self.printer.text("-" * 32 + "\n")

# Função de conveniência para usar sem instanciar a classe
def imprimir_comprovante_venda(dados_venda, dados_pagamento=None):
    """Função de conveniência para imprimir comprovante"""
    printer_manager = PrinterManager()
    return printer_manager.imprimir_comprovante(dados_venda, dados_pagamento)

def testar_impressora():
    """Função de conveniência para testar impressora"""
    printer_manager = PrinterManager()
    return printer_manager.testar_impressora()

def imprimir_relatorio_dia(data, vendas):
    """Função de conveniência para imprimir relatório do dia"""
    printer_manager = PrinterManager()
    return printer_manager.imprimir_relatorio_vendas_dia(data, vendas)

# Configuração alternativa para impressoras que não suportam ESC/POS
class PrinterFallback:
    """Fallback para quando a impressora ESC/POS não está disponível"""
    
    @staticmethod
    def gerar_comprovante_texto(dados_venda, dados_pagamento=None):
        """Gerar comprovante em formato texto para salvamento ou impressão manual"""
        try:
            linhas = []
            empresa_config = Config.SISTEMA_CONFIGS
            
            # Cabeçalho
            linhas.append("=" * 40)
            linhas.append(empresa_config['nome_empresa'].center(40))
            if empresa_config.get('endereco'):
                linhas.append(empresa_config['endereco'].center(40))
            if empresa_config.get('telefone'):
                linhas.append(f"Tel: {empresa_config['telefone']}".center(40))
            if empresa_config.get('cnpj'):
                linhas.append(f"CNPJ: {empresa_config['cnpj']}".center(40))
            
            linhas.append("-" * 40)
            linhas.append("COMPROVANTE DE VENDA".center(40))
            linhas.append("-" * 40)
            
            # Dados da venda
            linhas.append(f"Venda #: {dados_venda.get('id', 'N/A')}")
            if dados_venda.get('data_venda'):
                data_formatada = formatar_data_hora_brasileira(dados_venda['data_venda'])
                linhas.append(f"Data: {data_formatada}")
            if dados_venda.get('cliente_nome'):
                linhas.append(f"Cliente: {dados_venda['cliente_nome']}")
            
            linhas.append("-" * 40)
            linhas.append("ITENS:")
            
            # Itens
            for item in dados_venda.get('itens', []):
                descricao = item.get('descricao', 'Item')
                qtd = item.get('quantidade', 0)
                valor_unit = item.get('valor_unitario', 0)
                subtotal = item.get('subtotal', qtd * valor_unit)
                
                linhas.append(descricao)
                linhas.append(f"  {qtd:,.3f} x {formatar_moeda(valor_unit)} = {formatar_moeda(subtotal)}")
            
            linhas.append("-" * 40)
            
            # Totais
            valor_total = dados_venda.get('valor_total', 0)
            linhas.append(f"TOTAL: {formatar_moeda(valor_total)}")
            
            # Pagamento
            if dados_pagamento:
                linhas.append("")
                linhas.append("PAGAMENTO:")
                linhas.append(f"Valor Pago: {formatar_moeda(dados_pagamento.get('valor_pago', 0))}")
                
                forma_map = {'dinheiro': 'Dinheiro', 'cartao': 'Cartão', 'pix': 'PIX'}
                forma = dados_pagamento.get('forma_pagamento', 'N/A')
                linhas.append(f"Forma: {forma_map.get(forma, forma)}")
                
                if forma == 'dinheiro' and dados_pagamento.get('troco', 0) > 0:
                    linhas.append(f"TROCO: {formatar_moeda(dados_pagamento['troco'])}")
            
            linhas.append("-" * 40)
            linhas.append("Obrigado pela preferencia!".center(40))
            linhas.append("Volte sempre!".center(40))
            
            agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            linhas.append(f"Impresso em: {agora}".center(40))
            linhas.append("=" * 40)
            
            return "\n".join(linhas)
            
        except Exception as e:
            logger.error(f"Erro ao gerar comprovante texto: {e}")
            return None
    
    @staticmethod
    def salvar_comprovante_arquivo(dados_venda, dados_pagamento=None, caminho="comprovantes"):
        """Salvar comprovante em arquivo texto"""
        try:
            from utils import criar_diretorio_se_nao_existe
            
            criar_diretorio_se_nao_existe(caminho)
            
            comprovante_texto = PrinterFallback.gerar_comprovante_texto(dados_venda, dados_pagamento)
            if not comprovante_texto:
                return False, "Erro ao gerar comprovante"
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"comprovante_venda_{dados_venda.get('id', 'xxx')}_{timestamp}.txt"
            caminho_completo = os.path.join(caminho, nome_arquivo)
            
            with open(caminho_completo, 'w', encoding='utf-8') as arquivo:
                arquivo.write(comprovante_texto)
            
            return True, caminho_completo
            
        except Exception as e:
            logger.error(f"Erro ao salvar comprovante: {e}")
            return False, f"Erro ao salvar: {str(e)}"