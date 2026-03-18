import Navbar from "../components/NavBar";
import LoginForm from "../components/LoginForm";

function LoginPage(){

  return(

    <>
      <Navbar/>

      <div className="container vh-100 d-flex justify-content-center align-items-center">

        <div className="col-md-4">

          <LoginForm/>

        </div>

      </div>

    </>
  );
}

export default LoginPage;