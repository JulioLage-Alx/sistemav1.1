-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: acougue_db
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `clientes`
--

DROP TABLE IF EXISTS `clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cpf` varchar(14) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `endereco` text COLLATE utf8mb4_unicode_ci,
  `limite_credito` decimal(10,2) DEFAULT '500.00',
  `observacoes` text COLLATE utf8mb4_unicode_ci,
  `ativo` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cpf` (`cpf`),
  KEY `idx_nome` (`nome`),
  KEY `idx_cpf` (`cpf`),
  KEY `idx_ativo` (`ativo`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clientes`
--

LOCK TABLES `clientes` WRITE;
/*!40000 ALTER TABLE `clientes` DISABLE KEYS */;
INSERT INTO `clientes` VALUES (1,'Julio Lage','12406374629','(31) 9714-5779','Rua Dom Prudêncio Gomes, 460 - Coração Eucarístico, Belo Horizonte - MG, Brasil, 30535-580',500.00,'',1,'2025-06-29 13:50:29','2025-06-29 13:50:29');
/*!40000 ALTER TABLE `clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracoes`
--

DROP TABLE IF EXISTS `configuracoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracoes` (
  `chave` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`chave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracoes`
--

LOCK TABLES `configuracoes` WRITE;
/*!40000 ALTER TABLE `configuracoes` DISABLE KEYS */;
INSERT INTO `configuracoes` VALUES ('cnpj_empresa','24356000101','CNPJ da empresa','2025-06-26 19:02:09'),('endereco_empresa','Rua Governador Valadares, Centro','Endereço da empresa','2025-06-26 19:02:09'),('limite_credito_default','500.00','Limite de crédito padrão','2025-06-26 19:02:09'),('limite_inadimplencia_dias','30','Dias para considerar venda vencida','2025-06-26 19:02:09'),('nome_empresa','Casa de Carnes São José','Nome da empresa','2025-06-26 19:02:09'),('telefone_empresa','(31)3861-1575','Telefone da empresa','2025-06-26 19:02:09');
/*!40000 ALTER TABLE `configuracoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `itens_venda`
--

DROP TABLE IF EXISTS `itens_venda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `itens_venda` (
  `id` int NOT NULL AUTO_INCREMENT,
  `venda_id` int NOT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantidade` decimal(8,3) NOT NULL,
  `valor_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) GENERATED ALWAYS AS ((`quantidade` * `valor_unitario`)) STORED,
  PRIMARY KEY (`id`),
  KEY `idx_venda` (`venda_id`),
  CONSTRAINT `itens_venda_ibfk_1` FOREIGN KEY (`venda_id`) REFERENCES `vendas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `itens_venda`
--

LOCK TABLES `itens_venda` WRITE;
/*!40000 ALTER TABLE `itens_venda` DISABLE KEYS */;
INSERT INTO `itens_venda` (`id`, `venda_id`, `descricao`, `quantidade`, `valor_unitario`) VALUES (1,1,'carne de boi',5.000,30.00),(2,2,'carne',2.000,120.00),(3,3,'teste',2.000,20.00);
/*!40000 ALTER TABLE `itens_venda` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs_sistema`
--

DROP TABLE IF EXISTS `logs_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logs_sistema` (
  `id` int NOT NULL AUTO_INCREMENT,
  `acao` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detalhes` text COLLATE utf8mb4_unicode_ci,
  `usuario` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'sistema',
  `ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_acao` (`acao`),
  KEY `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs_sistema`
--

LOCK TABLES `logs_sistema` WRITE;
/*!40000 ALTER TABLE `logs_sistema` DISABLE KEYS */;
INSERT INTO `logs_sistema` VALUES (1,'SISTEMA_CONFIGURADO','Sistema configurado com sucesso','instalador',NULL,'2025-06-26 19:02:09'),(2,'LOGIN','Login realizado','usuario','127.0.0.1','2025-06-26 19:02:57'),(3,'LOGIN','Login realizado','usuario','127.0.0.1','2025-06-29 13:37:20'),(4,'CLIENTE_CRIADO','Cliente Julio Lage (ID: 1)','sistema',NULL,'2025-06-29 13:50:29'),(5,'CLIENTE_CRIADO','Cliente: Julio Lage','usuario','127.0.0.1','2025-06-29 13:50:29'),(6,'VENDA_CRIADA','Venda ID: 1, Cliente: Julio Lage, Valor: R$ 150,00','sistema',NULL,'2025-06-29 13:51:02'),(7,'VENDA_CRIADA','Venda ID: 1, Valor: R$ 150,00','usuario','127.0.0.1','2025-06-29 13:51:02'),(8,'RELATORIO_EXPORTADO','Relatório de vendas: relatorio_vendas_20250629_105209.xlsx','usuario','127.0.0.1','2025-06-29 13:52:09'),(9,'LOGIN','Login realizado','usuario','192.168.0.144','2025-06-29 14:00:57'),(10,'TESTE_IMPRESSORA','Não foi possível conectar com a impressora','usuario','192.168.0.144','2025-06-29 14:01:04'),(11,'PAGAMENTO_PROCESSADO','Venda ID: 1, Valor: R$ 150,00, Forma: cartao','sistema',NULL,'2025-06-29 14:23:02'),(12,'PAGAMENTO_PROCESSADO','Venda ID: 1, Valor: R$ 150,00','usuario','127.0.0.1','2025-06-29 14:23:02'),(13,'VENDA_CRIADA','Venda ID: 2, Cliente: Julio Lage, Valor: R$ 240,00','sistema',NULL,'2025-06-29 14:25:15'),(14,'VENDA_CRIADA','Venda ID: 2, Valor: R$ 240,00','usuario','127.0.0.1','2025-06-29 14:25:15'),(15,'PAGAMENTO_PROCESSADO','Venda ID: 2, Valor: R$ 240,00, Forma: dinheiro','sistema',NULL,'2025-06-29 14:25:29'),(16,'PAGAMENTO_PROCESSADO','Venda ID: 2, Valor: R$ 240,00','usuario','127.0.0.1','2025-06-29 14:25:29'),(17,'VENDA_CRIADA','Venda ID: 3, Cliente: Julio Lage, Valor: R$ 40,00','sistema',NULL,'2025-06-29 14:35:58'),(18,'VENDA_CRIADA','Venda ID: 3, Valor: R$ 40,00','usuario','127.0.0.1','2025-06-29 14:35:58');
/*!40000 ALTER TABLE `logs_sistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pagamentos`
--

DROP TABLE IF EXISTS `pagamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pagamentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `venda_id` int NOT NULL,
  `valor_pago` decimal(10,2) NOT NULL,
  `forma_pagamento` enum('dinheiro','cartao','pix') COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_pagamento` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `observacoes` text COLLATE utf8mb4_unicode_ci,
  `comprovante_impresso` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_venda` (`venda_id`),
  KEY `idx_data_pagamento` (`data_pagamento`),
  CONSTRAINT `pagamentos_ibfk_1` FOREIGN KEY (`venda_id`) REFERENCES `vendas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pagamentos`
--

LOCK TABLES `pagamentos` WRITE;
/*!40000 ALTER TABLE `pagamentos` DISABLE KEYS */;
INSERT INTO `pagamentos` VALUES (1,1,150.00,'cartao','2025-06-29 14:23:01','',0),(2,2,240.00,'dinheiro','2025-06-29 14:25:29','',0);
/*!40000 ALTER TABLE `pagamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendas`
--

DROP TABLE IF EXISTS `vendas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int NOT NULL,
  `data_venda` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `valor_total` decimal(10,2) NOT NULL,
  `valor_pago` decimal(10,2) DEFAULT '0.00',
  `valor_restante` decimal(10,2) GENERATED ALWAYS AS ((`valor_total` - `valor_pago`)) STORED,
  `status` enum('aberta','paga','vencida','cancelada') COLLATE utf8mb4_unicode_ci DEFAULT 'aberta',
  `observacoes` text COLLATE utf8mb4_unicode_ci,
  `venda_origem_ids` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_status` (`status`),
  KEY `idx_data_venda` (`data_venda`),
  CONSTRAINT `vendas_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendas`
--

LOCK TABLES `vendas` WRITE;
/*!40000 ALTER TABLE `vendas` DISABLE KEYS */;
INSERT INTO `vendas` (`id`, `cliente_id`, `data_venda`, `valor_total`, `valor_pago`, `status`, `observacoes`, `venda_origem_ids`, `created_at`, `updated_at`) VALUES (1,1,'2025-06-29 13:51:02',150.00,150.00,'paga','',NULL,'2025-06-29 13:51:02','2025-06-29 14:23:01'),(2,1,'2025-06-29 14:25:15',240.00,240.00,'paga','',NULL,'2025-06-29 14:25:15','2025-06-29 14:25:29'),(3,1,'2025-06-29 14:35:58',40.00,0.00,'aberta','',NULL,'2025-06-29 14:35:58','2025-06-29 14:35:58');
/*!40000 ALTER TABLE `vendas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'acougue_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-29 12:05:23
