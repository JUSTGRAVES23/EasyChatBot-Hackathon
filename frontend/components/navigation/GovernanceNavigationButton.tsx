import { useNavigate } from "react-router-dom";


interface GovernanceNavigationButtonProps {

    label: string;

    path: string;

    status?: string;

}



export default function GovernanceNavigationButton({

    label,

    path,

    status,

}: GovernanceNavigationButtonProps) {


    const navigate = useNavigate();



    return (

        <button

            className="control-row"

            onClick={() => navigate(path)}

        >

            <span>

                {label}

            </span>


            {status && (

                <strong>

                    ✓ {status}

                </strong>

            )}


        </button>

    );

}