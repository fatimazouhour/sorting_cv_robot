"""
Teste de deteccao com YOLO11s e a webcam do computador.

Instalacao:
    pip install ultralytics opencv-python

Uso:
    python teste_deteccao.py
    python teste_deteccao.py --camera 1 --conf 0.4

Teclas:
    q ou ESC : sair
    s        : salvar o frame atual (com as deteccoes) na pasta capturas/
    a        : alternar entre "so classes escolhidas" e "todas as 80 classes"
    + / -    : aumentar / diminuir o limiar de confianca
"""

import argparse
import os
import time

import cv2
from ultralytics import YOLO

# IDs do COCO: 32 = sports ball, 46 = banana, 47 = apple, 49 = orange
CLASSES_ALVO = [32, 46, 47, 49]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--camera", type=int, default=0, help="indice da webcam (0, 1, ...)")
    p.add_argument("--modelo", default="yolo11s.pt", help="pesos do modelo")
    p.add_argument("--conf", type=float, default=0.5, help="limiar de confianca inicial")
    p.add_argument("--largura", type=int, default=1280)
    p.add_argument("--altura", type=int, default=720)
    return p.parse_args()


def main():
    args = parse_args()

    model = YOLO(args.modelo)  # baixa os pesos automaticamente na primeira vez

    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.largura)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.altura)
    if not cap.isOpened():
        raise SystemExit(f"Nao foi possivel abrir a camera {args.camera}. Tente --camera 1.")

    os.makedirs("capturas", exist_ok=True)

    conf = args.conf
    so_alvo = True
    ultimo_tempo = time.time()
    fps = 0.0

    print("Camera aberta. Teclas: q = sair, s = salvar, a = todas as classes, +/- = confianca")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Falha ao ler frame da camera.")
            break

        resultados = model(
            frame,
            classes=CLASSES_ALVO if so_alvo else None,
            conf=conf,
            verbose=False,
        )[0]

        imagem = resultados.plot()

        # Lista as deteccoes no terminal
        deteccoes = []
        for box in resultados.boxes:
            nome = model.names[int(box.cls)]
            confianca = float(box.conf)
            cx, cy = box.xywh[0][:2].tolist()
            deteccoes.append(f"{nome} {confianca:.2f} ({cx:.0f},{cy:.0f})")
        if deteccoes:
            print(" | ".join(deteccoes))

        # FPS suavizado
        agora = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(agora - ultimo_tempo, 1e-6))
        ultimo_tempo = agora

        modo = "classes alvo" if so_alvo else "todas as classes"
        info = f"FPS {fps:.1f} | conf {conf:.2f} | {modo}"
        cv2.putText(imagem, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Teste de deteccao (q para sair)", imagem)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla in (ord("q"), 27):
            break
        elif tecla == ord("s"):
            nome_arquivo = os.path.join("capturas", f"captura_{int(time.time())}.jpg")
            cv2.imwrite(nome_arquivo, imagem)
            print(f"Salvo: {nome_arquivo}")
        elif tecla == ord("a"):
            so_alvo = not so_alvo
        elif tecla in (ord("+"), ord("=")):
            conf = min(0.95, conf + 0.05)
        elif tecla in (ord("-"), ord("_")):
            conf = max(0.05, conf - 0.05)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()