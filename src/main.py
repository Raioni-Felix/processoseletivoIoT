import machine
import time

# Otimização de emulação
machine.freq(80000000)

# Configuração de Pinos
PIN_LDR = 34
PIN_BTN = 12

# Configuração do ADC para o LDR (0 a 3.3V, resolução de 12 bits)
adc_ldr = machine.ADC(machine.Pin(PIN_LDR))
adc_ldr.atten(machine.ADC.ATTN_11DB)
adc_ldr.width(machine.ADC.WIDTH_12BIT) 

# Configuração do Botão com Pull-Up interno
btn_reset = machine.Pin(PIN_BTN, machine.Pin.IN, machine.Pin.PULL_UP)

# Variáveis de Estado
contador_pecas = 0
peca_bloqueando = False
tempo_inicio_bloqueio = 0
alerta_enviado = False

ultimo_estado_btn = 1
tempo_ultimo_debounce = 0

# Limiares e Constantes
# 800 lux (livre) -> ADC Baixo (< 2500)
# 50 lux (bloqueado) -> ADC Alto (> 3000)
LIMIAR_BLOQUEIO = 2500 
TEMPO_MICRO_PARADA_MS = 4000

# Inicialização exigida pelo CI
print("Contador de Producao Inicializado")

while True:
    tempo_atual = time.ticks_ms()
    
    # ---------------------------------------------------------
    # 1. Lógica do Botão (Reset de Turno com Debounce)
    # ---------------------------------------------------------
    estado_btn = btn_reset.value()
    
    # Detecta borda de subida (botão liberado) com debounce não-bloqueante de 50ms
    if estado_btn == 1 and ultimo_estado_btn == 0 and time.ticks_diff(tempo_atual, tempo_ultimo_debounce) > 50:
        contador_pecas = 0
        peca_bloqueando = False
        alerta_enviado = False
        print("Turno resetado com sucesso. Contadores zerados.")
        tempo_ultimo_debounce = tempo_atual
        
    ultimo_estado_btn = estado_btn

    # ---------------------------------------------------------
    # 2. Lógica de Detecção (LDR) e Micro-paradas
    # ---------------------------------------------------------
    valor_adc = adc_ldr.read()
    
    if valor_adc > LIMIAR_BLOQUEIO:
        # Estado: Peça bloqueando o feixe de luz (lux < 100)
        if not peca_bloqueando:
            peca_bloqueando = True
            tempo_inicio_bloqueio = tempo_atual
            alerta_enviado = False
        else:
            # Verifica gargalo/micro-parada se a peça ficar muito tempo sob o sensor
            if not alerta_enviado and time.ticks_diff(tempo_atual, tempo_inicio_bloqueio) >= TEMPO_MICRO_PARADA_MS:
                print("Alerta: Micro-parada detectada!")
                alerta_enviado = True
    else:
        # Estado: Linha livre (lux > 100)
        if peca_bloqueando:
            # Borda de subida (a peça passou completamente)
            peca_bloqueando = False
            contador_pecas += 1
            print(f"Peca detectada! Total: {contador_pecas}")
            alerta_enviado = False

    # Delay mínimo ajustado para evitar sobrecarga extrema no host do emulador
    time.sleep_ms(100)