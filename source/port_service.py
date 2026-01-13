import socket
from typing import Optional

class PortService:


    CRITICAL_PORTS = {
        21: "FTP",
        22: "SSH",
        23: "TELNET",
        25: "SMTP",
        53: "DNS",
        67: "DHCP",
        68: "DHCP",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        3306: "MYSQL",
        5432: "POSTGRESQL",
        6379: "REDIS",
        27017: "MONGODB",
    }


    @staticmethod
    def get_service_name(port: int) -> str:
        """
        Args:
            port (int): Número da porta
        
        Returns:
            str: Nome do serviço base

        """
        try:
            service_name = socket.getservbyport(port, 'tcp')
            return service_name.upper()
        
        except OSError:
            return PortService.CRITICAL_PORTS.get(port, "UNKNOWN")
        

    @staticmethod
    def get_port_by_service(service_name: str) -> Optional[int]:
        """
        Args:
            service_name (str): Nome do serviço
        
        Returns:
            Optional[int]: Número da porta ou None se não encontrado

        """
        try:
            port = socket.getservbyname(service_name.lower(), 'tcp')
            return port
        except OSError:
            for port, service in PortService.CRITICAL_PORTS.items():
                if service.lower() == service_name.lower():
                    return port
            return None
        
    
def run_tests():
    """Executa testes unitários para verificar o funcionamento das funções."""
    
    test_ports = [22, 80, 3306, 9999]

    for port in test_ports:
        service = PortService.get_service_name(port)
        print(f"Port {port} -> Service: {service}")


if __name__ == "__main__":
    run_tests()