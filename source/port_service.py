import os 
import json
import csv
from typing import Optional, Dict
from datetime import datetime, timedelta

class PortService:
    """
    Sistema de identificação de serviços de rede por porta.
    """

    # Constantes de configuração
    CACHE_FILE = "port_service_cache.json"
    CACHE_EXPIRY_DAYS = 30
    IANA_CSV_URL = "https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv"

    def __init__(self, auto_update: bool = True):
        """
        Processo de inicialização do serviço de portas.
        1. Verifica se existe cache local válido.
        2. Se existe e está válido: carrega os dados do cache.
        3. Se não existe ou está expirado: baixa os dados da IANA e atualiza o cache.
        4. Se falhar: usa database hardcoded como fallback
        """
        self.ports_db: Dict[int, str] = {}
        self.cache_file = self.CACHE_FILE
        self.cache_days = self.CACHE_EXPIRY_DAYS
        self.auto_update = auto_update

        # Inicializa o banco de dados de portas
        self._initialize_ports_db()

    def _initialize_ports_db(self) -> None:
        """
        Ordem de tentativas:
        1. Cache local válido -> carregar do cache
        2. Cache expirado -> baixa IANA novo
        3. Iana falhou -> fallback hardcoded
        """
        print("[*] Inicializando sistema de identificação de serviços...")

        # Estratégia 1: Tentar carregar do cache local
        if self._is_cache_valid():
            if self._load_from_cache():
                print(f"[*] Dados carregados do cache local ({len(self.ports_db)}).")
                return
            
        
        # Estratégia 2: Tentar baixar da IANA
        if self.auto_update:
            print("[*] Tentando baixar dados da IANA...")
            if self._update_from_iana():
                print(f"[*] Dados baixados da IANA ({len(self.ports_db)}).")
                self._save_to_cache()
                return

        # Estratégia 3: Fallback hardcoded
        print("[*] Usando banco de dados hardcoded como fallback.")
        self._load_hardcoded_db()
        print(f"[*] Dados carregados do fallback ({len(self.ports_db)}).")

    def _is_cache_valid(self) -> bool:
        """
        Verifica se o cache existe e está dentro do período de validade.

        Returns:
            bool: True se o cache é válido, False caso contrário.
        """

        if not os.path.exists(self.cache_file):
            return False
        
        # Verifica a idade do cache
        try:
            file_modified_time = os.path.getmtime(self.cache_file)
            file_age = datetime.now() - datetime.fromtimestamp(file_modified_time)

            return file_age < timedelta(days=self.cache_days)
        
        except Exception:
            return False
        
    
    def _load_from_cache(self) -> bool:
        """
        Carrega database do arquivo JSON local

        Returns:
            bool: True se o carregamento foi bem-sucedido, False caso contrário.
        """

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                metadata = data.get("metadata", {})
                ports_data = data.get("ports", {})

                #Converte  chaves strings para int
                self.ports_db = {int(k): v for k,v in ports_data.items()}

                #log de informações
                if metadata:
                    created = metadata.get("created", "N/A")
                    source = metadata.get("source", "N/A")
                    print(f"[*] Cache metadata - Created: {created}, Source: {source}")

                return len(self.ports_db) > 0
            
        except Exception as e:
            print(f"[!] Falha ao carregar cache: {e}")
            return False
    

    def _save_to_cache(self) -> bool:
        """
        Salva o database atual em um arquivo JSON local.
        Returns:
            bool: True se o salvamento foi bem-sucedido, False caso contrário.
        """

        try:
            cache_data = {
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'source': 'IANA Service Names and Port Numbers',
                    'total_services': len(self.ports_db),
                    'cache_expiry_days': self.cache_days                   
                },
                'ports': self.ports_db

            }

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=4, ensure_ascii=False)
            
            print(f"[*] Cache salvo em {self.cache_file}.")
            return True
        
        except Exception as e:
            print(f"[!] Falha ao salvar cache: {e}")
            return False
        

    def _download_from_iana(self) -> bool:
        """
        A iana mantem o registro oficial de serviços e portas.

        Returns:
            bool: True se o download foi bem-sucedido, False caso contrário.
        """
