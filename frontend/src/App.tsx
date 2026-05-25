import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NL2SQLPage from './pages/NL2SQLPage';
import MarketingPage from './pages/MarketingPage';
import CampaignDetail from './pages/CampaignDetail';
import NavBar from './components/NavBar';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <NavBar />
        <div className="container mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<NL2SQLPage />} />
            <Route path="/nl2sql" element={<NL2SQLPage />} />
            <Route path="/marketing" element={<MarketingPage />} />
            <Route path="/campaign/:id" element={<CampaignDetail />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;