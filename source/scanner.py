
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any


class PortScanner:
    """
    Scanner de portas TCP com suporte a multithreading.

    Esta classe implementa um scanner de portas básico que tenta estabelecer
    conexões TCP em portas especificadas para determinar se estão abertas,
    fechadas ou filtradas.

    Atributos:
        target (str): IP ou hostname do alvo a ser escaneado
        ports (range): Range de portas a serem verificadas
        timeout (float): Tempo máximo de espera por porta (em segundos)
        threads (int): Número de threads simultâneas para paralelização

    Exemplo de uso:
        >>> scanner = PortScanner("scanme.nmap.org", range(1, 1001), timeout=1.0)
        >>> results = scanner.scan_range()
        >>> print(f"Encontradas {len(results)} portas abertas")
    """

    def __init__(self, target: str, ports: range, timeout: float = 1.0, threads: int = 100):
        """
        Construtor da classe PortScanner.

        Inicializa o scanner com as configurações fornecidas e resolve
        o hostname do alvo para seu endereço IP.

        Args:
            target (str): IP (ex: "192.168.1.1") ou hostname (ex: "example.com")
            ports (range): Range de portas (ex: range(1, 1025) para portas 1-1024)
            timeout (float, opcional): Timeout por porta em segundos. Padrão: 1.0
            threads (int, opcional): Número de threads simultâneas. Padrão: 100

        Raises:
            ValueError: Se o hostname não puder ser resolvido para um IP

        Exemplo:
            >>> scanner = PortScanner("google.com", range(80, 81))
        """
        # Atributos públicos - podem ser acessados diretamente
        self.target = target
        self.ports = ports
        self.timeout = timeout
        self.threads = threads

        # Atributo privado (convenção: underscore) - não deve ser acessado diretamente
        # Armazena os resultados do scan
        self._results: List[Dict] = []

        # Resolve o hostname para endereço IP
        # Isso é feito no construtor para falhar rapidamente se o host for inválido
        try:
            # socket.gethostbyname() converte hostname → IP
            # Exemplo: "google.com" → "142.250.219.4"
            self._ip = socket.gethostbyname(target)
            print(f"[*] Hostname '{target}' resolvido para IP: {self._ip}")

        except socket.gaierror:
            # gaierror = "getaddrinfo error" - erro ao resolver nome
            raise ValueError(
                f"Erro: Não foi possível resolver o hostname '{target}'. "
                f"Verifique se o nome está correto e se há conexão com a internet."
            )


    def scan_port(self, port: int) -> Dict[str, Any]:
        """
        Escaneia uma única porta TCP.

        Este é o método CORE do scanner. Cada thread executará este método
        para uma porta diferente. O processo é:

        1. Cria um socket TCP
        2. Define timeout
        3. Tenta conectar na porta (TCP Three-Way Handshake)
        4. Se conectar: porta ABERTA → tenta capturar banner
        5. Se falhar: porta FECHADA ou FILTRADA
        6. Fecha o socket

        Args:
            port (int): Número da porta a ser escaneada (1-65535)

        Returns:
            dict: Dicionário com informações da porta:
                {
                    "port": int,        # Número da porta
                    "status": str,      # "open", "closed", "filtered" ou "error"
                    "service": str,     # Nome do serviço (será preenchido depois)
                    "banner": str       # Banner capturado (se disponível)
                }

        Exemplo:
            >>> result = scanner.scan_port(80)
            >>> print(result)
            {"port": 80, "status": "open", "service": "", "banner": "Apache/2.4"}
        """
        # Cria um novo socket TCP/IP
        # AF_INET = IPv4, SOCK_STREAM = TCP (conexão confiável)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Define timeout: tempo máximo que o socket vai esperar por resposta
        # Se passar desse tempo, levanta exceção socket.timeout
        sock.settimeout(self.timeout)

        try:
            # connect_ex() tenta conectar e retorna código de erro
            # Retorno 0 = sucesso (porta aberta)
            # Retorno != 0 = erro (porta fechada/filtrada)
            #
            # Isso faz o TCP Three-Way Handshake:
            # Cliente → SYN → Servidor
            # Servidor → SYN-ACK → Cliente (se porta aberta)
            # Cliente → ACK → Servidor
            result_code = sock.connect_ex((self._ip, port))

            if result_code == 0:
                # ✅ PORTA ABERTA - Conexão estabelecida com sucesso!

                # Tenta capturar o banner do serviço
                # Banner = mensagem inicial que o serviço envia
                banner = self.grab_banner(sock)

                return {
                    "port": port,
                    "status": "open",
                    "service": "",  # Será preenchido pela classe PortService depois
                    "banner": banner
                }

            else:
                # ❌ PORTA FECHADA ou FILTRADA - Conexão recusada/bloqueada
                
                # Códigos de erro comuns (Windows):
                # 10060 = WSAETIMEDOUT (Timeout - Filtrada)
                # 10061 = WSAECONNREFUSED (Connection Refused - Fechada)
                # 10013 = WSAEACCES (Permission Denied - Bloqueada por firewall local)
                # 10051 = WSAENETUNREACH (Network Unreachable - Sem rota)
                
                # Códigos de erro comuns (Linux):
                # 111 = ECONNREFUSED (Connection Refused - Fechada)
                # 113 = EHOSTUNREACH (No route to host - Sem rota)
                # 110 = ETIMEDOUT (Connection timed out - Timeout)

                # Log de debug apenas para erros incomuns
                # Ignora os códigos mais comuns para não poluir a saída
                if result_code not in [0, 10060, 10061, 10035, 111, 110, 113]:
                    print(f"[DEBUG] Porta {port} - Código de erro incomum: {result_code}")

                return {
                    "port": port,
                    "status": "closed",
                    "service": "N/A",
                    "banner": ""
                }

        except socket.timeout:
            # ⏱️ TIMEOUT - Porta provavelmente filtrada por firewall
            # Firewall está "engolindo" o pacote sem responder
            return {
                "port": port,
                "status": "filtered",
                "service": "N/A",
                "banner": ""
            }

        except PermissionError:
            # 🔒 SEM PERMISSÃO - Algumas portas < 1024 podem precisar de privilégios
            return {
                "port": port,
                "status": "error",
                "service": "Permission Denied",
                "banner": ""
            }

        except Exception as e:
            # ⚠️ ERRO GENÉRICO - Qualquer outro problema
            print(f"[ERRO CRÍTICO] Porta {port}: {type(e).__name__} - {e}")
            return {
                "port": port,
                "status": "error",
                "service": "N/A",
                "banner": f"Erro: {str(e)}"
            }

        finally:
            # SEMPRE fecha o socket, independente do que acontecer
            # Isso libera recursos do sistema operacional
            sock.close()


    def grab_banner(self, sock: socket.socket) -> str:
        """
        Tenta capturar o banner de um serviço.

        Banner = mensagem de identificação que alguns serviços enviam
        automaticamente quando você se conecta.

        Exemplos de banners:
        - SSH: "SSH-2.0-OpenSSH_7.4"
        - FTP: "220 ProFTPD Server ready"
        - HTTP: "Apache/2.4.41 (Ubuntu)"
        - SMTP: "220 mail.example.com ESMTP Postfix"

        O processo é:
        1. Envia uma requisição vazia (\r\n)
        2. Aguarda resposta do servidor (até 1024 bytes)
        3. Decodifica bytes para string UTF-8

        Args:
            sock (socket.socket): Socket já conectado ao serviço

        Returns:
            str: Banner capturado ou string vazia se falhar

        Nota:
            Nem todos os serviços respondem com banner.
            Alguns precisam de comandos específicos.
        """
        try:
            # Envia requisição vazia (carriage return + line feed)
            # Alguns serviços respondem automaticamente a isso
            sock.send(b"\r\n")

            # recv(1024) = recebe até 1024 bytes de dados
            # Isso fica esperando até receber dados ou dar timeout
            banner_bytes = sock.recv(1024)

            # Decodifica bytes para string UTF-8
            # errors="ignore" = ignora caracteres inválidos
            banner_texto = banner_bytes.decode("utf-8", errors="ignore")

            # Remove espaços em branco e quebras de linha
            return banner_texto.strip()

        except socket.timeout:
            # Serviço não respondeu no tempo esperado
            return ""

        except Exception:
            # Qualquer outro erro (conexão perdida, etc)
            return ""


    def scan_range(self) -> List[Dict]:
        """
        Escaneia todas as portas do range usando multi-threading.

        Este método orquestra todo o processo de scanning:
        1. Cria um pool de threads
        2. Distribui as portas entre as threads
        3. Cada thread chama scan_port() para uma porta
        4. Coleta todos os resultados
        5. Filtra apenas portas abertas
        6. Ordena por número da porta

        Multi-threading significa que múltiplas portas são scaneadas
        SIMULTANEAMENTE, tornando o processo muito mais rápido.

        Exemplo de ganho de performance:
            - Sem threads: 1000 portas × 1s = 1000 segundos (~16 minutos)
            - Com 100 threads: 1000 portas ÷ 100 × 1s = 10 segundos

        Returns:
            list: Lista de dicionários contendo apenas portas ABERTAS

        Exemplo:
            >>> scanner = PortScanner("example.com", range(1, 101))
            >>> results = scanner.scan_range()
            >>> for result in results:
            ...     print(f"Porta {result['port']}: {result['status']}")
        """
        # Limpa resultados de scans anteriores (se houver)
        self._results = []

        # Cabeçalho informativo para o usuário
        print(f"\n{'='*60}")
        print(f"INICIANDO SCAN")
        print(f"{'='*60}")
        print(f"[*] Alvo: {self.target} ({self._ip})")
        print(f"[*] Portas: {self.ports.start} - {self.ports.stop - 1}")
        print(f"[*] Total de portas: {len(self.ports)}")
        print(f"[*] Threads: {self.threads} | Timeout: {self.timeout}s")
        print(f"{'='*60}\n")

        # ThreadPoolExecutor = gerenciador de threads do Python
        # max_workers = número máximo de threads rodando ao mesmo tempo
        with ThreadPoolExecutor(max_workers=self.threads) as executor:

            # Submete todas as portas para serem scaneadas
            # executor.submit(função, argumento) = cria uma tarefa para a thread
            #
            # Este dicionário mapeia: future → porta
            # future = "promessa" de um resultado futuro
            future_to_port = {
                executor.submit(self.scan_port, port): port
                for port in self.ports
            }

            # Contadores para mostrar progresso
            completed = 0
            total = len(self.ports)

            # as_completed() retorna futures conforme vão terminando
            # Isso permite processar resultados em tempo real
            for future in as_completed(future_to_port):
                # future.result() obtém o retorno do scan_port()
                result = future.result()

                # Incrementa contador
                completed += 1

                # Mostra progresso a cada 20 portas ou no final
                if completed % 20 == 0 or completed == total:
                    porcentagem = (completed / total) * 100
                    print(f"[*] Progresso: {porcentagem:.1f}%")

                # Só guarda portas ABERTAS (para economizar memória)
                # Portas fechadas/filtradas não são interessantes na maioria dos casos
                if result["status"] == "open":
                    print(f"[!] ENCONTRADO: Porta {result['port']} ABERTA!")
                    self._results.append(result)

        # Ordena resultados por número da porta (ordem crescente)
        # key=lambda x: x["port"] = usa o valor da chave "port" para ordenar
        self._results.sort(key=lambda x: x["port"])

        return self._results


    def get_results(self) -> List[Dict]:
        """
        Getter para acessar os resultados do scan.

        Este método implementa ENCAPSULAMENTO: ao invés de acessar
        diretamente _results (que é privado), usamos este método público.

        Retorna uma CÓPIA da lista para evitar que código externo
        modifique os resultados internos acidentalmente.

        Returns:
            list: Cópia da lista de resultados

        Exemplo:
            >>> results = scanner.get_results()
            >>> results.append({"fake": "data"})  # Não afeta o scanner!
        """
        # .copy() cria uma cópia superficial da lista
        # Isso protege _results de modificações externas
        return self._results.copy()


    def __str__(self) -> str:
        """
        Método especial para representação em string do objeto.

        Chamado automaticamente quando usamos:
        - print(scanner)
        - str(scanner)
        - f"Scanner: {scanner}"

        Similar ao toString() do Java.

        Returns:
            str: Representação legível do scanner
        """
        return (
            f"PortScanner(target='{self.target}', "
            f"ports={self.ports.start}-{self.ports.stop - 1}, "
            f"timeout={self.timeout}s, "
            f"threads={self.threads})"
        )


    def __repr__(self) -> str:
        """
        Método especial para representação técnica do objeto.

        Usado para debugging. Deve retornar uma string que,
        se executada, recria o objeto.

        Chamado por:
        - repr(scanner)
        - No console interativo do Python

        Returns:
            str: Representação técnica do scanner
        """
        return (
            f"PortScanner('{self.target}', "
            f"range({self.ports.start}, {self.ports.stop}), "
            f"timeout={self.timeout}, "
            f"threads={self.threads})"
        )


# ==================== FUNÇÕES AUXILIARES DE TESTE ====================

def executar_teste_scan(
    target: str,
    start_port: int,
    end_port: int,
    timeout: float,
    threads: int,
    desc: str
) -> None:
    """
    Função auxiliar para executar testes de scan de forma padronizada.

    Args:
        target: Hostname ou IP do alvo
        start_port: Porta inicial do range
        end_port: Porta final do range (inclusiva)
        timeout: Timeout em segundos por porta
        threads: Número de threads simultâneas
        desc: Descrição do teste

    Exemplo:
        >>> executar_teste_scan("google.com", 80, 80, 2.0, 1, "Teste Google")
    """
    print(f"\n{'#'*60}")
    print(f"TESTE: {desc}")
    print(f"{'#'*60}")

    try:
        # Cria o scanner
        scanner = PortScanner(
            target=target,
            ports=range(start_port, end_port + 1),
            timeout=timeout,
            threads=threads
        )

        # Mede o tempo de execução
        inicio = time.time()
        results = scanner.scan_range()
        duracao = time.time() - inicio

        # Relatório final
        print(f"\n{'='*60}")
        print(f"RELATÓRIO FINAL")
        print(f"{'='*60}")
        print(f"⏱️  Tempo total: {duracao:.2f}s")
        print(f"📊 Portas scaneadas: {len(scanner.ports)}")
        print(f"✅ Portas abertas: {len(results)}")
        print(f"{'='*60}")

        # Tabela de resultados
        if results:
            print(f"\n{'PORTA':<10} {'STATUS':<12} {'BANNER'}")
            print("-" * 60)
            for res in results:
                # Trunca banner se for muito longo
                banner_preview = res['banner'][:40] + '..' if len(res['banner']) > 40 else res['banner']
                print(f"{res['port']:<10} {res['status']:<12} {banner_preview}")
        else:
            print("\n⚠️  Nenhuma porta aberta encontrada no range especificado.")

    except ValueError as e:
        # Erro esperado (ex: hostname inválido)
        print(f"❌ Erro de validação: {e}")

    except KeyboardInterrupt:
        # Usuário cancelou (Ctrl+C)
        print(f"\n⚠️  Scan interrompido pelo usuário.")

    except Exception as e:
        # Erro inesperado
        print(f"❌ Erro inesperado: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()


# ==================== BLOCO DE TESTE ====================
# Só executa se rodar: python scanner.py
# Não executa se importar: from scanner import PortScanner

if __name__ == "__main__":
    """
    Bateria de testes para validar o Port Scanner.
    
    Testa diferentes cenários:
    1. Conectividade básica (Google)
    2. Site autorizado para testes (scanme.nmap.org)
    """

    print("\n" + "="*60)
    print("🔍 PORT SCANNER - BATERIA DE TESTES")
    print("="*60)

    # TESTE 1: Conectividade básica com Google (porta 80)
    executar_teste_scan(
        target="www.google.com",
        start_port=80,
        end_port=80,
        timeout=2.0,
        threads=1,
        desc="Conectividade Básica (Google Port 80)"
    )

    # TESTE 2: Scan em site autorizado para testes
    executar_teste_scan(
        target="scanme.nmap.org",
        start_port=20,
        end_port=100,
        timeout=1.0,
        threads=50,
        desc="Scan Autorizado (Scanme.nmap.org - Portas 20-100)"
    )

    print("\n" + "="*60)
    print("🎉 BATERIA DE TESTES CONCLUÍDA!")
    print("="*60 + "\n")