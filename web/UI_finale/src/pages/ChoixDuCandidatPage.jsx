import FilDAriane from '../components/FilDAriane';
import '../components/CandidateProfile.css';

/* ── /candidats : le choix d'un candidat, sans fiche par défaut (#1329) ──────
 *
 * L'adresse redirigeait vers une fiche choisie d'avance — celle de Jean-Luc
 * Mélenchon —, si bien que la carte « Mai 2027 » du carrousel et du bandeau des
 * articles menait à un candidat que rien ne désignait. Demandé par la
 * propriétaire le 26/10/2026 : le fil d'Ariane ouvert sur la liste des
 * candidats, et le reste de la page vide. Aucun candidat n'est mis en avant
 * (AGENTS.md §2 règle 1).
 */
export default function ChoixDuCandidatPage() {
  return (
    <main className="cp-main cp-main--choix">
      <div className="cp-breadcrumb">
        <FilDAriane libelle="Candidats" ouvertAuDepart type="candidats" />
      </div>
    </main>
  );
}
