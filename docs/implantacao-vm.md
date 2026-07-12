# Implantação em VM (KVM) — opção alternativa ao bare-metal

> Esta é uma **opção** de implantação. A forma padrão de rodar o sistema continua sendo bare-metal (direto na máquina), conforme descrito no [`README.md`](../README.md). Este documento é para quem quiser isolar o servidor ASAC numa máquina virtual — por exemplo, para testar em ambiente descartável (com snapshots), rodar ao lado de outros serviços no mesmo computador físico, ou preparar uma migração futura para outro hardware sem afetar o sistema operacional principal.

Todos os recursos do sistema (scanner de código de barras via webcam USB, acesso HTTPS pelo celular na rede local, serviço systemd) funcionam dentro da VM — os passos abaixo mostram como reproduzir cada um deles no ambiente virtualizado.

---

## Visão geral

1. Preparar o host (verificar suporte a virtualização, instalar KVM/QEMU/virt-manager)
2. Configurar uma **bridge de rede** no host, para a VM receber IP próprio na rede local
3. Criar a VM (Ubuntu Server 24.04 LTS) com virt-manager
4. Fazer o **passthrough USB** da webcam para a VM
5. Instalar o projeto dentro da VM (igual ao bare-metal: venv, dependências, `.env`)
6. Configurar HTTPS (mkcert) e o serviço systemd dentro da VM
7. Testar o fluxo completo: navegador do celular → HTTPS → VM → webcam passthrough → scanner
8. Snapshots e rotina de backup da VM

---

## Pré-requisitos do host

- CPU com suporte a virtualização (Intel VT-x ou AMD-V) **habilitado na BIOS/UEFI**
- Linux com `systemd` (Ubuntu/Debian nos exemplos abaixo — ajuste os comandos de pacote se usar outra distro)
- Acesso `sudo` no host
- Um cabo de rede/Wi-Fi já conectando o host à rede local (a bridge vai reaproveitar essa conexão)
- Webcam USB disponível (a mesma usada hoje no bare-metal serve)

### 1. Verificar suporte a virtualização

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
```

Se o resultado for `0`, a virtualização por hardware está desabilitada na BIOS/UEFI ou o processador não suporta — habilite antes de continuar (a opção costuma se chamar "Intel VT-x", "Intel Virtualization Technology" ou "SVM Mode", dependendo do fabricante).

---

## 2. Instalar KVM, QEMU e virt-manager

```bash
sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
```

Adicione seu usuário aos grupos necessários (evita ter que rodar tudo como root):

```bash
sudo usermod -aG libvirt,kvm $USER
```

**Faça logout e login novamente** (ou reinicie) para o novo grupo entrar em vigor. Confirme que o serviço está ativo:

```bash
sudo systemctl status libvirtd
```

Abra o virt-manager (`virt-manager` no terminal, ou pelo menu de aplicativos) e confirme que ele conecta em "QEMU/KVM" sem pedir senha de root.

---

## 3. Configurar bridge de rede no host

Por padrão, o libvirt cria a VM numa rede **NAT** isolada (IP tipo `192.168.122.x`), o que funciona para a VM acessar a internet, mas **não permite que o celular na rede local acesse a VM diretamente** — exigiria redirecionamento manual de porta e complicaria os certificados mkcert (que são gerados por IP).

A solução recomendada é criar uma **bridge**: a VM passa a ter um IP próprio na mesma rede local do celular (ex.: `192.168.15.x`), exatamente como acontece hoje com o bare-metal.

> ⚠️ Editar a configuração de rede do host pode derrubar a conexão temporariamente enquanto a interface é reconfigurada. Como este é um procedimento local (não um servidor remoto acessado por SSH), o risco é baixo — mas vale fechar downloads/chamadas em andamento antes de aplicar.

### 3.1 Identificar a interface de rede atual

```bash
ip a
```

Anote o nome da interface conectada à rede local (ex.: `enp3s0`, `eth0` ou `wlan0` — **Wi-Fi não pode ser colocado em bridge na maioria dos drivers**; se o host só tem Wi-Fi, use a alternativa NAT com redirecionamento de porta descrita no final desta seção).

### 3.2 Criar a bridge com netplan (Ubuntu)

Faça backup do arquivo atual antes de editar:

```bash
sudo cp /etc/netplan/*.yaml ~/netplan-backup-$(date +%Y%m%d).yaml
ls /etc/netplan/
```

Edite o arquivo netplan (o nome varia, ex.: `/etc/netplan/01-network-manager-all.yaml`) substituindo a interface física pela bridge:

```yaml
network:
  version: 2
  ethernets:
    enp3s0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [enp3s0]
      dhcp4: yes
      parameters:
        stp: false
        forward-delay: 0
```

Aplique:

```bash
sudo netplan try     # mostra preview e reverte sozinho em 120s se algo quebrar
sudo netplan apply   # confirma, se estiver tudo certo
ip a show br0        # confirme que br0 recebeu um IP da rede local
```

### 3.3 Apontar a VM para a bridge

Isso é feito na tela de rede da VM (passo 4.4 abaixo), selecionando **"Bridge device..."** e informando `br0` — não é necessário criar uma "rede virtual" separada no libvirt para isso.

### Alternativa: host só com Wi-Fi (sem bridge)

Se a interface de rede do host for Wi-Fi, use a rede NAT padrão do libvirt e redirecione a porta 8000 do host para a VM:

```bash
# descobra o IP da VM dentro dela mesma com `ip a`, depois no host:
sudo iptables -t nat -A PREROUTING -p tcp --dport 8000 -j DNAT --to-destination <IP_DA_VM>:8000
sudo iptables -A FORWARD -p tcp -d <IP_DA_VM> --dport 8000 -j ACCEPT
```

Nesse caso, o celular acessa pelo IP do **host** (`https://<IP_DO_HOST>:8000`), e o certificado mkcert deve ser gerado para o IP do host, não da VM. Essa alternativa é mais frágil (regras de iptables não sobrevivem a reboot sem serem persistidas) — prefira a bridge sempre que possível.

---

## 4. Criar a VM no virt-manager

### 4.1 Baixar a ISO do Ubuntu Server 24.04 LTS

Baixe a ISO oficial em `https://ubuntu.com/download/server` (link oficial — confirme o site antes de baixar).

### 4.2 Assistente de nova VM

No virt-manager: **Arquivo → Nova máquina virtual**

1. "Mídia de instalação local (ISO)" → selecione o arquivo baixado
2. Recursos recomendados para este sistema (FastAPI + YOLO nano + pyzbar):
   - **2 vCPUs** (mínimo)
   - **4 GB de RAM** (mínimo — 2 GB sobem o sistema, mas a inferência YOLO fica apertada)
   - **25 GB de disco**
3. Nomeie a VM (ex.: `asac-servidor`)
4. **Marque "Personalizar configuração antes de instalar"** antes de finalizar — precisamos ajustar CPU e rede antes do primeiro boot

### 4.3 Configuração de CPU (importante para performance do YOLO)

Na tela de personalização, vá em **CPUs** e mude o modelo de CPU para:

```
Configuração: Copiar configuração de CPU do host (host-passthrough)
```

Isso expõe ao guest as mesmas instruções vetoriais do processador físico (AVX2, etc.), usadas pelo PyTorch/Ultralytics — sem isso, a inferência YOLO roda com CPU emulada genérica e fica sensivelmente mais lenta.

### 4.4 Configuração de rede

Na seção **NIC**, mude "Rede virtual: NAT" para **"Especificar dispositivo de bridge/macvtap compartilhado"** → digite `br0` (a bridge criada no passo 3).

### 4.5 Instalar o Ubuntu Server

Prossiga com a instalação padrão do Ubuntu Server:
- Configure rede como DHCP (vai pegar IP da bridge, ou seja, da rede local)
- **Marque "Install OpenSSH server"** durante a instalação — facilita administrar a VM via terminal do host depois
- Crie um usuário (ex.: `asac`)

Ao terminar, anote o IP que a VM recebeu (`ip a` dentro da VM, ou veja na tela "Detalhes" da VM no virt-manager).

---

## 5. Passthrough USB da webcam

A webcam física precisa ser "emprestada" da máquina host para a VM.

### 5.1 Conectar o dispositivo à VM

Com a VM ligada, no virt-manager: **Mostrar detalhes virtuais da máquina (ícone de informação) → Adicionar hardware → Host USB Device** → selecione a webcam na lista (aparece pelo nome do fabricante, ex.: "Logitech Webcam C270") → **Concluir**.

O dispositivo é anexado a quente — não precisa desligar a VM.

> Enquanto a webcam estiver passada para a VM, **ela some do host** (não aparece mais em `ls /dev/video*` na máquina física). Para devolver ao host, remova o dispositivo na mesma tela (clique nele → **Remover hardware**).

### 5.2 Confirmar dentro da VM

```bash
lsusb                          # a webcam deve aparecer na lista
sudo apt install v4l-utils
v4l2-ctl --list-devices        # deve listar /dev/video0 (ou similar)
```

Se a webcam não aparecer, verifique `dmesg | tail -30` dentro da VM logo após anexar o dispositivo — costuma indicar erro de permissão ou dispositivo composto (webcams com microfone embutido às vezes aparecem como dois dispositivos USB; passe ambos).

---

## 6. Instalar o projeto dentro da VM

A partir daqui, os passos são **idênticos ao bare-metal** — a VM se comporta como qualquer máquina Linux comum.

```bash
sudo apt update
sudo apt install python3.12-venv python3-pip git libzbar0   # libzbar0: dependência do pyzbar

git clone https://github.com/fabriciogeog/asac-materiais.git
cd asac-materiais

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure o `.env` (copie de `.env.example` e preencha a chave da Cosmos):

```bash
cp .env.example .env
nano .env   # preencher BLUE_SOFT_COSMOS_KEY
```

Inicialize o banco:

```bash
python seed.py
```

---

## 7. HTTPS (mkcert) dentro da VM

Repita o procedimento de mkcert descrito na seção ["Acesso pela rede local com câmera (celular)"](../README.md#acesso-pela-rede-local-com-câmera-celular) do README principal, mas usando o **IP da VM na bridge** (não o IP do host):

```bash
sudo apt install mkcert libnss3-tools
mkcert -install

mkdir -p certs
mkcert -cert-file certs/cert.pem -key-file certs/key.pem \
  <IP_DA_VM_NA_BRIDGE> localhost 127.0.0.1
```

Transfira o `rootCA.pem` (mostrado por `mkcert -CAROOT` dentro da VM) para o celular e instale como certificado confiável, do mesmo jeito já documentado no README principal.

Teste subindo manualmente antes de criar o serviço:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

Acesse do celular em `https://<IP_DA_VM>:8000/ui/login.html` — se a webcam foi passada corretamente (passo 5) e a bridge está funcionando (passo 3), o scanner deve funcionar exatamente como no bare-metal.

Se a VM usar `ufw`, libere a porta antes de testar:

```bash
sudo ufw allow 8000/tcp
```

---

## 8. Serviço systemd dentro da VM

Igual ao bare-metal (seção ["Executar como serviço systemd (produção)"](../README.md#executar-como-serviço-systemd-produção) do README), com atenção especial aos caminhos:

> O `systemd/asac.service` versionado no repositório tem caminhos absolutos apontando para a máquina de desenvolvimento original. Dentro da VM, o usuário e o caminho do clone são diferentes — **edite `WorkingDirectory` e `ExecStart`** antes de instalar, apontando para o caminho real dentro da VM (ex.: `/home/asac/asac-materiais`).

```bash
grep -E "WorkingDirectory|ExecStart" systemd/asac.service
pwd    # compare e edite o arquivo se divergir

sudo cp systemd/asac.service /etc/systemd/system/asac.service
sudo systemctl daemon-reload
sudo systemctl enable --now asac
```

Comandos do dia a dia (rodar dentro da VM):

```bash
sudo systemctl status asac
journalctl -u asac -f
```

Se aparecer `status=203/EXEC`, veja a seção de troubleshooting equivalente no README principal — as causas (venv ausente, caminho errado, permissão) são as mesmas.

---

## 9. Snapshots e backup da VM

Uma vantagem da VM sobre o bare-metal é poder tirar **snapshots** antes de mudanças arriscadas (ex.: antes de atualizar o código, testar uma feature nova, ou mexer em configuração do sistema):

No virt-manager: **Detalhes da VM → Gerenciador de instantâneos (ícone de câmera na barra lateral) → +** para criar; para reverter, selecione o snapshot e clique em **Executar** (com a VM desligada).

Pela linha de comando:

```bash
virsh snapshot-create-as asac-servidor antes-da-atualizacao
virsh snapshot-list asac-servidor
virsh snapshot-revert asac-servidor antes-da-atualizacao
```

Para backup completo do disco da VM (fora do libvirt, para outra mídia):

```bash
sudo systemctl stop asac        # dentro da VM, evita corromper dados em uso
virsh shutdown asac-servidor    # do host
sudo cp /var/lib/libvirt/images/asac-servidor.qcow2 /caminho/de/backup/
virsh start asac-servidor
```

---

## Checklist de teste completo

- [ ] `br0` recebeu IP da rede local (`ip a show br0` no host)
- [ ] VM recebeu IP na mesma faixa da rede local (`ip a` na VM)
- [ ] Webcam aparece em `v4l2-ctl --list-devices` dentro da VM
- [ ] `uvicorn` sobe com HTTPS sem erro dentro da VM
- [ ] Celular acessa `https://<IP_DA_VM>:8000/ui/login.html` e o cadeado é aceito (rootCA instalado)
- [ ] Scanner de código de barras abre a câmera e decodifica um código real
- [ ] Serviço systemd sobrevive a `sudo systemctl restart asac` e a um reboot da VM (`sudo reboot` dentro da VM, aguardar subir, `systemctl status asac`)
- [ ] Snapshot criado após confirmar que tudo funciona, como ponto de restauração

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| virt-manager pede senha de root / não conecta | Usuário não está nos grupos `libvirt`/`kvm` | `sudo usermod -aG libvirt,kvm $USER` e fazer logout/login |
| VM não recebe IP da rede local | Bridge `br0` não foi criada corretamente, ou NIC da VM ainda aponta para "NAT" | Conferir `ip a show br0` no host; conferir se a NIC da VM está como "Bridge device: br0" |
| Webcam não aparece em `lsusb` na VM | Passthrough não foi anexado, ou dispositivo composto (áudio+vídeo) só teve uma parte anexada | Reconferir em Adicionar hardware → Host USB Device; verificar `dmesg` |
| Inferência YOLO muito lenta dentro da VM | CPU da VM não está em modo `host-passthrough` | Detalhes da VM → CPUs → Copiar configuração de CPU do host (requer VM desligada) |
| `status=203/EXEC` no `journalctl -u asac` | Caminhos do `asac.service` não batem com o clone dentro da VM, ou `.venv` não foi criado | Ver seção 8 acima e a tabela de troubleshooting do README principal |
| Celular não confia no certificado | `rootCA.pem` da VM não foi instalado no celular (é diferente do rootCA do host!) | Gerar o `rootCA.pem` de dentro da VM (`mkcert -CAROOT`) e reinstalar no celular |
