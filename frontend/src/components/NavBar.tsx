import { Link, useLocation } from 'react-router-dom';

function NavBar() {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/nl2sql') {
      return location.pathname === '/' || location.pathname === '/nl2sql';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">DA</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">Data Agent</span>
            </Link>
            <div className="flex space-x-1">
              <Link
                to="/nl2sql"
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/nl2sql')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                NL2SQL
              </Link>
              <Link
                to="/marketing"
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/marketing')
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Marketing
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default NavBar;