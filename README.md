## 📋 Sobre o Projeto

O **Port Scanner** é uma ferramenta de linha de comando desenvolvida para identificar portas abertas em hosts remotos, detectar serviços em execução e gerar relatórios detalhados.

Este projeto foi criado como uma ferramenta educacional para aprender sobre:

- Conceitos de rede (TCP/IP, portas, protocolos)
- Programação concorrente (multi-threading)
- Segurança da informação (reconhecimento e mapeamento de rede)
- Boas práticas de desenvolvimento em Python

### 🎯 Objetivo Principal

Fornecer uma ferramenta simples, rápida e eficaz para:

- ✅ **Auditorias de segurança**: Identificar portas abertas em sua própria infraestrutura
- ✅ **Aprendizado**: Entender como funcionam scanners de porta profissionais
- ✅ **Reconhecimento de rede**: Mapear serviços disponíveis em um host
- ✅ **Documentação**: Gerar relatórios de scan em formato JSON

⚠️ **IMPORTANTE**: Use apenas em redes próprias ou com autorização explícita. Scanning não autorizado é ilegal.

---

## ✨ Características

- 🚀 **Multi-threading**: Scan paralelo de até 200 portas simultaneamente
- 🎨 **Interface visual**: Output colorido e formatado com Rich
- 🔍 **Detecção de serviços**: Identifica automaticamente 50+ serviços comuns
- 📊 **Relatórios JSON**: Exportação estruturada para integração com outras ferramentas
- ⚡ **Performance**: Scan de 1000 portas em ~10 segundos
- 🛡️ **Banner grabbing**: Captura informações de versão dos serviços
- 🎯 **Range customizável**: Escolha quais portas scanear (ex: 1-1024, 80,443,8080)
- ⏱️ **Timeout configurável**: Ajuste o tempo de espera por porta

---

## 🛠️ Tecnologias Usadas

### **Core**

- **Python 3.11+**: Linguagem principal
- **socket**: Comunicação TCP/IP nativa
- **concurrent.futures**: Multi-threading para paralelização
- **argparse**: Interface de linha de comando

### **Dependências**

- **[Rich 13.9.4](https://github.com/Textualize/rich)**: Terminal formatting e tabelas
- **[pytest 8.3.4](https://pytest.org/)**: Framework de testes (dev)

### **Gerenciamento**

- **[uv](https://github.com/astral-sh/uv)**: Gerenciador de pacotes ultra-rápido

---

## 📁 Arquitetura de Pastas

```
port-scanner/
│
├── source/                    # 📦 Código fonte
│   ├── __init__.py           # Inicialização do pacote
│   ├── scanner.py            # 🔍 Lógica principal do scanner
│   ├── port_service.py       # 🗂️ Database de serviços
│   ├── report.py             # 📊 Geração de relatórios
│   └── cli.py                # 🖥️ Interface CLI
│
├── tests/                     # 🧪 Testes automatizados
│   ├── test_scanner.py
│   ├── test_port_service.py
│   └── test_report.py
│
├── reports/                   # 📄 Relatórios gerados (criado automaticamente)
│
├── .gitignore                # Arquivos ignorados pelo Git
├── pyproject.toml            # Configuração de dependências
├── README.md                 # Este arquivo
├── ROADMAP.md                # Documentação técnica detalhada
└── LICENSE                   # Licença MIT
```

---

## 🚀 Instalação

### **Pré-requisitos**

- Python 3.11 ou superior
- [uv](https://github.com/astral-sh/uv) instalado

#### Instalando o UV (se necessário)

**Linux/macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### **1. Clone o repositório**

```bash
git clone https://github.com/WL-DF/port-scanner.git
cd port-scanner
```

### **2. Instale as dependências**

```bash
# Instala todas as dependências automaticamente
uv sync
```

### **3. Verifique a instalação**

```bash
uv run python -m source.cli --help
```

Se você ver a mensagem de ajuda, está tudo pronto! 🎉

---

## 💻 Uso

### **Sintaxe Básica**

```bash
uv run python -m source.cli -t <TARGET> [OPÇÕES]
```

### **Exemplos Práticos**

#### 1. **Scan básico (portas 1-1024)**

```bash
uv run python -m source.cli -t scanme.nmap.org
```

#### 2. **Scan em range específico**

```bash
uv run python -m source.cli -t 192.168.1.1 -p 1-1000
```

#### 3. **Scan de portas específicas**

```bash
uv run python -m source.cli -t example.com -p 80,443,8080,3306
```

#### 4. **Scan com mais threads (mais rápido)**

```bash
uv run python -m source.cli -t 10.0.0.1 -p 1-10000 --threads 200
```

#### 5. **Scan com timeout customizado**

```bash
uv run python -m source.cli -t slow-server.com -p 1-1000 --timeout 2
```

#### 6. **Exportar para arquivo específico**

```bash
uv run python -m source.cli -t target.com -o meu_scan.json
```

### **Opções Disponíveis**

| Opção              | Descrição                                     | Padrão                     |
| -------------------- | ----------------------------------------------- | --------------------------- |
| `-t`, `--target` | Host alvo (IP ou hostname)                      | *Obrigatório*            |
| `-p`, `--ports`  | Range ou lista de portas (ex: 1-1024 ou 80,443) | 1-1024                      |
| `--timeout`        | Timeout em segundos por porta                   | 1.0                         |
| `--threads`        | Número de threads simultâneas                 | 100                         |
| `-o`, `--output` | Caminho do arquivo de relatório JSON           | reports/scan_TIMESTAMP.json |
| `-h`, `--help`   | Mostra mensagem de ajuda                        | -                           |

---

## 📊 Exemplo de Output

```bash
$ uv run python -m source.cli -t scanme.nmap.org -p 1-100

╔═══════════════════════════════════════════════════════╗
║           Port Scanner v1.0 - by Wanderson           ║
╚═══════════════════════════════════════════════════════╝

[*] Target: scanme.nmap.org (45.33.32.156)
[*] Scanning ports: 1-100
[*] Threads: 100
[*] Timeout: 1.0s

Scanning... ████████████████████ 100%

╔═══════════════════════════════════════════════════════╗
║                    Scan Results                       ║
╠═══════╦═══════════╦═══════════════════════════════════╣
║ Port  ║  Status   ║          Service                  ║
╠═══════╬═══════════╬═══════════════════════════════════╣
║  22   ║   OPEN    ║  SSH - OpenSSH 7.4               ║
║  80   ║   OPEN    ║  HTTP - Apache/2.4.7             ║
║  443  ║   OPEN    ║  HTTPS - nginx/1.18.0            ║
╚═══════╩═══════════╩═══════════════════════════════════╝

[✓] Scan completed in 8.42s
[✓] Found 3 open ports
[*] Report saved: reports/scan_2025-01-05_153042.json
```

### **Relatório JSON**

```json
{
  "scan_info": {
    "target": "scanme.nmap.org",
    "ip_address": "45.33.32.156",
    "timestamp": "2025-01-05T15:30:42.123456",
    "total_ports_scanned": 100,
    "scan_duration": 8.42
  },
  "results": [
    {
      "port": 22,
      "status": "open",
      "service": "SSH - OpenSSH 7.4",
      "banner": "SSH-2.0-OpenSSH_7.4"
    },
    {
      "port": 80,
      "status": "open",
      "service": "HTTP - Apache/2.4.7",
      "banner": "Apache/2.4.7 (Ubuntu)"
    },
    {
      "port": 443,
      "status": "open",
      "service": "HTTPS - nginx/1.18.0",
      "banner": ""
    }
  ]
}
```

---

## 🧪 Testes

### **Rodar todos os testes**

```bash
uv run pytest
```

### **Testes com cobertura**

```bash
uv run pytest --cov=source tests/
```

### **Testes verbosos**

```bash
uv run pytest -v
```

---

## 🤝 Contribuição

Contribuições são muito bem-vindas! Este projeto está aberto para melhorias.

### **Como contribuir**

1. **Fork o projeto**

```bash
# Clique no botão "Fork" no GitHub
```

2. **Clone seu fork**

```bash
git clone https://github.com/SEU-USUARIO/port-scanner.git
cd port-scanner
```

3. **Crie uma branch para sua feature**

```bash
git checkout -b feature/minha-nova-feature
```

4. **Faça suas alterações e commit**

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
```

5. **Push para seu fork**

```bash
git push origin feature/minha-nova-feature
```

6. **Abra um Pull Request**

- Vá até o repositório original no GitHub
- Clique em "New Pull Request"
- Descreva suas mudanças

### **Diretrizes de Contribuição**

- ✅ Siga o padrão de código Python (PEP 8)
- ✅ Adicione testes para novas funcionalidades
- ✅ Atualize a documentação quando necessário
- ✅ Use mensagens de commit descritivas
- ✅ Mantenha o código limpo e comentado

### **Ideias para Contribuição**

- 🔹 Implementar scan UDP
- 🔹 Adicionar progress bar animada
- 🔹 Criar exportação em HTML/PDF
- 🔹 Implementar SYN scan (stealth mode)
- 🔹 Adicionar detecção de sistema operacional
- 🔹 Melhorar identificação de serviços com regex
- 🔹 Criar API REST para o scanner

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

```
MIT License

Copyright (c) 2025 Wanderson Lucas Damasceno Freitas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## ⚠️ Aviso Legal

**USO RESPONSÁVEL**

Este software foi desenvolvido exclusivamente para **fins educacionais** e de **auditoria de segurança autorizada**.

- ✅ **Permitido**: Usar em sua própria rede ou infraestrutura
- ✅ **Permitido**: Usar em ambientes de teste autorizados (ex: scanme.nmap.org)
- ✅ **Permitido**: Aprendizado e pesquisa acadêmica
- ❌ **PROIBIDO**: Scanear redes ou sistemas sem autorização explícita
- ❌ **PROIBIDO**: Usar para fins maliciosos ou ilegais
- ❌ **PROIBIDO**: Violar leis de crimes cibernéticos locais ou internacionais

**O autor NÃO se responsabiliza por uso indevido desta ferramenta.**

Scanning não autorizado pode ser considerado crime em muitos países, incluindo Brasil (Lei 12.737/2012 - Lei Carolina Dieckmann).

---

## 👤 Autor

**Wanderson Lucas Damasceno Freitas**

- GitHub: [@WL-DF](https://github.com/WL-DF)
- Email: wanderson.ldf11@gmail.com
- LinkedIn: [Wanderson Lucas](https://www.linkedin.com/in/wanderson-lucas)
-
