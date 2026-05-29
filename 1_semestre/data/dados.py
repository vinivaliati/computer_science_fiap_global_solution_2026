import csv
import random
from datetime import datetime, timedelta

random.seed(42)

INICIO = datetime(2026, 1, 1, 0, 0)
FIM    = datetime(2026, 7, 1, 0, 0)
INTERVALO = timedelta(hours=4)

INDICE_INCONSISTENCIA = 50
PROB_FALHA_MODULO     = 0.006

def gerar_perfil_mes(mes):
    if mes == 1:
        return {"radiacao": (0.05, 0.30), "bateria": (65, 85), "solar": (70, 90), "temp_ext": (-120, -80)}
    elif mes == 2:
        return {"radiacao": (0.10, 0.35), "bateria": (60, 80), "solar": (65, 85), "temp_ext": (-130, -90)}
    elif mes == 3:
        return {"radiacao": (0.10, 0.40), "bateria": (58, 78), "solar": (60, 80), "temp_ext": (-140, -100)}
    elif mes == 4:
        return {"radiacao": (0.15, 0.45), "bateria": (52, 72), "solar": (55, 75), "temp_ext": (-150, -110)}
    elif mes == 5:
        return {"radiacao": (0.20, 0.55), "bateria": (45, 68), "solar": (45, 65), "temp_ext": (-160, -120)}
    else:
        return {"radiacao": (0.25, 0.65), "bateria": (38, 60), "solar": (35, 55), "temp_ext": (-170, -130)}

leituras = []
atual = INICIO
idx   = 0

while atual < FIM:
    mes  = atual.month
    hora = atual.hour
    perfil = gerar_perfil_mes(mes)

    if 6 <= hora <= 18:
        fator_hora = 1.0 - abs(hora - 12) / 6.0
        solar = round(random.uniform(*perfil["solar"]) * fator_hora, 2)
    else:
        solar = round(random.uniform(0, 5), 2)

    if idx == INDICE_INCONSISTENCIA:
        solar = 980.0

    consumo  = round(random.uniform(40, 60), 2)
    bateria  = round(random.uniform(*perfil["bateria"]), 1)
    temp_ext = round(random.uniform(*perfil["temp_ext"]), 1)
    temp_int = round(random.uniform(19, 26), 1)
    radiacao = round(random.uniform(*perfil["radiacao"]), 3)

    def status(p=PROB_FALHA_MODULO):
        return 0 if random.random() < p else 1

    leituras.append([
        atual.strftime("%Y-%m-%d %H:%M"),
        solar, consumo, bateria,
        temp_ext, temp_int, radiacao,
        status(), status(), status(), status(), status(), status(),
    ])

    idx  += 1
    atual += INTERVALO

cabecalho = [
    "datetime",
    "geracao_solar_kwh", "consumo_kwh", "reserva_bateria_pct",
    "temp_externa_c", "temp_interna_c", "radiacao_msv",
    "oxigenio", "energia", "comunicacao", "habitat", "pressao", "combustivel",
]

with open("dados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(cabecalho)
    writer.writerows(leituras)
