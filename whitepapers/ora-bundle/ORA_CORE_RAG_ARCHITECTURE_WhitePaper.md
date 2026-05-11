# ORA_CORE_RAG_ARCHITECTURE White Paper

## Navigation du bundle

- Index global du bundle: `README_whitepaper_bundle.md`
- White paper principal ORA Core OS et ORA RAG: `ORA_CORE_OS_ORA_RAG_MODULAR_ARCHITECTURE_WhitePaper.md`

## 1. Position

`ORA_CORE_RAG` est la couche de retrieval canonique de l’écosystème ORA.

Son rôle n’est pas de remplacer le raisonnement, ni de devenir une mémoire générale. Son rôle est de produire un contexte récupéré, borné, traçable et gouverné pour les couches d’orchestration et de décision.

La formule la plus courte est la suivante:

`retrieval gouverné -> paquet d’évidence -> orchestration -> validation -> réponse`

## 2. Problème architectural

Un système RAG mal structuré mélange souvent cinq responsabilités:

- ingestion
- indexation
- routage
- contrôle d’accès
- formulation finale

Quand ces couches se confondent, le système devient difficile à auditer. Il sait retrouver du texte, mais il ne sait plus dire:

- ce qu’il a lu
- pourquoi il l’a lu
- si la source était autorisée
- si le contexte était suffisant
- si le résultat peut soutenir une affirmation

`ORA_CORE_RAG` existe pour séparer ces responsabilités.

## 3. Principe directeur

Le retrieval ne décide pas seul du vrai.

Il prépare un contexte source-backed, mais laisse:

- l’évaluation du claim à `H-NERONS` si nécessaire
- la prudence et les bornes d’assertion à `HGOV`
- la synthèse finale à la couche d’orchestration et au LLM

Le principe de base peut donc s’écrire ainsi:

`RAG trouve`
`H-NERONS qualifie`
`HGOV borne`
`ORCHESTRATEUR_LLM assemble`

## 4. Chaîne interne

L’architecture d’`ORA_CORE_RAG` peut être décrite en huit étapes:

1. **Intake**  
   La requête arrive avec un niveau de risque, un contexte, et éventuellement une route client.

2. **Route Gate**  
   Le système vérifie si la requête a le droit d’accéder à un corpus donné.

3. **Registry Check**  
   Les sources disponibles et leur statut sont identifiés.

4. **Retrieval Plan**  
   Le système détermine quelles sources interroger et avec quelle profondeur.

5. **Fanout Regulation**  
   `Neroflux` réduit ou étend le fanout selon la pression, la sensibilité et le risque.

6. **Evidence Packet**  
   Les résultats sont agrégés dans un paquet traçable: source, chunk, score, route, audit.

7. **Governance Handoff**  
   Le paquet est transmis à la couche d’orchestration, puis à `HGOV` ou `H-NERONS` si nécessaire.

8. **Bounded Answer**  
   La réponse finale doit rester compatible avec les preuves récupérées et leurs limites.

## 5. Frontière canon / client

L’une des propriétés les plus importantes de l’architecture est la séparation entre:

- le canon ORA
- les corpus clients
- les sources expérimentales

Cette frontière ne doit pas être une simple convention documentaire. Elle doit être une propriété du système.

Concrètement:

- le canon ORA peut être indexé comme référence publique
- les données client doivent rester sur des routes séparées
- les environnements sensibles doivent exiger une route valide avant toute activation de corpus
- aucune donnée client ne doit contaminer silencieusement l’index canonique

Cette règle est plus importante que la performance brute.

## 6. Route Gate et isolation

Le `GLK route gate` sert de frontière logique entre les espaces documentaires.

Son rôle est double:

- empêcher l’accès non autorisé à un corpus
- rendre explicite la provenance documentaire du paquet de retrieval

Dans une architecture plus large, cette porte logique peut être renforcée par:

- authentification
- permissions par workspace
- journalisation d’accès
- rétention
- révocation

Mais même dans sa forme simple, le route gate pose déjà la règle décisive: un corpus n’est pas interrogé seulement parce qu’il existe; il est interrogé parce qu’une route valide l’autorise.

## 7. Fanout comme décision de risque

Le `fanout` ne doit pas être traité comme un simple paramètre de rappel documentaire.

Interroger trop de sources peut:

- ralentir le système
- augmenter le bruit
- élargir l’incertitude
- accroître le risque de mélange de corpus

Dans `ORA_CORE_RAG`, le fanout est donc régulé par contexte. `Neroflux` peut réduire `top_k`, plafonner le nombre de corpus, ou durcir la nécessité de validation.

Le système cherche ainsi non pas le maximum de texte, mais le minimum de contexte suffisant.

## 8. Audit minimal

Une couche RAG gouvernée doit toujours pouvoir reconstruire son propre geste.

L’audit minimal devrait inclure:

- la requête
- la route
- les sources consultées
- les chunks retenus
- le score ou le rang
- les limites appliquées
- le paquet transmis en sortie

Sans cela, le retrieval produit du contexte mais pas de responsabilité.

## 9. Invariants d’architecture

`ORA_CORE_RAG` tient si ces invariants restent vrais:

- le retrieval ne répond pas seul
- le canon et le client ne se mélangent pas
- les routes documentaires restent explicites
- l’audit reste reconstructible
- le fanout reste gouverné
- la réponse finale n’upgrade pas un chunk en vérité sans couche d’évaluation

Si l’un de ces invariants tombe, la qualité perçue peut rester correcte quelque temps, mais l’architecture a déjà commencé à dériver.

## 10. Relation avec ORA Core OS

`ORA_CORE_RAG` n’est pas une brique extérieure collée à ORA Core OS.

Il prolonge directement plusieurs principes du noyau:

- hiérarchie des couches
- prudence sur les claims
- traçabilité
- séparation des rôles
- refus de l’implicite silencieux

En ce sens, `ORA_CORE_RAG` n’est pas seulement un moteur de recherche local. C’est la forme documentaire de la gouvernance ORA.

## 11. Limites

`ORA_CORE_RAG` ne garantit pas:

- qu’un document est vrai parce qu’il est indexé
- qu’un chunk est suffisant parce qu’il est pertinent
- qu’une réponse est légitime parce qu’elle cite une source
- qu’un système local-first est automatiquement sécurisé

Il faut donc le comprendre comme une couche de retrieval gouvernée, pas comme une autorité finale.

## 12. Conclusion

La force de `ORA_CORE_RAG` ne vient pas seulement de sa capacité à retrouver des documents. Elle vient de sa capacité à faire du retrieval une opération responsable, route-aware, séparable, auditable et compatible avec une chaîne de gouvernance plus large.

Dans l’architecture ORA, il occupe une fonction précise: rendre le contexte récupéré utilisable sans laisser la couche documentaire dissoudre la hiérarchie de vérité.