import { Link } from "react-router-dom";


export default function OperationsCenterPage() {


    return (

        <div className="operations-center">


            <section className="hero">


                <div>


                    <small>
                        EASYCHATBOT OPERATIONS CENTER
                    </small>



                    <h1>
                        AI Operations Center
                    </h1>



                    <p>
                        Operational visibility across governance,
                        cybersecurity and provider controls.
                    </p>


                </div>





                <div className="yeti-hero">


                    <img

                        src="/assets/characters/yeti-governance.png"

                        alt="YETI Operations Guardian"

                    />


                </div>



            </section>









            <section className="card">


                <h2>
                    Operations Health
                </h2>



                <strong className="health-value">

                    96%

                </strong>





                <div className="health-bar">


                    <span />


                </div>





                <p>
                    All operational controls are operating normally.
                </p>



            </section>









            <section className="card">


                <h2>
                    YETI Operational Brief
                </h2>



                <h3>
                    Everything looks calm from an operations perspective.
                </h3>




                <p>
                    YETI explains operational state while authorised humans
                    remain responsible for decisions.
                </p>



            </section>









            <section className="operations-grid">



                <DashboardCard

                    title="Governance"

                    status="Healthy"

                    description="Governance controls and audit visibility."

                    path="/operations-center/governance"

                />






                <DashboardCard

                    title="Cybersecurity"

                    status="Monitoring"

                    description="Cybersecurity intelligence visibility."

                    path="/operations-center/cybersecurity"

                />






                <DashboardCard

                    title="Provider Management"

                    status="Healthy"

                    description="Approved provider operational controls."

                    path="/operations-center/providers"

                />



            </section>



        </div>


    );

}






interface DashboardCardProps {

    title:string;

    status:string;

    description:string;

    path:string;

}






function DashboardCard({

    title,

    status,

    description,

    path


}: DashboardCardProps) {



    return (


        <div className="operation-domain-card">


            <h2>

                {title}

            </h2>





            <h3>

                {status}

            </h3>





            <p>

                {description}

            </p>





            <Link

                to={path}

                className="dashboard-link"

            >

                Open Dashboard →

            </Link>



        </div>


    );

}