# Monitoring et énergie (responsables : P5 pour le monitoring, P3 pour l'énergie)

## Monitoring
- **Prometheus** collecte : CPU/mémoire des containers (cAdvisor ou node-exporter),
  durée de chaque étape du pipeline (les `timings_ms` de metadata.json), requêtes/s sur le LB.
- **Grafana** : un tableau de bord avec ces courbes.
- **eBPF (bonus, cf. TP8)** : compter les paquets/s sur l'interface réseau du LB.

## Énergie
- Mesurer la consommation (RAPL : `/sys/class/powercap/intel-rapl*`, `powerstat`, `scaphandre`)
  pendant le traitement d'une **vidéo de référence** toujours la même.
- Comparer les gouverneurs CPU `powersave` / `schedutil` / `performance`.
- Comparer les choix : Whisper tiny vs base, YOLO via ONNX vs PyTorch, 1 image/s vs 1 image/2 s.
- Consigner les résultats dans un tableau (Watts moyens, durée, énergie = W × s) → argument pour le bonus.
