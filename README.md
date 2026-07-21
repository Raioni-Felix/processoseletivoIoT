# Relatório Técnico – Contador de Produção Não-Intrusivo

### Identificação do Candidato
- **Nome completo:** Raioni Felix de Sousa


## Visão Geral da Solução
O projeto consiste em um Contador de Produção Não-Intrusivo simulado no Wokwi. O sistema embarcado monitora a passagem de objetos em uma esteira através da variação de luminosidade captada por um sensor LDR. O firmware realiza a contagem das peças, detecta micro-paradas na linha de produção (gargalos) e permite o reset manual do turno através de um botão físico, emitindo logs e métricas via porta serial.

---

## Arquitetura do Sistema Embarcado
O firmware (`main.py`) opera através de um laço principal estritamente não-bloqueante, estruturado nas seguintes lógicas:
- **Temporização:** Utiliza `time.ticks_ms()` e `time.ticks_diff()` para gerenciar cronômetros de forma assíncrona, não interrompendo o fluxo do código.
- **Máquina de Estados LDR:** Avalia continuamente o canal ADC. Transita entre "Linha Livre" (ADC alto) e "Peça Bloqueando" (ADC baixo). A transição para bloqueio inicia o cronômetro de micro-parada; a transição de volta para linha livre consolida o incremento na contagem.
- **Máquina de Estados Botão:** Monitora o pino digital com validação de borda de descida acoplada a um temporizador de *debounce*.

---

## Componentes Utilizados na Simulação
Os componentes mapeados no `diagram.json` compreendem:
- **Microcontrolador:** ESP32 DevKit C v4, orquestrando todo o processamento lógico.
- **Sensor Óptico (id: `ldr1`):** LDR conectado ao pino analógico 34 (resolução 12-bit, atenuação 11dB). Monitora a obstrução do feixe de luz.
- **Botão de Reset (id: `btn1`):** Pushbutton conectado ao pino digital 12, configurado com resistor de *pull-up* interno, responsável por receber o comando do operador para reiniciar o turno.

---

## Decisões Técnicas Relevantes

- **Gerenciamento de Tempo Assíncrono (`time.ticks_ms`):** A substituição de rotinas de atraso por hardware (`time.sleep`) pelo monitoramento contínuo de *ticks* da CPU é fundamental. Funções bloqueantes paralisam a execução do laço principal, impedindo a amostragem simultânea de múltiplos sensores. No contexto do Wokwi CI, onde os eventos do LDR e do botão são injetados de forma determinística e em intervalos curtos (ex: 300ms a 500ms), qualquer bloqueio do microcontrolador resultaria na perda da janela de leitura e consequente falha do teste.
- **Arquitetura de Polling versus Interrupções (IRQ):** Optou-se pelo *polling* de alta frequência (limitado a um `sleep_ms(10)` para evitar picos de 100% de uso de CPU no simulador/host) em detrimento de interrupções de hardware. Em MicroPython, rotinas de tratamento de interrupção (ISR) possuem restrições severas sobre alocação de memória e uso de I/O (como a função `print()`, exigida pelo CI). O *polling* garante estabilidade no controle de fluxo e previne condições de corrida no acesso às variáveis globais de estado e temporização.
- **Configuração do ADC e Limiares:** A configuração da atenuação do LDR para 11dB (`ATTN_11DB`) expande o limite de leitura do conversor analógico-digital para cerca de 3.3V (tensão de operação do ESP32), evitando saturação do sinal luminoso. A resolução parametrizada em 12 bits (`WIDTH_12BIT`) provê um mapeamento de 0 a 4095. Isso permite estabelecer um limiar lógico central bem definido (2500) para distinguir com precisão o estado de esteira livre (alta luminosidade, ADC > 3000) do estado de objeto bloqueando o feixe (baixa luminosidade, ADC < 2500).
- **Controle Lógico por Análise de Borda (Edge Detection):** A máquina de estados condiciona a contagem de peças exclusivamente à borda de subida do sensor (transição do estado bloqueado para livre). Isso garante robustez: se um objeto obstruir a linha e parar sob o LDR, o sistema iniciará a contagem de micro-parada, mas não consolidará a contagem da peça até que ela tenha passado inteiramente, mitigando contagens espúrias.
- **Topologia do Botão (Pull-up Interno e Debounce por Software):** O pino digital do botão de reset utiliza a configuração `machine.Pin.PULL_UP`, aproveitando o resistor interno do microcontrolador e simplificando o esquemático (redução de componentes de hardware). Para tratar o ruído eletromecânico inerente a chaves tácteis, implementou-se um *debounce* lógico: a mudança de estado só é validada em uma borda de descida com espaçamento mínimo de 50ms desde a última transição lida, garantindo transição limpa sem uso de filtros RC externos.
---

## Resultados Obtidos
O sistema cumpre todos os requisitos definidos para a simulação:
- **Cenário 1 (Contagem):** O evento de passagem de caixa (`lux` de 800 para 50 e volta para 800) processa o incremento corretamente.
- **Cenário 2 (Micro-parada):** O travamento do sensor em `lux: 50` aciona o limite parametrizado e dispara adequadamente o alerta de parada.
- **Cenário 3 (Reset):** O acionamento estável do pino zera os contadores e limpa o flag de parada.
- A solução roda com êxito em todos os *steps* no pipeline de testes de integração contínua (GitHub Actions).