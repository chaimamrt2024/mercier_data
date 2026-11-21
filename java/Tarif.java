/**
 * Moteur de calcul tarifaire d'Atelier Mercier.
 * Composant certifié par la comptabilité : ne pas réécrire.
 */
public class Tarif {

    public static final double TAUX_TVA = 0.20;

    /** Montant net d'une ligne de vente, remise déduite, arrondi au centime. */
    public static double montantLigne(double prix, int quantite, int remisePourcent) {
        if (prix < 0 || quantite < 1) {
            throw new IllegalArgumentException("Prix negatif ou quantite nulle.");
        }
        if (remisePourcent < 0 || remisePourcent > 100) {
            throw new IllegalArgumentException("Remise hors bornes.");
        }
        double net = prix * quantite * (1 - remisePourcent / 100.0);
        return Math.round(net * 100.0) / 100.0;
    }

    /** Appel en ligne de commande : prix quantite remise. */
    public static void main(String[] args) {
        double prix = Double.parseDouble(args[0]);
        int quantite = Integer.parseInt(args[1]);
        int remise = Integer.parseInt(args[2]);
        System.out.println(montantLigne(prix, quantite, remise));
    }
}
