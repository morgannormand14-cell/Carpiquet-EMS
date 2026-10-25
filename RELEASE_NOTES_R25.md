# Carpiquet EMS — R25 dynamic control (prérelease alpha)

Version candidate : `v0.6.5-alpha.3.15-r25`
Branche source : `dev-alpha-3.15-phase3b-r25-dynamic-control`

## Changements
- Sélecteur R25 Simulation / Cycle réel.
- Session SolarFlow 2400 Pro Local HTTP, confirmation POST/GET et retour à zéro.
- Watchdog, gestion des erreurs réseau et verrouillage des transitions concurrentes.
- Préservation de l'exécuteur R24 des essais physiques temporisés.

## État des vérifications
- CI GitHub Actions R25 : exécution #16 verte sur le commit 2667e2a.
- Tests automatisés : simulations et vérifications d'invariants.
- **Non validé sur Home Assistant réel ni sur SolarFlow physique.**
- Les tests de concurrence ne prouvent pas l'absence de tout défaut en production.

## Conditions avant tout essai matériel
1. Sauvegarder la configuration Home Assistant et conserver une copie R24 réinstallable.
2. Installer la prérelease en environnement contrôlé et vérifier l'absence d'erreurs au chargement.
3. Vérifier les entités, les données SOC, le transport Local HTTP et le mode Simulation par défaut.
4. Ne passer en Cycle réel qu'après vérification des limites de puissance, du SOC minimum et de la possibilité d'arrêt indépendant.
5. Surveiller la consigne appliquée et le retour GET ; interrompre immédiatement au moindre écart.
6. Si le retour à zéro n'est pas confirmé, considérer l'appareil potentiellement actif, isoler par un moyen matériel sûr et ne pas relancer la session.
7. Contrôler arrêt, rechargement et redémarrage de Home Assistant avant toute utilisation prolongée.

## Limitations
- Prérelease de développement, non recommandée pour fonctionnement sans surveillance.
- Hyper 2000 non inclus dans la commande HTTP dynamique R25.
- Les validations physiques R24 ne valident pas automatiquement la session continue R25.
