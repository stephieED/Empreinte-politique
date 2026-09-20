import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import ConstructionBanner from './components/ConstructionBanner';
import TitreDeLaPage from './components/TitreDeLaPage';
import ExplorerLayout from './components/ExplorerLayout';
import LandingPage from './pages/LandingPage';
import CandidateProfilePage from './pages/CandidateProfilePage';
import GroupProfilePage from './pages/GroupProfilePage';
import GovernmentProfilePage from './pages/GovernmentProfilePage';
import MethodologyPage from './pages/MethodologyPage';
import AboutPage from './pages/AboutPage';
import CoveragePage from './pages/CoveragePage';
import FaqPage from './pages/FaqPage';
import LegalNoticePage from './pages/LegalNoticePage';
import { DEFAULT_CANDIDATE_ID, DEFAULT_GROUP_ID, DEFAULT_GOVERNMENT_ID } from './data';

function App() {
  return (
    // Le bandeau vit ICI, hors des routes : les pages de méthodologie et de
    // mentions légales ne passent pas par ExplorerLayout, et un lecteur arrive
    // souvent par un lien direct sur un profil sans voir la landing.
    <>
      <ConstructionBanner />
      <TitreDeLaPage />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* Layout route sans path propre : les enfants gardent leurs URLs actuelles
            (/candidats/:id, /groupes/:id, /gouvernements/:id), seule la racine "/"
            bascule désormais vers la landing page au lieu de rediriger vers un candidat. */}
        <Route element={<ExplorerLayout />}>
          <Route path="candidats" element={<Navigate to={`/candidats/${DEFAULT_CANDIDATE_ID}`} replace />} />
          <Route path="candidats/:candidateId" element={<CandidateProfilePage />} />
          <Route path="groupes" element={<Navigate to={`/groupes/${DEFAULT_GROUP_ID}`} replace />} />
          <Route path="groupes/:groupId" element={<GroupProfilePage />} />
          <Route path="gouvernements" element={<Navigate to={`/gouvernements/${DEFAULT_GOVERNMENT_ID}`} replace />} />
          <Route path="gouvernements/:governmentId" element={<GovernmentProfilePage />} />
        </Route>
        {/* Pages statiques hors ExplorerLayout : pas de candidat/groupe sélectionné,
            les bandeaux Groupes/Gouvernements/Candidats n'ont pas de sens ici. */}
        <Route path="/a-propos" element={<AboutPage />} />
        <Route path="/methodologie" element={<MethodologyPage />} />
        <Route path="/sources" element={<CoveragePage />} />
        {/* /couverture est devenue /sources (#951). Elle REDIRIGE, et garde
            l'ancre : des liens partagés et les renvois des fiches y mènent. */}
        <Route path="/couverture" element={<RedirectionCouverture />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/mentions-legales" element={<LegalNoticePage />} />
      </Routes>
    </>
  );
}

export default App;

function RedirectionCouverture() {
  const { hash } = useLocation();
  return <Navigate to={{ pathname: '/sources', hash }} replace />;
}
