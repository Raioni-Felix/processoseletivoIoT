# Relatório Técnico – Contador de Produção Não-Intrusivo

### Identificação do Candidato
- **Nome completo:** Raioni Felix de Sousa
- **GitHub:** Raioni-Felix

---

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
- **Abordagem Não-Bloqueante (Polling):** Optou-se pela verificação ativa contínua (*polling*) sem uso de `time.sleep()` longo. Isso assegura que o firmware reaja de forma imediata aos gatilhos disparados pelos cenários de teste automatizado (CI).
- **Debounce por Software:** Para a leitura do botão, implementou-se um atraso lógico de 50ms para descarte de ruídos de acionamento mecânico, garantindo que o evento de reset registre apenas uma execução por clique estável.
- **Desacoplamento de Estados:** A lógica de contagem foi separada da lógica de micro-paradas. A mesma obstrução física inicializa a análise de falha na esteira, mas não consolida a peça até que ela libere o sensor completamente (borda de subida).

---

## Resultados Obtidos
O sistema cumpre todos os requisitos definidos para a simulação:
- **Cenário 1 (Contagem):** O evento de passagem de caixa (`lux` de 800 para 50 e volta para 800) processa o incremento corretamente.
- **Cenário 2 (Micro-parada):** O travamento do sensor em `lux: 50` aciona o limite parametrizado e dispara adequadamente o alerta de parada.
- **Cenário 3 (Reset):** O acionamento estável do pino zera os contadores e limpa o flag de parada.
- A solução roda com êxito em todos os *steps* no pipeline de testes de integração contínua (GitHub Actions).