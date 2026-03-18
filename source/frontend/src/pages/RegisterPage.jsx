import Navbar from "../components/NavBar";
import RegisterForm from "../components/RegisterForm";

function RegisterPage(){

  return(

    <>
      <Navbar/>

      <div className="container vh-100 d-flex justify-content-center align-items-center">

        <div className="col-md-4">

          <RegisterForm/>

        </div>

      </div>

    </>
  );
}

export default RegisterPage;