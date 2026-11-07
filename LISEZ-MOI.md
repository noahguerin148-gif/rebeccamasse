# Site de Rébecca Massé, artiste peintre

Nouvelle version de www.rebeccamasse.com : 128 œuvres en 7 séries, classées aussi par thèmes bibliques, avec la biographie, les expositions et le mémoire de maîtrise. Le site ne dépend plus de Wix. Toutes les photos sont dans le projet.

Le contenu (œuvres, séries, thèmes, page À propos) est rangé dans de petits fichiers de données, et un script construit le site à partir de ces fichiers. Une fois sur GitHub, le site se reconstruit et se republie tout seul à chaque modification. L'hébergement sur GitHub Pages est gratuit.

## Si tu as reçu plusieurs fichiers zip

Le projet est livré en quatre zips pour respecter les limites d'envoi : le projet, deux zips de photos et le mémoire. **Extrais-les tous au même endroit.** Chacun contient un dossier `rebeccamasse-site`, et les quatre se combinent en un seul dossier complet.

## Voir le site sur l'ordinateur

Clic droit sur `apercu.ps1` > *Exécuter avec PowerShell*. Le script installe Pillow au besoin, construit le site et l'ouvre dans le navigateur. Il faut Python ; s'il manque : `winget install Python.Python.3.12`.

Sans le script : `pip install Pillow`, puis `python outils\construire.py`, puis ouvrir `_site\index.html`.

## Organisation du projet

| Dossier ou fichier | Rôle |
|---|---|
| `contenu/oeuvres/` | Un fichier par œuvre : titre, photo, série, thèmes, position, technique, dimensions, année |
| `contenu/series/` | Les séries : nom, adresse de la page, ordre, affichée ou masquée |
| `contenu/themes/` | Les thèmes : Moïse, L'Arbre de la vie, Jonas, La Pêche miraculeuse, Noé, L'Agneau de Dieu, Abraham |
| `contenu/apropos.json` | Biographie, expositions et mémoire de maîtrise |
| `contenu/site.json` | Réglages : lien Facebook, clé du formulaire de contact |
| `originaux/` | Les photos des œuvres (2000 pixels maximum ; les vignettes sont générées) |
| `statique/` | Mise en page (CSS), JavaScript, polices, mémoire en PDF, images du site |
| `outils/construire.py` | Construit le site dans `_site/` |
| `apercu.ps1` | Construit le site et l'ouvre dans le navigateur |
| `.github/workflows/publier.yml` | Fait construire et publier le site par GitHub à chaque modification |
| `.pages.yml` | Les formulaires de Pages CMS |

---

## Mise en ligne (à faire une seule fois)

### 1. Mettre le projet sur GitHub

Crée un compte GitHub et un dépôt **public** vide nommé `rebeccamasse`. Ensuite, dans PowerShell, dans le dossier du projet :

```powershell
git init
git add .
git commit -m "Nouveau site"
git branch -M main
git remote add origin https://github.com/TONCOMPTE/rebeccamasse.git
git push -u origin main
```

### 2. Activer GitHub Pages

Dans le dépôt : *Settings > Pages*, et sous *Source*, choisis **GitHub Actions**. L'onglet *Actions* montre la construction en cours. Une à deux minutes plus tard, le site est en ligne à `https://TONCOMPTE.github.io/rebeccamasse/`.

### 3. Activer le formulaire de contact

Crée un compte gratuit sur https://web3forms.com avec l'adresse où Rébecca veut recevoir les messages (250 messages par mois). Copie la clé (*Access Key*) dans `contenu/site.json`, à la place de `REMPLACER_PAR_VOTRE_CLE_WEB3FORMS`. On peut aussi la coller dans Pages CMS, sous *Réglages du site*.

### 4. Brancher rebeccamasse.com

Dans GitHub (*Settings > Pages > Custom domain*), entre `www.rebeccamasse.com`. Ensuite, chez Wix : *Domaines* > *Domain Actions* > *Manage DNS Records*. Supprime les anciens enregistrements A et CNAME, puis ajoute :

| Type | Hôte | Valeur |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `TONCOMPTE.github.io` |

La propagation peut prendre jusqu'à 48 h. Quand GitHub confirme le domaine, coche *Enforce HTTPS*.

Résilie le forfait Premium de Wix seulement quand tout fonctionne sur rebeccamasse.com, et garde l'abonnement du domaine actif. Les anciennes adresses (`/gallery`, `/hotel-de-glace`, `/figuratif`, `/copie-de-portfolio`) redirigent vers les nouvelles pages.

### 5. Brancher le formulaire d'ajout (Pages CMS)

Pages CMS est un outil libre (licence MIT) qui affiche des formulaires par-dessus le dépôt GitHub.

1. Va sur https://app.pagescms.org et connecte-toi avec GitHub.
2. Installe l'application GitHub de Pages CMS sur le dépôt `rebeccamasse`.
3. Ouvre le dépôt : les sections *Œuvres*, *Séries*, *Thèmes*, *Page À propos* et *Réglages du site* apparaissent.

Pour que Rébecca puisse l'utiliser elle-même, elle se crée un compte GitHub. Tu l'ajoutes ensuite comme collaboratrice du dépôt (*Settings > Collaborators*).

---

## Ajouter un tableau

### Avec le formulaire

1. Dans Pages CMS, ouvre *Œuvres* et crée une nouvelle entrée.
2. Téléverse la photo (JPG ou PNG, idéalement 2000 pixels de large ou plus).
3. Remplis le titre, choisis la série et, au besoin, un ou plusieurs thèmes. Technique, dimensions et année sont facultatives et s'affichent sous l'œuvre.
4. *Position dans la série* : 1 pour la mettre en premier, ou vide pour la mettre à la fin.
5. Enregistre. Le site se republie tout seul en une à deux minutes.

### À la main

1. Dépose la photo dans `originaux/`, par exemple `originaux/bible/25-arbre-de-vie.jpg`.
2. Crée le fichier `contenu/oeuvres/bible-25-arbre-de-vie.json` :

```json
{
  "titre": "L'Arbre de la vie",
  "image": "/originaux/bible/25-arbre-de-vie.jpg",
  "serie": "la-bible-source-de-poesie",
  "themes": ["arbre-de-vie"],
  "ordre": 25,
  "technique": "Acrylique et faux vitrail sur bois",
  "dimensions": "40 × 50 cm",
  "annee": "2026"
}
```

3. Lance `apercu.ps1` pour vérifier, puis `git add .`, `git commit -m "Nouvelle œuvre"` et `git push`.

Les séries à utiliser dans `"serie"` : `la-bible-source-de-poesie`, `la-belle-province`, `cupcakes`, `chiens-et-chats`, `fleurs`, `mes-debuts`, `objets-peints`.

## Masquer une série

Dans Pages CMS, sous *Séries*, décoche *Afficher la série sur le site* (ou mets `"visible": false` dans le fichier de la série). La série et ses œuvres disparaissent du site sans que rien ne soit effacé.

---

## Ce qui a été fait avec les photos de Wix

L'export Wix contenait 150 fichiers. On y trouvait les 79 œuvres de l'ancien site, plusieurs œuvres qui n'étaient sur aucune page, des doublons et quelques photos qui ne sont pas des œuvres.

- **Œuvres ajoutées aux séries** : La Bible passe de 21 à 24 œuvres (dont Ouverture du chemin, qui n'était que sur l'accueil), la Belle Province de 7 à 10 (dont Limoilou 1 et 2), les Cupcakes de 19 à 20, Chiens et chats de 5 à 6, les Fleurs de 9 à 11 et Mes débuts… de 17 à 22.
- **Nouvelle série « Objets peints »** : les créations de Noël (patins, boules, quilles, moules, cuillères…) et les citrouilles de l'Action de grâce, 24 en tout.
- **Recadrées** : quatre photos prises au mur d'une exposition ont été recadrées sur la toile.
- **Écartées** : les doublons, les photos d'exposition des œuvres qui avaient déjà une bonne photo, une photo de famille et la photo d'un module de jeu.
- **Photos allégées** : 2000 pixels maximum, sans les métadonnées de l'appareil photo. Rébecca garde ses originaux en pleine qualité.

## À faire valider par Rébecca

- **Titres** : ceux qui manquaient sur l'ancien site viennent des noms de fichiers qu'elle avait donnés (Celui qui suis, Dieu pourvoit, Berger et moutons, Coq, Hippo, Lapins, Chameau, Croco, La promesse, La féministe, Prélude…). Quelques fautes ont été corrigées (« Tournesol rouge », « Problèmes de famille », « Prélude »). Certains noms comme « Hippo » ou « Croco » sont peut-être des noms de travail.
- **Thèmes** : ce sont des propositions faites en regardant les œuvres.

| Thème | Œuvres |
|---|---|
| Moïse | Buisson ardent, Ouverture du chemin (la mer qui s'ouvre), Celui qui suis (Exode 3, 14) |
| L'Arbre de la vie | Les trois arbres sans titre : celui aux serpents, celui à la colombe et aux grenades, celui entouré des noms de Dieu |
| Jonas | Jonas |
| La Pêche miraculeuse | Pêche miraculeuse 2, et le tableau sans titre aux voiliers et au banc de poissons |
| Noé | Et Dieu se souvint de Noé |
| L'Agneau de Dieu | Le mouton fait de pages de Bible (sans titre), l'agneau de profil sur fond rouge |
| Abraham | La promesse et les bergers sous les étoiles |

**Mise à jour du 7 novembre 2026** (demandes de Rébecca) : le Coq a été retiré, et 12 nouvelles œuvres ont été ajoutées en tête de la série biblique, sans titre pour l'instant.

- **Rangement** : les tableaux figuratifs ajoutés sont dans « Mes débuts… » (l'ancienne adresse de cette série était `/figuratif`). Les deux versions de « La promesse », l'horizontale et la verticale, sont dans la série biblique.
- **Objets peints** : à garder, renommer ou masquer selon ce qu'elle préfère.

## Le mémoire de maîtrise

Le PDF (`statique/documents/memoire-rebecca-masse-2010.pdf`) a été allégé de 120 Mo à 28 Mo. Le texte reste cherchable. GitHub Pages l'accepte sans problème.
