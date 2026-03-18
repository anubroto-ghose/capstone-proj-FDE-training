import { Link, useNavigate } from "react-router-dom";
import { isAuthenticated, removeToken } from "../utils/auth";

function Navbar() {

  const navigate = useNavigate();

  const logout = () => {
    removeToken();
    navigate("/");
  };

  return (

    <nav className="navbar navbar-dark bg-black border-bottom border-secondary px-4">

      <span className="navbar-brand fw-semibold">
        Incident Knowledge Assistant
      </span>

      <div>

        {!isAuthenticated() && (
          <>
            <Link className="btn btn-outline-light me-2" to="/">
              Login
            </Link>

            <Link className="btn btn-light" to="/register">
              Register
            </Link>
          </>
        )}

        {isAuthenticated() && (
          <button
            className="btn btn-outline-light"
            onClick={logout}
          >
            Logout
          </button>
        )}

      </div>

    </nav>

  );
}

export default Navbar;