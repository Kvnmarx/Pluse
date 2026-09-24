#!/bin/sh
# Abre el Hábitat de Madreperla conectado a Hermes (Mac: doble clic).
cd "$(dirname "$0")"
python3 puente/servidor.py
