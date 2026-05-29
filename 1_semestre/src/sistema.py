import csv
import os

CAMINHO_CSV = os.path.join(os.path.dirname(__file__), "../data/dados.csv")


def carregar_dados(caminho):
    dados = []
    with open(caminho, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            if linha["datetime"].startswith("#"):
                continue
            dados.append({
                "datetime":             linha["datetime"],
                "geracao_solar_kwh":    float(linha["geracao_solar_kwh"]),
                "consumo_kwh":          float(linha["consumo_kwh"]),
                "reserva_bateria_pct":  float(linha["reserva_bateria_pct"]),
                "temp_externa_c":       float(linha["temp_externa_c"]),
                "temp_interna_c":       float(linha["temp_interna_c"]),
                "radiacao_msv":         float(linha["radiacao_msv"]),
                "oxigenio":             int(linha["oxigenio"]),
                "energia":              int(linha["energia"]),
                "comunicacao":          int(linha["comunicacao"]),
                "habitat":              int(linha["habitat"]),
                "pressao":              int(linha["pressao"]),
                "combustivel":          int(linha["combustivel"]),
            })
    return dados


def classificar_variavel(bateria, radiacao, temp_int, geracao_solar):
    alertas  = []
    criticos = []

    if bateria < 15:
        criticos.append("bateria_critica")
    elif bateria < 25:
        alertas.append("bateria_baixa")

    if radiacao > 1.0:
        criticos.append("radiacao_critica")
    elif radiacao > 0.8:
        alertas.append("radiacao_elevada")

    if temp_int < 5 or temp_int > 35:
        criticos.append("temperatura_critica")
    elif temp_int < 10 or temp_int > 30:
        alertas.append("temperatura_alerta")

    if geracao_solar > 200:
        alertas.append("inconsistencia_solar")

    return alertas, criticos


def diagnosticar(leitura, modulos):
    alertas, criticos = classificar_variavel(
        leitura["reserva_bateria_pct"],
        leitura["radiacao_msv"],
        leitura["temp_interna_c"],
        leitura["geracao_solar_kwh"],
    )

    for nome, mod in modulos.items():
        if not mod["status"]:
            criticos.append(f"falha_{nome}")

    if len(alertas) >= 2:
        criticos.append("multiplos_alertas")

    # CRITICO = modulo_falho OR (count_alertas >= 2) OR (radiacao > 1.0 AND NOT comunicacao)
    radiacao_critica = leitura["radiacao_msv"] > 1.0
    sem_comunicacao  = not modulos["comunicacao"]["status"]
    if radiacao_critica and sem_comunicacao:
        criticos.append("radiacao_critica")

    if criticos:
        return "CRITICO", alertas, criticos
    elif alertas:
        return "ALERTA", alertas, criticos
    else:
        return "NORMAL", alertas, criticos


RECOMENDACOES = {
    "bateria_baixa":       ("ALERTA",  "Bateria baixa",                "Reduzir consumo nao essencial e priorizar recarga"),
    "bateria_critica":     ("CRITICO", "Bateria critica",               "Desligar sistemas nao essenciais imediatamente"),
    "radiacao_elevada":    ("ALERTA",  "Radiacao elevada",              "Acionar blindagem e reduzir exposicao da tripulacao"),
    "radiacao_critica":    ("CRITICO", "Radiacao critica",              "Evacuar modulos expostos e acionar protocolo de emergencia"),
    "temperatura_alerta":  ("ALERTA",  "Temperatura interna em alerta", "Verificar sistema de climatizacao"),
    "temperatura_critica": ("CRITICO", "Temperatura interna critica",   "Acionar sistema de emergencia termico imediatamente"),
    "falha_oxigenio":      ("CRITICO", "Falha no oxigenio",             "Ativar reserva de oxigenio de emergencia"),
    "falha_energia":       ("CRITICO", "Falha na energia",              "Alternar para baterias de reserva"),
    "falha_comunicacao":   ("CRITICO", "Falha na comunicacao",          "Ativar radio de emergencia de baixa frequencia"),
    "falha_habitat":       ("CRITICO", "Falha no habitat",              "Verificar integridade estrutural e pressurizacao"),
    "falha_pressao":       ("CRITICO", "Falha na pressao",              "Acionar protocolo de despressurizacao controlada"),
    "falha_combustivel":   ("CRITICO", "Falha no combustivel",          "Suspender manobras orbitais imediatamente"),
    "inconsistencia_solar":("ALERTA",  "Inconsistencia no sensor solar","Recalibrar sensor de geracao solar"),
    "multiplos_alertas":   ("CRITICO", "Multiplos alertas simultaneos", "Acionar protocolo de crise geral da missao"),
}


def gerar_recomendacoes(alertas, criticos):
    causas = criticos + alertas
    vistas = set()
    recomendacoes = []
    for causa in causas:
        if causa in RECOMENDACOES and causa not in vistas:
            vistas.add(causa)
            recomendacoes.append(RECOMENDACOES[causa])
    recomendacoes.sort(key=lambda r: 0 if r[0] == "CRITICO" else 1)
    return recomendacoes


def organizar_estruturas(dados):
    lista_geracao  = [d["geracao_solar_kwh"]   for d in dados]
    lista_consumo  = [d["consumo_kwh"]          for d in dados]
    lista_bateria  = [d["reserva_bateria_pct"]  for d in dados]
    lista_radiacao = [d["radiacao_msv"]         for d in dados]
    lista_temp_int = [d["temp_interna_c"]       for d in dados]

    modulos = {
        "oxigenio": {
            "nome":         "Suporte a Vida - Oxigenio",
            "descricao":    "Fornecimento e monitoramento de oxigenio respiravel",
            "status":       bool(dados[-1]["oxigenio"]),
            "total_falhas": sum(1 for d in dados if not d["oxigenio"]),
        },
        "energia": {
            "nome":         "Energia - Paineis Solares",
            "descricao":    "Geracao de energia via paineis solares fotovoltaicos",
            "status":       bool(dados[-1]["energia"]),
            "total_falhas": sum(1 for d in dados if not d["energia"]),
        },
        "comunicacao": {
            "nome":         "Comunicacao - Link Terra",
            "descricao":    "Canal de comunicacao bidirecional com a Terra",
            "status":       bool(dados[-1]["comunicacao"]),
            "total_falhas": sum(1 for d in dados if not d["comunicacao"]),
        },
        "habitat": {
            "nome":         "Habitat - Modulo Principal",
            "descricao":    "Integridade estrutural e conforto da tripulacao",
            "status":       bool(dados[-1]["habitat"]),
            "total_falhas": sum(1 for d in dados if not d["habitat"]),
        },
        "pressao": {
            "nome":         "Pressao - Atmosfera Interna",
            "descricao":    "Controle da pressao atmosferica interna da estacao",
            "status":       bool(dados[-1]["pressao"]),
            "total_falhas": sum(1 for d in dados if not d["pressao"]),
        },
        "combustivel": {
            "nome":         "Combustivel - Propulsao",
            "descricao":    "Reserva de combustivel para manobras orbitais",
            "status":       bool(dados[-1]["combustivel"]),
            "total_falhas": sum(1 for d in dados if not d["combustivel"]),
        },
    }

    hierarquia = {
        "missao_gb": {
            "energia": {
                "geracao_solar":   lista_geracao[-1],
                "reserva_bateria": lista_bateria[-1],
            },
            "habitat": {
                "oxigenio":            modulos["oxigenio"]["status"],
                "temperatura_interna": lista_temp_int[-1],
                "pressao":             modulos["pressao"]["status"],
            }
        }
    }

    fila_alertas   = []
    pilha_criticos = []

    for d in dados:
        mod_temp = {k: {"nome": v["nome"], "status": bool(d[k])} for k, v in modulos.items()}
        status, alertas, criticos = diagnosticar(d, mod_temp)

        if status in ("ALERTA", "CRITICO"):
            fila_alertas.append({
                "datetime": d["datetime"],
                "tipo":     status,
                "motivos":  criticos + alertas,
            })

        if status == "CRITICO":
            pilha_criticos.append({
                "datetime": d["datetime"],
                "motivos":  criticos,
            })

    matriz_24h = []
    for d in dados[-6:]:
        matriz_24h.append([
            d["datetime"],
            d["geracao_solar_kwh"],
            d["consumo_kwh"],
            d["reserva_bateria_pct"],
            d["temp_interna_c"],
            d["radiacao_msv"],
        ])

    return (
        lista_geracao, lista_consumo, lista_bateria, lista_radiacao, lista_temp_int,
        modulos, hierarquia, fila_alertas, pilha_criticos, matriz_24h
    )


def regressao_linear(valores):
    n      = len(valores)
    x_vals = list(range(n))
    sum_x  = sum(x_vals)
    sum_y  = sum(valores)
    sum_xy = sum(x_vals[i] * valores[i] for i in range(n))
    sum_x2 = sum(x ** 2 for x in x_vals)

    a = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    b = (sum_y - a * sum_x) / n
    return a, b


def media_movel(valores, janela=6):
    suavizado = []
    for i in range(len(valores)):
        inicio = max(0, i - janela + 1)
        suavizado.append(sum(valores[inicio:i+1]) / (i - inicio + 1))
    return suavizado


def prever_bateria(lista_bateria, base=42, horizonte=12):
    base_vals = lista_bateria[-base:]
    suavizado = media_movel(base_vals, janela=6)
    a, b      = regressao_linear(suavizado)

    previsoes = []
    for i in range(1, horizonte + 1):
        x_futuro = base + i - 1
        y_prev   = max(0.0, min(100.0, round(a * x_futuro + b, 1)))
        previsoes.append(y_prev)

    return a, b, previsoes


def exibir_alertas_recentes(fila_alertas, n=10):
    print(f"\n--- ULTIMOS {n} EVENTOS EM ALERTA/CRITICO ---")
    for a in fila_alertas[-n:]:
        chave  = a["motivos"][0] if a["motivos"] else "-"
        rec    = RECOMENDACOES.get(chave)
        motivo = rec[1] if rec else chave
        MODOS = {
            "bateria_baixa":        "modo economia ativado",
            "bateria_critica":      "modo economia critico ativado",
            "radiacao_elevada":     "blindagem acionada",
            "radiacao_critica":     "protocolo de emergencia radiologica ativado",
            "temperatura_alerta":   "climatizacao verificada",
            "temperatura_critica":  "sistema termico de emergencia ativado",
            "falha_oxigenio":       "reserva de oxigenio ativada",
            "falha_energia":        "baterias de reserva ativadas",
            "falha_comunicacao":    "radio de emergencia ativado",
            "falha_habitat":        "protocolo de integridade estrutural ativado",
            "falha_pressao":        "despressurizacao controlada iniciada",
            "falha_combustivel":    "manobras orbitais suspensas",
            "inconsistencia_solar": "recalibracao de sensor iniciada",
            "multiplos_alertas":    "protocolo de crise geral ativado",
        }
        if chave in MODOS:
            motivo += f" -> {MODOS[chave]}"
        print(f"  [{a['tipo']}] {a['datetime']} - {motivo}")


def exibir_diagnostico_e_recomendacoes(leitura, modulos):
    status, alertas, criticos = diagnosticar(leitura, modulos)
    recomendacoes = gerar_recomendacoes(alertas, criticos)

    print(f"\n--- DIAGNOSTICO ATUAL ({leitura['datetime']}) ---")
    print(f"  Status: {status}")
    for c in criticos:
        rec = RECOMENDACOES.get(c)
        print(f"  [CRITICO] {rec[1] if rec else c}")
    for a in alertas:
        rec = RECOMENDACOES.get(a)
        print(f"  [ALERTA]  {rec[1] if rec else a}")

    print(f"\n--- RECOMENDACOES ---")
    if recomendacoes:
        for i, (nivel, causa, acao) in enumerate(recomendacoes, 1):
            print(f"  {i}. [{nivel}] {causa}: {acao}")
    else:
        print(f"  Missao operando normalmente. Nenhuma acao necessaria.")


def exibir_previsao(lista_bateria):
    a, b, previsoes = prever_bateria(lista_bateria)

    print(f"\n--- PREVISAO DE BATERIA (proximos 2 dias / 12 leituras) ---")
    print(f"  Metodo: media movel (janela=6) + regressao linear")
    print(f"  Regressao linear: y = {a:.4f}x + {b:.4f}")
    print(f"  Base: ultimas 42 leituras (7 dias)")
    print()

    alerta_disparado  = False
    critico_disparado = False

    for i, val in enumerate(previsoes, 1):
        horas = i * 4
        flag  = ""
        if val < 15:
            flag = " << CRITICO"
            critico_disparado = True
        elif val < 25:
            flag = " << ALERTA"
            alerta_disparado = True
        print(f"  +{horas:>3}h: {val:>5.1f}%{flag}")

    if critico_disparado:
        print(f"\n  [AVISO CRITICO] Bateria deve atingir nivel critico nas proximas 48h")
        print(f"  [RECOMENDACAO]  Desligar sistemas nao essenciais imediatamente")
    elif alerta_disparado:
        print(f"\n  [AVISO ALERTA] Bateria deve atingir nivel de alerta nas proximas 48h")
        print(f"  [RECOMENDACAO] Reduzir consumo nao essencial e priorizar recarga")
    else:
        print(f"\n  Bateria prevista dentro dos limites normais nas proximas 48h")


if __name__ == "__main__":
    dados = carregar_dados(CAMINHO_CSV)
    print(f"Leituras carregadas: {len(dados)}")

    (lista_geracao, lista_consumo, lista_bateria, lista_radiacao, lista_temp_int,
     modulos, hierarquia, fila_alertas, pilha_criticos, matriz_24h) = organizar_estruturas(dados)

    print(f"\n--- MODULOS ---")
    for k, v in modulos.items():
        print(f"  {v['nome']}: {'OK' if v['status'] else 'FALHA'} | Falhas historicas: {v['total_falhas']}")

    exibir_alertas_recentes(fila_alertas, n=10)

    print(f"\n--- PILHA DE CRITICOS (topo = mais recente) ---")
    for c in pilha_criticos[-3:]:
        motivo = RECOMENDACOES.get(c["motivos"][0])
        print(f"  {c['datetime']} - {motivo[1] if motivo else c['motivos'][0]}")

    exibir_diagnostico_e_recomendacoes(dados[-1], modulos)

    exibir_previsao(lista_bateria)

    print(f"\n--- MATRIZ 24H ---")
    print(f"  {'datetime':<18} {'solar':>8} {'consumo':>8} {'bateria':>8} {'t_int':>7} {'rad':>7}")
    for linha in matriz_24h:
        print(f"  {linha[0]:<18} {linha[1]:>8.2f} {linha[2]:>8.2f} {linha[3]:>8.1f} {linha[4]:>7.1f} {linha[5]:>7.3f}")