"""
Module de gestion de stock et de préparation de colis.
Ce module contient les classes nécessaires pour gérer un inventaire en FIFO,
des alertes systèmes, et la préparation de colis en LIFO triée.
"""
import sys
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional


# --- 1. MODÈLE DE DONNÉES ---

@dataclass
class Produit:
    """Représente un produit avec son type et son volume."""
    type_p: str
    volume: int

    def __str__(self):
        return f"{self.type_p}{self.volume}"


@dataclass
class Alerte:
    """Représente une alerte système."""
    message: str


# --- 2. SERVICES ---

class GestionAlertes:
    """Gère le log des alertes avec un tampon circulaire (3 places)."""

    def __init__(self):
        # Structure STATIQUE, 3 places
        self.log = deque(maxlen=3)

    def ajouter_alerte(self, message: str):
        """Ajoute une alerte. La plus ancienne est écrasée si plein."""
        self.log.append(Alerte(message))
        print(f"[ALERTE] {message}")

    def afficher_alertes(self):
        """Affiche de la plus ancienne à la plus récente."""
        print("\n--- JOURNAL DES ALERTES ---")
        if not self.log:
            print("Aucune alerte active.")
        for alerte in self.log:
            print(f"Log: {alerte.message}")


class GestionStock:
    """Gère l'inventaire (FIFO) et les entrées."""

    def __init__(self, service_alerte: GestionAlertes):
        self.stock: Dict[str, deque] = {}
        self.alertes = service_alerte
        self.SEUIL_MIN = 2  # Seuil pour déclencher l'alerte

    def ajouter_masse(self, chaine_saisie: str):
        """Saisie rapide ex: 'A1, B2, A1'."""
        if not chaine_saisie:
            return
        items = [x.strip() for x in chaine_saisie.split(',')]
        for item in items:
            self._ajouter_unitaire(item)

    def _ajouter_unitaire(self, code: str):
        """Parse et ajoute un produit unique."""
        try:
            p = Produit(type_p=code[0].upper(), volume=int(code[1:]))
            if p.type_p not in self.stock:
                self.stock[p.type_p] = deque()

            # FIFO: ajout à droite
            self.stock[p.type_p].append(p)
            print(f"Stock + : {p}")
        except (IndexError, ValueError):
            print(f"Erreur format : {code}")

    def retirer_produit(self, type_p: str, vol_demande: int) -> Optional[Produit]:
        """Tente de retirer un produit spécifique."""
        if type_p not in self.stock or not self.stock[type_p]:
            return None

        # Sélection par Type et Volume
        for i, prod in enumerate(self.stock[type_p]):
            if prod.volume == vol_demande:
                del self.stock[type_p][i]
                self._verifier_seuil(type_p)
                return prod
        return None

    def _verifier_seuil(self, type_p: str):
        """Vérifie si le stock est bas."""
        qte = len(self.stock[type_p])
        if qte < self.SEUIL_MIN:
            # Id de l'alarme
            self.alertes.ajouter_alerte(f"Rupture imminente {type_p} (Stock: {qte})")


class GestionColis:
    """
    Gère la création de colis (LIFO triée).
    Cette classe agit comme un orchestrateur.
    """
    # On supprime l'avertissement car cette classe sert de Service
    # pylint: disable=too-few-public-methods

    def __init__(self, stock_manager: GestionStock, alerte_manager: GestionAlertes):
        self.stock_mgr = stock_manager
        self.alerte_mgr = alerte_manager

    def preparer_colis(self, chaine_commande: str):
        """Orchestre la création d'un colis."""
        # Correction C0321 : Séparation sur deux lignes
        if not chaine_commande:
            return

        produits_bruts = [x.strip() for x in chaine_commande.split(',')]
        produits_recuperes = []

        print(f"\n--- COMMANDE : {chaine_commande} ---")

        for code in produits_bruts:
            p = self._recuperer_ou_gerer_rupture(code)
            if p:
                produits_recuperes.append(p)

        # Empilés du plus grand volume au plus petit
        pile_finale = sorted(produits_recuperes, key=lambda x: x.volume, reverse=True)
        self._afficher_colis(pile_finale)

    def _recuperer_ou_gerer_rupture(self, code: str) -> Optional[Produit]:
        """Gère la récupération et les stratégies de rupture."""
        type_p = code[0].upper()
        vol = int(code[1:])

        prod = self.stock_mgr.retirer_produit(type_p, vol)
        if prod:
            return prod

        #  Stratégie 1 : Log + Annulation de la ligne
        self.alerte_mgr.ajouter_alerte(f"Rupture stock: {code}")
        return None

    # Correction R0201 : Passage en staticmethod car 'self' n'est pas utilisé
    @staticmethod
    def _afficher_colis(pile: List[Produit]):
        """Affiche le contenu final du colis de manière sobre."""
        # Affichage simple : [A3, B2, C1]
        contenu = ", ".join(str(p) for p in pile)
        print(f"-> Colis assemblé : [{contenu}]")


# --- 3. INTERFACE (CLI) ---

def main():
    """Point d'entrée principal."""
    srv_alertes = GestionAlertes()
    srv_stock = GestionStock(srv_alertes)
    srv_colis = GestionColis(srv_stock, srv_alertes)

    # Stock en dur
    print("Initialisation...")
    srv_stock.ajouter_masse("A1, A2, A3, B1, B2, C3, C3, A1")

    while True:
        print("\n1. Ajouter (ex: A1, B2)\n2. Colis (ex: A3, C3)\n3. Alertes\n4. Quitter\n")
        choix = input("> ")

        if choix == '1':
            srv_stock.ajouter_masse(input("Saisie : "))
        elif choix == '2':
            srv_colis.preparer_colis(input("Commande : "))
        elif choix == '3':
            srv_alertes.afficher_alertes()
        elif choix == '4':
            sys.exit()


if __name__ == "__main__":
    main()