# WHITE PAPER - ORA CORE RAG

Version 1.0 - Avril 2026  
Repository: `TwinsProductionAI/ora-core-rag`  
Status: public RAG governance white paper

## Resume executif

ORA Core RAG est une couche de retrieval gouvernee pour l'ecosysteme ORA Core OS. Son role n'est pas de devenir une base documentaire generale ni un simple moteur de recherche. Son role est de fournir un pipeline local-first, auditable et borne, capable de recuperer des sources pertinentes, de proteger les frontieres entre canon public et donnees client, puis de livrer un contexte source-backed a un orchestrateur LLM.

Le principe central est: le RAG ne doit pas augmenter seulement la quantite d'information; il doit augmenter la fiabilite, la tracabilite et la separation des responsabilites. Sans gouvernance, un RAG peut amplifier la confusion: mauvais chunks, sources obsoletes, melange de tenants, surconfiance, ou reponses finales non verifiees.

ORA Core RAG formalise donc un `RAG Governor`: une couche qui controle l'index, les routes, les logs, la sensibilite client, le fanout et les exigences de verification.

## 1. Probleme vise

Les architectures RAG classiques rencontrent souvent quatre problemes:

1. Retrieval non gouverne: le systeme recupere du texte sans comprendre le risque de l'utiliser.
2. Contamination de contexte: documents clients, canon public et notes experimentales se melangent.
3. Audit faible: il devient difficile de savoir quelles sources ont influence une reponse.
4. Surconfiance: le LLM transforme des chunks partiels en certitudes finales.

ORA Core RAG repond a ces limites en separant explicitement: ingestion, index, route gate, fanout, audit, orchestration et generation finale.

## 2. Definition

ORA Core RAG est un moteur de retrieval local-first pour le canon ORA et les profils de gouvernance associes. Il peut:

- decouvrir et ingerer des sources publiques;
- indexer localement des contenus autorises;
- produire des traces d'audit;
- router les requetes par profil;
- appliquer des restrictions client via GLK route;
- limiter le fanout selon le risque;
- preparer un paquet de contexte pour un orchestrateur;
- refuser la contamination croisee entre tenants.

Il ne doit pas:

- devenir une memoire client globale;
- repondre comme generateur final autonome;
- melanger le canon ORA et les donnees client;
- masquer les incertitudes des sources;
- bypasser HGOV, H-NERONS ou Primordia lorsque le risque l'exige.

## 3. Architecture conceptuelle

```text
User query
  -> RAG Governor
  -> route policy + GLK tenant gate
  -> source registry
  -> ingestion / local index
  -> retrieval
  -> Neroflux fanout regulation
  -> evidence packet
  -> ORCHESTRATEUR_LLM
  -> HGOV / H-NERONS if needed
  -> final bounded answer
```

Le RAG Governor ne remplace pas le raisonnement. Il prepare un contexte propre, verifiable et limite.

## 4. Local-first comme choix de gouvernance

Le mode local-first reduit plusieurs risques:

- controle sur les fichiers indexes;
- audit plus simple;
- couts previsibles;
- reduction de l'exposition de donnees;
- possibilite de fonctionner sans infrastructure lourde.

Le choix Python + SQLite FTS5 est volontaire: il favorise la simplicite, l'inspection et la portabilite. Une architecture plus lourde peut etre ajoutee plus tard, mais le noyau doit rester comprehensible.

## 5. Separation canon / client

Une regle fondatrice d'ORA Core RAG est que le canon ORA et les donnees client ne doivent pas se confondre. Le canon peut etre indexe comme reference publique. Les donnees client doivent rester dans des routes separees, avec un identifiant ou un profil qui limite explicitement l'acces.

Cette separation soutient trois objectifs:

1. Eviter qu'un client modifie ou contamine le coeur ORA.
2. Eviter qu'un client voie des documents qui ne lui appartiennent pas.
3. Permettre un audit clair des sources utilisees.

## 6. GLK route gate

Le GLK route gate sert de frontiere logique. Il ne doit pas etre traite comme un simple tag decoratif. Il doit agir comme condition d'acces: une requete client doit posseder une route valide avant d'activer un index ou un registre specifique.

Dans une version industrielle, ce mecanisme pourrait etre renforce par:

- authentification;
- permissions par workspace;
- journaux d'acces;
- chiffrement des secrets;
- politiques de retention;
- revocation par client.

## 7. Fanout regulation

Un RAG mal controle peut interroger trop de sources, augmenter les couts, ralentir les reponses et introduire plus de bruit. Neroflux intervient comme regulateur de fanout: selon la sensibilite client, le risque de permission, le nombre d'agents ou la densite du contexte, le systeme peut reduire `top_k`, limiter les routes et exiger une verification supplementaire.

Le principe n'est pas de chercher plus, mais de chercher mieux.

## 8. Audit trace

L'audit minimal doit permettre de repondre a ces questions:

- Quelle requete a ete formulee?
- Quelle route a ete utilisee?
- Quels documents ont ete consultes?
- Quels chunks ont ete recuperes?
- Quel score ou rang leur a ete attribue?
- Quelle politique a limite ou autorise le retrieval?
- Quel paquet a ete transmis a l'orchestrateur?

Sans cette trace, le RAG devient une boite noire. Avec elle, il devient une couche defendable.

## 9. Relation avec H-NERONS et HGOV

ORA Core RAG ne valide pas seul la verite finale. Il recupere du contexte. H-NERONS peut ensuite qualifier les claims verifiables. HGOV garde l'autorite epistemique sur la prudence, le risque et l'assertivite.

La chaine saine est donc:

```text
RAG trouve -> H-NERONS qualifie -> HGOV borne -> LLM formule
```

Un chunk pertinent n'est pas automatiquement une preuve complete. Un resultat de recherche n'est pas automatiquement une autorisation d'affirmer.

## 10. Cas d'usage

ORA Core RAG est utile pour:

- interroger le canon ORA avec citations;
- construire un assistant documentaire local;
- produire des paquets de contexte pour un orchestrateur;
- separer plusieurs clients dans un environnement PME;
- verifier que les reponses restent reliees aux documents autorises;
- preparer une evolution vers Qdrant, Chroma, FAISS ou autre backend vectoriel sans perdre la gouvernance.

## 11. Limites

Le systeme ne promet pas:

- une comprehension parfaite des documents;
- une preuve absolue de verite;
- une securite enterprise complete sans couches supplementaires;
- une precision equivalente a une revue humaine expert;
- une absence de biais dans les sources.

Il faut le presenter comme un moteur de retrieval gouverne, pas comme une autorite finale.

## 12. Roadmap conseillee

1. Stabiliser les manifests de sources.
2. Ajouter des tests de non-contamination client.
3. Ajouter des benchmarks de retrieval sur questions ORA connues.
4. Produire des traces d'audit lisibles par humain.
5. Connecter proprement H-NERONS pour claims dynamiques.
6. Ajouter une abstraction pour backend vectoriel optionnel.
7. Documenter un profil PME local deployable.

## Conclusion

ORA Core RAG est une couche de gouvernance documentaire. Sa valeur ne vient pas seulement de recuperer des documents; elle vient de savoir quels documents il a le droit de recuperer, pourquoi, pour qui, avec quelle trace et avec quelle limite d'assertivite.

Dans l'ecosysteme ORA, il occupe une place critique: il relie le canon, les sources, les clients et l'orchestrateur sans transformer le retrieval en chaos contextuel.
