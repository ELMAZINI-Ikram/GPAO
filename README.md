# GPAO : Gestion de Production Assistée par Ordinateur

**Application web de pilotage de la production pour un atelier électromécanique** : du programme directeur de production au calcul des besoins (MRP), en passant par la charge machine, l'ordonnancement des ordres de fabrication, la gestion des stocks et la maintenance.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![Chart.js](https://img.shields.io/badge/Chart.js-visualisation-ff6384)
![GPAO](https://img.shields.io/badge/Production-MRP%20%7C%20MPS%20%7C%20CBN-orange)

> 🇬🇧 *Production planning and control web application (MRP II) for an electromechanical workshop: master production schedule, time-phased MRP, EOQ and ABC inventory management, load vs. capacity analysis, interactive Gantt scheduling, maintenance management and role-based access.*

---

## Sommaire

- [Contexte et problématique](#contexte-et-problématique)
- [Solution](#solution)
- [Aperçu](#aperçu)
- [Modules de production](#modules-de-production)
- [Pilotage en temps réel](#pilotage-en-temps-réel)
- [Gestion des rôles](#gestion-des-rôles)
- [Architecture](#architecture)
- [Installation](#installation)
- [Limites et perspectives](#limites-et-perspectives)
- [Compétences mobilisées](#compétences-mobilisées)
- [Équipe](#équipe)

---

## Contexte et problématique

Dans un atelier de production, la planification repose souvent sur des tableurs dispersés : les besoins en composants sont calculés à la main, la charge des machines est mal connue et les retards ne sont détectés qu'une fois constatés. Résultat : ruptures de stock, surstockage, goulots d'étranglement et dates de livraison non tenues.

**Enjeu :** centraliser la planification et le suivi de la production dans un outil unique, qui applique les méthodes de la GPAO (MRP II) et rend visibles en continu l'état des machines, des stocks et des ordres de fabrication.

## Solution

```
Commandes clients ─► Programme directeur (MPS) ─► Calcul des besoins nets (CBN / MRP)
        ─► Ordres de fabrication & d'achat ─► Charge / capacité machines
        ─► Ordonnancement (Gantt) ─► Suivi de production, stocks et maintenance
```

## Aperçu

<!-- Ajouter les captures d'écran dans un dossier docs/ puis décommenter :
![Tableau de bord](docs/dashboard.png)
![Diagramme de Gantt](docs/gantt.png)
![Calcul MRP](docs/mrp.png)
-->

*Captures d'écran à venir.*

## Modules de production

| Module | Contenu |
|--------|---------|
| **Programme directeur (MPS)** | Besoins bruts par période, lancements décalés |
| **CBN / MRP temporel** | Calcul des besoins nets par semaine, prise en compte des délais d'obtention (lead time), lancement décalé automatique |
| **Gestion des stocks** | Stock de sécurité, point de commande, quantité économique de commande (**EOQ**), classification **ABC**, alertes automatiques |
| **Charge et capacité** | Charge par machine, comparaison charge / capacité, identification des goulots d'étranglement |
| **Ordres de fabrication (OF)** | Génération automatique à partir des commandes confirmées, suivi des ordres de travail (OT), **Gantt interactif** avec filtres et statuts |
| **Maintenance** | Tickets de maintenance corrective, maintenance préventive planifiée, pièces de rechange, impact sur la disponibilité machine |
| **Achats et réceptions** | Commandes fournisseurs, factures, réceptions en magasin |

## Pilotage en temps réel

- Tableau de bord avec indicateurs clés (KPI)
- État des machines mis à jour en continu
- Rafraîchissement automatique des tableaux de bord (30 à 60 secondes)
- Alertes visuelles de production et graphiques des décalages de planning
- Interface responsive (ordinateur, tablette, mobile), thème clair ou sombre

## Gestion des rôles

| Rôle | Périmètre |
|------|-----------|
| **ADMIN** | Accès complet |
| **DIRECTOR** | Vue d'ensemble et rapports |
| **OPERATOR** | Production, OF / OT, machines, Gantt |
| **BUYER** | Achats fournisseurs, factures |
| **STOREKEEPER** | Réceptions, gestion des stocks |

## Architecture

```
gpao_v4_complete/
├── core/                     # Application principale
│   ├── models.py             # Modèles de données (articles, nomenclatures, OF, machines…)
│   ├── views.py              # Vues et logique métier
│   ├── urls.py               # Routes
│   └── utils.py              # Algorithmes : MRP, EOQ, ABC…
├── templates/                # Interfaces HTML
├── static/                   # CSS, JavaScript, images
├── gpao/                     # Configuration Django
│   ├── settings.py
│   └── urls.py
├── start_gpao.py             # Script de lancement automatisé
└── manage.py
```

**Stack :** Python · Django 5.2 · SQLite · Bootstrap 5 · Chart.js

## Installation

**Prérequis :** Python 3.11 ou supérieur.

```powershell
git clone https://github.com/ELMAZINI-Ikram/GPAO.git
cd GPAO

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo     # Données de démonstration
python manage.py runserver
```

Ou en une seule commande : `python start_gpao.py`

> Si PowerShell bloque l'activation de l'environnement virtuel : `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

L'application est accessible sur **http://127.0.0.1:8000**. La commande `seed_demo` crée un jeu de données de démonstration et un compte administrateur (`admin` / `admin123`), à modifier en dehors d'un usage de test.

## Limites et perspectives

Le moteur MRP est conçu dans une optique pédagogique et opérationnelle ; il ne remplace pas un outil de planification avancée (APS). Pistes d'évolution :

- Ordonnancement à capacité finie
- Connexion aux données machines réelles (capteurs, MES)
- Calcul d'indicateurs de performance comme le TRS / OEE

## Compétences mobilisées

| Domaine | Compétences |
|---------|-------------|
| **Planification de la production** | MPS, MRP / CBN, lancement décalé, ordonnancement Gantt |
| **Gestion des stocks** | EOQ, stock de sécurité, point de commande, classification ABC |
| **Performance industrielle** | Analyse charge / capacité, détection des goulots d'étranglement |
| **Maintenance** | Maintenance préventive et corrective, disponibilité des équipements |
| **Digitalisation industrielle** | Traduction de processus de production en application métier |
| **Développement** | Python, Django, modélisation de données, contrôle d'accès par rôles |
| **Travail en équipe** | Projet collaboratif réalisé à trois |

## Équipe

Projet réalisé dans le cadre du module de GPAO par trois élèves ingénieur(e)s en Transformation Digitale Industrielle — ENSA Béni Mellal :

- **Ikram ELMAZINI** — [@ELMAZINI-Ikram](https://github.com/ELMAZINI-Ikram)
- **Loubna ECH-CHOKHMANY** — [@LOUBNA-ECH-CHOKHMANY](https://github.com/pseudo-github)
- **N.PHILIPPE** — [@N.PHILIPPE](https://github.com/pseudo-github)
