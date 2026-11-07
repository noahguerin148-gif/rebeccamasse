/* Rébecca Massé, artiste peintre : menu, visionneuse d'œuvres et formulaire de contact. */
(function () {
  "use strict";

  /* ---------- Année dans le pied de page ---------- */
  document.querySelectorAll("[data-annee]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ---------- Menu sur téléphone ---------- */
  var menuBouton = document.querySelector(".menu-bouton");
  var nav = document.getElementById("nav-principale");

  function fermerMenu(rendreFocus) {
    if (!menuBouton || !nav) return;
    menuBouton.setAttribute("aria-expanded", "false");
    nav.classList.remove("ouvert");
    if (rendreFocus) menuBouton.focus();
  }

  if (menuBouton && nav) {
    menuBouton.addEventListener("click", function () {
      var ouvert = menuBouton.getAttribute("aria-expanded") === "true";
      menuBouton.setAttribute("aria-expanded", String(!ouvert));
      nav.classList.toggle("ouvert", !ouvert);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("ouvert")) fermerMenu(true);
    });
    document.addEventListener("click", function (e) {
      if (nav.classList.contains("ouvert") && !e.target.closest(".entete")) fermerMenu(false);
    });
  }

  /* ---------- Protection légère des images ---------- */
  document.addEventListener("contextmenu", function (e) {
    if (e.target.closest && e.target.closest(".oeuvre, .vitrail, .bande, .serie-lien, .visionneuse")) e.preventDefault();
  });
  document.addEventListener("dragstart", function (e) {
    if (e.target.tagName === "IMG") e.preventDefault();
  });

  /* ---------- Visionneuse ---------- */
  var ICONES = {
    fermer: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    prec: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    suiv: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'
  };

  var galeries = document.querySelectorAll("[data-galerie]");
  var dialogueOk = typeof HTMLDialogElement === "function" && "showModal" in HTMLDialogElement.prototype;

  if (galeries.length && dialogueOk) {
    var dlg = document.createElement("dialog");
    dlg.className = "visionneuse";
    dlg.setAttribute("aria-label", "Visionneuse d'œuvres");
    dlg.innerHTML =
      '<figure class="visionneuse-scene">' +
        '<div class="visionneuse-cadre"><img alt="" draggable="false"></div>' +
        '<figcaption><span class="visionneuse-titre"></span><span class="visionneuse-details"></span><span class="visionneuse-compte"></span></figcaption>' +
      "</figure>" +
      '<button type="button" class="visionneuse-fermer" aria-label="Fermer">' + ICONES.fermer + "</button>" +
      '<button type="button" class="visionneuse-prec" aria-label="Œuvre précédente">' + ICONES.prec + "</button>" +
      '<button type="button" class="visionneuse-suiv" aria-label="Œuvre suivante">' + ICONES.suiv + "</button>";
    document.body.appendChild(dlg);

    var vImg = dlg.querySelector("img");
    var vTitre = dlg.querySelector(".visionneuse-titre");
    var vCompte = dlg.querySelector(".visionneuse-compte");
    var vDetails = dlg.querySelector(".visionneuse-details");
    var cadre = dlg.querySelector(".visionneuse-cadre");
    var liste = [];
    var index = 0;
    var declencheur = null;

    function lire(a) {
      var img = a.querySelector("img");
      return {
        src: a.getAttribute("href"),
        titre: a.getAttribute("data-titre") || "",
        details: a.getAttribute("data-details") || "",
        serie: a.getAttribute("data-serie") || "",
        alt: img ? img.getAttribute("alt") : ""
      };
    }

    function prechargerVoisines() {
      [index - 1, index + 1].forEach(function (i) {
        var o = liste[(i + liste.length) % liste.length];
        if (!o) return;
        var im = new Image();
        im.src = o.src;
      });
    }

    function afficher(i) {
      index = (i + liste.length) % liste.length;
      var o = liste[index];
      vImg.classList.add("chargement");
      vImg.onload = function () { vImg.classList.remove("chargement"); };
      vImg.src = o.src;
      vImg.alt = o.alt;
      vTitre.textContent = o.titre || o.serie;
      vDetails.textContent = o.details;
      vCompte.textContent = liste.length > 1 ? (index + 1) + " / " + liste.length : "";
      prechargerVoisines();
    }

    function ouvrir(groupe, i, lien) {
      liste = Array.prototype.map.call(groupe.querySelectorAll("a.oeuvre"), lire);
      declencheur = lien;
      dlg.classList.toggle("seule", liste.length < 2);
      afficher(i);
      dlg.showModal();
    }

    galeries.forEach(function (groupe) {
      var liens = groupe.querySelectorAll("a.oeuvre");
      liens.forEach(function (lien, i) {
        lien.addEventListener("click", function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
          e.preventDefault();
          ouvrir(groupe, i, lien);
        });
      });
    });

    dlg.querySelector(".visionneuse-fermer").addEventListener("click", function () { dlg.close(); });
    dlg.querySelector(".visionneuse-prec").addEventListener("click", function () { afficher(index - 1); });
    dlg.querySelector(".visionneuse-suiv").addEventListener("click", function () { afficher(index + 1); });

    dlg.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); afficher(index - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); afficher(index + 1); }
    });

    /* Un clic dans le vide autour de l'œuvre ferme la visionneuse */
    dlg.addEventListener("click", function (e) {
      if (e.target === dlg || e.target === cadre || e.target.classList.contains("visionneuse-scene")) dlg.close();
    });

    dlg.addEventListener("close", function () {
      vImg.removeAttribute("src");
      if (declencheur) declencheur.focus();
    });

    /* Glisser du doigt pour passer d'une œuvre à l'autre */
    var departX = null;
    cadre.addEventListener("pointerdown", function (e) { departX = e.clientX; });
    cadre.addEventListener("pointerup", function (e) {
      if (departX === null) return;
      var dx = e.clientX - departX;
      departX = null;
      if (Math.abs(dx) > 50 && liste.length > 1) afficher(dx < 0 ? index + 1 : index - 1);
    });
    cadre.addEventListener("pointercancel", function () { departX = null; });
  }

  /* ---------- Formulaire de contact (Web3Forms) ---------- */
  var form = document.querySelector("form.formulaire");
  if (form && window.fetch && window.FormData) {
    var etat = form.querySelector(".formulaire-etat");
    var bouton = form.querySelector('button[type="submit"]');
    var texteBouton = bouton ? bouton.textContent : "Envoyer";

    function montrer(message, type) {
      etat.textContent = message;
      etat.setAttribute("data-type", type);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var cle = (form.querySelector('[name="access_key"]') || {}).value || "";
      if (!cle || cle.indexOf("REMPLACER") === 0) {
        montrer("Le formulaire n'est pas encore activé. En attendant, écrivez-moi sur Facebook.", "erreur");
        return;
      }
      bouton.disabled = true;
      bouton.textContent = "Envoi en cours…";
      montrer("", "");

      fetch(form.action, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: new FormData(form)
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (res.ok && res.d && res.d.success) {
            form.reset();
            montrer("Vos informations ont bien été envoyées !", "ok");
          } else {
            throw new Error((res.d && res.d.message) || "Erreur");
          }
        })
        .catch(function () {
          montrer("Le message n'a pas pu être envoyé. Vérifiez votre connexion et réessayez, ou écrivez-moi sur Facebook.", "erreur");
        })
        .then(function () {
          bouton.disabled = false;
          bouton.textContent = texteBouton;
        });
    });
  }
})();
