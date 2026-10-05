import { Navigate, Outlet, useLocation } from "react-router-dom";

import AuthenticationHelper from "../../shared/helpers/authenticationHelper";

function ProtectedRoute() {
  const location = useLocation();

  if (!sessionStorage.getItem("jwtToken") || !AuthenticationHelper.isUserAuthenticated()) {
    return <Navigate to="/portal-access" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
