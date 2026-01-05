# 🗺️ ROADMAP - Port Scanner

## Documentação Técnica do Projeto

Este documento detalha a arquitetura, fluxo de dados e funcionamento interno do Port Scanner.

---

## 1. 🎯 Objetivo Principal das Funções

### **source/scanner.py**
**Classe: `PortScanner`**
- `__init__(target, ports, timeout, threads)`: Inicializa configurações do scanner
- `scan_port(port)`: Tenta conexão TCP em uma porta específica
- `grab_banner(sock)`: Captura banner do serviço (identificação)
- `scan_range()`: Orquestra o scan completo com multi-threading
- `get_results()`: Retorna dicionário com resultados do scan

**Responsabilidade**: Lógica central de scanning de portas usando sockets TCP

---

### **source/port_service.py**
**Função: `get_service_name(port, banner)`**
- Recebe número da porta e banner capturado
- Consulta dicionário interno de serviços comuns
- Retorna nome do serviço identificado

**Constante: `COMMON_PORTS`**
- Dicionário mapeando portas → serviços
- Exemplo: `{22: 'SSH', 80: 'HTTP', 443: 'HTTPS', ...}`

**Responsabilidade**: Database de serviços e identificação por porta/banner

---

### **source/report.py**
**Classe: `ReportGenerator`**
- `__init__(scan_data)`: Recebe dados do scan
- `generate_json(filepath)`: Exporta relatório em JSON
- `generate_console_table()`: Formata output para terminal com Rich
- `save_report()`: Salva relatório com timestamp

**Responsabilidade**: Formatação e exportação de resultados

---

### **source/cli.py**
**Função: `main()`**
- Parse de argumentos da linha de comando (argparse)
- Validação de inputs (IP/hostname, range de portas)
- Execução do scanner
- Exibição de progresso e resultados

**Argumentos suportados**:
```bash
--target / -t     → Host alvo (obrigatório)
--ports / -p      → Range de portas (padrão: 1-1024)
--timeout         → Timeout por porta (padrão: 1s)
--threads         → Número de threads (padrão: 100)
--output / -o     → Caminho do relatório JSON
```

**Responsabilidade**: Interface com o usuário via terminal

---

## 2. 📁 Arquitetura de Pastas

```
port-scanner/
│
├── source/                          # Código fonte principal
│   ├── __init__.py                 # Torna 'source' um pacote Python
│   ├── scanner.py                  # [CORE] Lógica do scanner de portas
│   ├── port_service.py             # [DATA] Mapeamento porta → serviço
│   ├── report.py                   # [OUTPUT] Geração de relatórios
│   └── cli.py                      # [INTERFACE] CLI do projeto
│
├── tests/                           # Testes automatizados
│   ├── __init__.py
│   ├── test_scanner.py             # Testes do scanner
│   ├── test_port_service.py        # Testes de identificação de serviços
│   └── test_report.py              # Testes de geração de relatórios
│
├── reports/                         # Relatórios gerados (criado automaticamente)
│   └── .gitkeep                    # Mantém pasta no Git
│
├── .gitignore                       # Arquivos ignorados pelo Git
├── pyproject.toml                   # Configuração do UV e dependências
├── README.md                        # Documentação para usuários
├── ROADMAP.md                       # Documentação técnica (este arquivo)
└── LICENSE                          # Licença MIT
```

### **Convenções de Nomenclatura**
- **Classes**: PascalCase (PortScanner, ReportGenerator)
- **Funções**: snake_case (scan_port, get_service_name)
- **Constantes**: UPPER_CASE (COMMON_PORTS, DEFAULT_TIMEOUT)
- **Arquivos**: snake_case.py

---

## 3. 🔄 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUÁRIO                                  │
│  $ uv run python -m source.cli -t example.com -p 1-1000         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     source/cli.py                               │
│  • Parse argumentos (argparse)                                  │
│  • Valida IP/hostname                                           │
│  • Valida range de portas                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   source/scanner.py                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PortScanner(target, ports, timeout, threads)            │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  scan_range() → Cria ThreadPoolExecutor                  │  │
│  │                                                           │  │
│  │  Para cada porta no range:                               │  │
│  │    └─→ Thread executa scan_port(port)                    │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   [Thread 1]        [Thread 2]   ...  [Thread 100]
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────┐
│              scan_port(port) - Para cada porta                   │
│                                                                  │
│  1. socket.socket(AF_INET, SOCK_STREAM)  ← Cria socket TCP      │
│  2. sock.settimeout(timeout)              ← Define timeout       │
│  3. sock.connect((target, port))          ← Tenta conexão       │
│     │                                                            │
│     ├─→ Sucesso?                                                │
│     │   ├─→ grab_banner(sock)  ← Tenta capturar banner         │
│     │   └─→ Retorna {"port": X, "status": "open", "banner": Y} │
│     │                                                            │
│     └─→ Timeout/Erro?                                           │
│         └─→ Retorna {"port": X, "status": "closed"}             │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                source/port_service.py                           │
│  • Recebe: porta + banner                                       │
│  • Consulta: COMMON_PORTS[porta]                                │
│  • Analisa: banner para identificar versão                      │
│  • Retorna: "SSH - OpenSSH 7.4" ou "HTTP - Apache"             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            Resultados agregados em lista                        │
│  [                                                              │
│    {"port": 22, "status": "open", "service": "SSH"},           │
│    {"port": 80, "status": "open", "service": "HTTP"},          │
│    {"port": 443, "status": "open", "service": "HTTPS"}         │
│  ]                                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   source/report.py                              │
│  • ReportGenerator(scan_data)                                   │
│  • generate_console_table() → Output no terminal (Rich)         │
│  • generate_json() → Salva em reports/scan_TIMESTAMP.json      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT FINAL                               │
│  • Terminal: Tabela colorida com resultados                     │
│  • Arquivo: reports/scan_2025-01-05_143022.json                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. ⚙️ Como Funciona (Detalhamento Técnico)

### **Fase 1: Inicialização**
```python
# cli.py recebe argumentos
target = "scanme.nmap.org"
ports = range(1, 1001)  # Portas 1-1000
timeout = 1.0           # 1 segundo por porta
threads = 100           # 100 threads simultâneas

scanner = PortScanner(target, ports, timeout, threads)
```

### **Fase 2: Resolução de Hostname**
```python
# scanner.py resolve hostname para IP
import socket
ip_address = socket.gethostbyname(target)
# "scanme.nmap.org" → "45.33.32.156"
```

### **Fase 3: Multi-threaded Scanning**
```python
# ThreadPoolExecutor distribui trabalho
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=100) as executor:
    # Cria 100 threads
    futures = [executor.submit(scan_port, port) for port in ports]
    
    # Cada thread executa scan_port() independentemente
    # Thread 1 scanneia porta 1
    # Thread 2 scanneia porta 2
    # ...
    # Thread 100 scanneia porta 100
    # Depois Thread 1 pega porta 101, etc.
```

### **Fase 4: Tentativa de Conexão (Por Porta)**
```python
def scan_port(port):
    try:
        # 1. Cria socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        
        # 2. Tenta conectar (Three-Way Handshake TCP)
        result = sock.connect_ex((ip_address, port))
        
        if result == 0:  # Conexão bem-sucedida
            # 3. Porta ABERTA - Tenta capturar banner
            banner = grab_banner(sock)
            service = get_service_name(port, banner)
            
            return {
                "port": port,
                "status": "open",
                "service": service,
                "banner": banner
            }
        else:
            # Porta FECHADA ou FILTRADA
            return {"port": port, "status": "closed"}
            
    except socket.timeout:
        # Timeout - provavelmente firewall
        return {"port": port, "status": "filtered"}
    
    finally:
        sock.close()
```

### **Fase 5: Captura de Banner**
```python
def grab_banner(sock):
    try:
        # Envia requisição vazia para provocar resposta
        sock.send(b"\r\n")
        
        # Aguarda resposta (banner) do serviço
        banner = sock.recv(1024).decode("utf-8", errors="ignore")
        
        return banner.strip()
        
    except:
        return ""
```

**Exemplo de banners capturados:**
- SSH: `SSH-2.0-OpenSSH_7.4`
- HTTP: `Apache/2.4.41 (Ubuntu)`
- FTP: `220 ProFTPD Server ready`

### **Fase 6: Identificação de Serviço**
```python
# port_service.py
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    3306: "MySQL",
    # ... mais 50+ portas comuns
}

def get_service_name(port, banner):
    service = COMMON_PORTS.get(port, "Unknown")
    
    # Enriquece com informação do banner
    if banner:
        if "SSH" in banner:
            return f"SSH - {banner.split()[0]}"
        elif "Apache" in banner:
            return f"HTTP - Apache"
    
    return service
```

### **Fase 7: Agregação de Resultados**
```python
# scanner.py coleta resultados de todas as threads
results = []
for future in as_completed(futures):
    result = future.result()
    if result["status"] == "open":
        results.append(result)

# Ordena por número da porta
results.sort(key=lambda x: x["port"])
```

### **Fase 8: Geração de Relatório**
```python
# report.py
from rich.console import Console
from rich.table import Table

# Terminal (usando Rich)
table = Table(title="Port Scan Results")
table.add_column("Port", style="cyan")
table.add_column("Status", style="green")
table.add_column("Service", style="yellow")

for result in results:
    table.add_row(
        str(result["port"]),
        result["status"],
        result["service"]
    )

console.print(table)

# JSON (para integração)
import json
with open("reports/scan.json", "w") as f:
    json.dump({
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }, f, indent=2)
```

---

## 5. 🛠️ Tecnologias

### **Core Python (Built-in)**
| Módulo | Versão | Uso |
|--------|--------|-----|
| `socket` | Built-in | Criação de conexões TCP/UDP |
| `concurrent.futures` | Built-in | Multi-threading (ThreadPoolExecutor) |
| `argparse` | Built-in | Parse de argumentos CLI |
| `json` | Built-in | Exportação de relatórios |
| `datetime` | Built-in | Timestamps nos relatórios |

### **Dependências Externas**
| Pacote | Versão | Uso | Instalação |
|--------|--------|-----|------------|
| `rich` | 13.9.4 | Output colorido e tabelas no terminal | `uv add rich` |
| `pytest` | 8.3.4 | Testes automatizados | `uv add pytest --dev` |

### **Ferramentas de Desenvolvimento**
| Ferramenta | Versão | Uso |
|------------|--------|-----|
| `uv` | 0.5.11+ | Gerenciador de pacotes ultra-rápido |
| Python | 3.11+ | Linguagem base do projeto |
| Git | 2.40+ | Controle de versão |

### **Protocolos de Rede Utilizados**
- **TCP (Transmission Control Protocol)**: Protocolo principal para scan de portas
- **Socket API**: Interface de programação para comunicação de rede

---

## 📊 Estimativas de Performance

### **Tempos de Scan (Aproximados)**

| Range de Portas | Threads | Tempo Estimado |
|-----------------|---------|----------------|
| 1-100 | 50 | ~2-3 segundos |
| 1-1024 | 100 | ~10-15 segundos |
| 1-10000 | 100 | ~2-3 minutos |
| 1-65535 | 200 | ~10-15 minutos |

**Fatores que afetam performance:**
- Latência de rede
- Firewalls (aumentam timeout)
- Número de portas abertas (banner grabbing é lento)
- Hardware (CPU para threads)

---

## 🔐 Considerações de Segurança

### **Limitações Técnicas**
1. **Não é stealth**: TCP connect scan é facilmente detectado por IDS/IPS
2. **Logging**: Todas as tentativas de conexão ficam em logs do servidor
3. **Rate limiting**: Muitas conexões simultâneas podem ser bloqueadas

### **Melhorias Futuras (v2.0)**
- Implementar SYN scan (mais discreto, requer root)
- Randomização da ordem de portas
- Delay configurável entre scans
- User-Agent spoofing para HTTP

---

## 🧪 Testes

### **Cobertura de Testes**
```bash
# Rodar todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov=source tests/
```

### **Casos de Teste**
- ✅ Scan de porta aberta
- ✅ Scan de porta fechada
- ✅ Timeout em porta filtrada
- ✅ Identificação correta de serviços
- ✅ Geração de relatório JSON válido
- ✅ Validação de inputs inválidos

---

## 🚀 Roadmap de Desenvolvimento

### **Versão 1.0** (Atual)
- [x] Scan TCP básico
- [x] Multi-threading
- [x] Detecção de serviços comuns
- [x] Output no terminal com Rich
- [x] Exportação JSON

### **Versão 1.5** (Próximos passos)
- [ ] Scan UDP
- [ ] Progress bar com Rich.progress
- [ ] Melhor tratamento de erros
- [ ] Logging em arquivo

### **Versão 2.0** (Futuro)
- [ ] SYN scan (stealth)
- [ ] OS fingerprinting
- [ ] Exportação HTML/PDF
- [ ] API REST

---

## 📚 Referências Técnicas

- [Socket Programming in Python](https://docs.python.org/3/library/socket.html)
- [Nmap: Network Scanning Guide](https://nmap.org/book/)
- [RFC 793 - TCP Specification](https://tools.ietf.org/html/rfc793)
- [IANA Port Numbers](https://www.iana.org/assignments/service-names-port-numbers/)

---

**Última atualização**: 05 de Janeiro de 2025  
**Mantenedor**: Wanderson Lucas Damasceno Freitas