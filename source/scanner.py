
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

class PortScanner:
    """
    Scanner de portas TCP com suporte a multithreading.

    Esta classe implementa um scanner de portas básico que tenta estabelecer
    conexões TCP em portas diferentes para determinar se estão abertas ou 
    fechadas ou filtradas.

    Atributos:
        target (str): O endereço IP ou nome do host a ser escaneado.
        ports (range): A lista de portas a serem escaneadas.
        timeout (float): O tempo limite para cada tentativa de conexão em 
        segundos
        threads (int): Número de threads simultâneas para paralelização

    Exemplo de uso:
        >>> scanner = PortScanner("scanner.nmap.org", range(1,1001),
        timeout=1.0)
        >>> results = scanner.scan_range()
        >>> print(f"Encontradas {len(results)} portas abertas.")
    """

    def __init__(self, target: str, ports: range, timeout: float = 1.0, threads:
    int = 100):
        """ 
        Construdor da classe PortScanner.

        Inicializa o scanner com as configurações fornecidas e resolve o host
        name do alvo para seu endereço IP.

        Args:
            target (str): O endereço IP ou nome do host a ser escaneado.
            ports (range): A lista de portas a serem escaneadas.
            timeout (float, opcional): O tempo limite para cada tentativa de 
            conexão em segundos. Padrão é 1.0 segundo.
            threads (int, opcional): Número de threads simultâneas para 
            paralelização. Padrão é 100.

        Raises:
            ValueError: Se o nome do host não puder ser resolvido para um IP.

        Exemplo:
            >>> scanner = PortScanner("google.com", range(80,81))

        """
        # atributos públicos
        self.target = target
        self.ports = ports
        self.timeout = timeout
        self.threads = threads

        # atributos privados
        self._results: List[Dict] = []

        try:
            self._ip = socket.gethostbyname(target)
            print(f"[*] Hostname {target} resolvido para IP: {self._ip}")
        
        except socket.gaierror as e:
            raise ValueError(f"Erro: não foi possível resolver o hostname {target}.")
        
    def scan_port(self, port: int) -> Dict[str, any]:
        """
        Escaneia uma única porta TCP no alvo.

        1. Cria um socket TCP.
        2. Define o timeout
        3. Tenta conectar ao alvo na porta especificada.
        4. Se conectar: Porta Aberta -> tenta capturar o banner
        5. Se falhar: Porta Fechada ou Filtrada
        6. Fecha o socket e retorna o resultado.

        Args:
            port (int): Número da porta a ser escaneada.

        Returns:
            Dict: Dicionário com o resultado do escaneamento da porta.
                {
                    "port": int     # Número da porta escaneada
                    "status": str   # "open", "closed" ou "filtered"
                    "service": str  # Nome do serviço padrão (se conhecido)
                    "banner": str   # Banner capturado (se disponível)
                
                }
        """

        try:
            result_code = socket.connect_ex((self._ip, port))
            
            if result_code == 0:
                # Porta Aberta

                banner = self.grab_banner(socket)

                return {
                    "port": port,
                    "status": "open",
                    "service": "",
                    "banner": banner
                }
            
            else:
                return {
                    "port": port,
                    "status": "closed",
                    "service": "N/A",
                    "banner": ""
                }

        except socket.timeout:
            return{
                "port": port,
                "status": "filtered",
                "service": "N/A",
                "banner": ""
            }
        
        except PermissionError:
            return{
                "port": port,
                "status": "filtered",
                "service": "Permission Denied",
                "banner": ""}  
        
        except Exception as e:
            return{
                "port": port,
                "status": "error",
                "service": "N/A",
                "banner": f"Erro: {str(e)}"}
        
        finally:
            socket.close()


    def grab_banner(self, sock: socket.socket) -> str:
        """
        Tenta capturar o banner de um serviço

        Banner = mensagem de identificação que alguns serviços enviam
        automaticamente ao estabelecer uma conexão.

        exemplos:
        - SSH: "SSH-2.0-OpenSSH_7.4"
        - FTP: "220 (vsFTPd 3.0.3)"
        - HTTP: "HTTP/1.1 200 OK"

        O processo é:
        1. Envia uma requisição vazia (\r\n)
        2. Aguarda a resposta do servidor
        3. Decodifica bytes para string UTF-8

        Args:
            sock (socket.socket): Socket conectado ao serviço.

        Returns:
            str: Banner capturado ou string vazia se não for possível.
        
        """
        try:
            sock.send(b"\r\n") # Envia uma requisição vazia

            banner_bytes = sock.recv(1024) # Recebe até 1024 bytes

            banner_text = banner_bytes.decode("utf-8", errors="ignore")

            return banner_text.strip() # Remove espaços em branco extras
        
        except socket.timeout:
            return ""  # Timeout ao tentar capturar o banner
        
        except Exception:
            return ""
        

    def scan_range(self) -> List[Dict]:
        """
        Escaneia todas as portas no intervalo especificado usando multithreading
        
        Este método orquestra o processo de escaneamento:
        1. Cria um pool de threads com o número especificado de threads.
        2. Submete tarefas de escaneamento para cada porta no intervalo.
        3. Coleta os resultados conforme as tarefas são concluídas.
        4. filtra e retorna apenas as portas abertas.
        5. Ordena por número da porta.

        Multi-threading significa que múltiplas portas podem ser escaneadas
        simultaneamente, acelerando o processo.

        """

        self._results = []

        print(f"\n{'='*60}")
        print(f"Iniciando Scan")
        print(f"{'='*60}")
        print(f"[*] Alvo: {self.target} ({self._ip})")
        print(f"[*] Portas: {self.ports.start} a {self.ports.stop - 1}")
        print(f"[*] Total de portas: {len(self.ports)}")
        print(f"[*] Timeout por porta: {self.timeout}")
        print(f"[*] Threads simultâneas: {self.threads}")
        print(f"{'='*60}\n")

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submete tarefas para cada porta

            future_to_part = {
                executor.submit(self.scan_port, port) : port
                for port in self.ports
            }

            completed = 0
            total = len(self.ports)

            # as_completed() retorna futures conforme são concluídas
            # isso vai permitir atualizar o progresso em tempo real
            for future in as_completed(future_to_part):
                #Obtem o resultado do scan_port
                result = future.result()

                completed += 1

                if completed % 50  == 0 or completed == total:
                    porcetagem = (completed / total) * 100
                    print(f"[*] Progresso:({porcetagem:.1f}%)")
                
                #Só guarda portas abertas
                if result["status"] == "open":
                    self._results.append(result)

        self._results.sort(key=lambda x: x["port"])

        print(f"\n{'='*60}")
        print(f"SCAN CONCLUÍDO")
        print(f"{'='*60}")
        print(f"[✓] Total de portas scaneadas: {total}")
        print(f"[✓] Portas abertas encontradas: {len(self._results)}")
        print(f"{'='*60}\n")

        return self._results
        