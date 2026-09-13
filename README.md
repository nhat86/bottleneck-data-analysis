# Optimisation de la gestion des données d'une boutique — BottleNeck

> Projet réalisé dans le cadre de la formation **Data Analyst — OpenClassrooms**.

Analyse des ventes et des stocks d'une boutique en ligne de vins et spiritueux à partir de trois sources de données hétérogènes (ERP, table de liaison, export WooCommerce).

## Problématique

BottleNeck dispose de données éclatées entre son ERP et son site web, avec des erreurs de qualité (prix négatifs, stocks incohérents, identifiants non alignés). Objectif : **rapprocher, nettoyer et analyser** ces données pour produire des indicateurs de pilotage.

## Résultats clés

| Indicateur | Valeur |
|---|---|
| Chiffre d'affaires total | ~143 700 € |
| Unités vendues | ~5 750 |
| Valorisation du stock | ~548 800 € |
| Stock dormant (sans aucune vente) | ~68 200 € |
| Part du catalogue générant 80 % des ventes | ~63 % du catalogue actif |

## Compétences démontrées

- **Data cleaning** : détection et correction d'anomalies (stocks négatifs, prix aberrants, statuts incohérents, doublons de SKU)
- **Jointures multi-sources** : réconciliation ERP ↔ table de liaison ↔ WooCommerce
- **Analyse exploratoire** : statistiques descriptives, détection d'outliers (Z-score)
- **Indicateurs métier** : CA par article, courbe de Pareto, rotation et valorisation de stock, taux de marge
- **Data visualisation** : Plotly (boxplots, histogrammes, bar charts), Seaborn (heatmap de corrélation)

## Stack technique

`Python` · `pandas` · `numpy` · `plotly` · `seaborn` · `matplotlib` · `Jupyter`

## Structure du projet

```
├── analyse_bottleneck.ipynb   # Notebook d'analyse (principal livrable)
├── data/                      # Fichiers sources (erp, liaison, web)
├── exports/                   # Table finale nettoyée et enrichie
├── requirements.txt
└── README.md
```

## Reproduction

```bash
pip install -r requirements.txt
jupyter notebook analyse_bottleneck.ipynb
```
